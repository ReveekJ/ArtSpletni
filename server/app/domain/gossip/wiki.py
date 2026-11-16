import asyncio
import logging
from html.parser import HTMLParser

import httpx
import msgspec

from app.domain.gossip.types import CommonsPhoto, NearbyContext, WikiPlace

logger = logging.getLogger(__name__)

WIKI_LANGUAGES: tuple[str, ...] = ("ru", "en")
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PHOTO_MIME_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_RADIUS_M = 10000
THUMB_WIDTH = 800
EXTRACT_CHARS = 1200
PHOTOS_PER_ITEM = 3


class _Coordinate(msgspec.Struct):
    lat: float
    lon: float
    dist: float | None = None


class _ExtMetaValue(msgspec.Struct):
    value: str = ""


class _ExtMetadata(msgspec.Struct):
    artist: _ExtMetaValue | None = msgspec.field(name="Artist", default=None)
    license_short_name: _ExtMetaValue | None = msgspec.field(name="LicenseShortName", default=None)
    image_description: _ExtMetaValue | None = msgspec.field(name="ImageDescription", default=None)


class _ImageInfo(msgspec.Struct):
    url: str
    descriptionurl: str
    thumburl: str | None = None
    mime: str | None = None
    extmetadata: _ExtMetadata | None = None


class _Page(msgspec.Struct):
    title: str
    missing: bool = False
    fullurl: str | None = None
    extract: str | None = None
    pageimage: str | None = None
    coordinates: list[_Coordinate] = []
    imageinfo: list[_ImageInfo] = []


class _Query(msgspec.Struct):
    pages: list[_Page] = []


class _ApiResponse(msgspec.Struct):
    query: _Query | None = None


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return " ".join("".join(parser.parts).split())


def _distance(coordinate: _Coordinate | None) -> int | None:
    return round(coordinate.dist) if coordinate is not None and coordinate.dist is not None else None


class WikiGeoClient:
    def __init__(self, user_agent: str, timeout_seconds: float) -> None:
        self._headers = {"User-Agent": user_agent}
        self._timeout = timeout_seconds

    async def collect(self, latitude: float, longitude: float, radius_m: int, limit: int) -> NearbyContext:
        async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
            wiki_results = await asyncio.gather(
                *(
                    self._fetch_places(client, language, latitude, longitude, radius_m, limit)
                    for language in WIKI_LANGUAGES
                )
            )
            places = self._assign_place_refs([page for batch in wiki_results for page in batch])
            geo_photos = await self._fetch_geo_photos(client, latitude, longitude, radius_m, limit * 2)
            page_image_titles = [f"File:{place.page_image}" for place in places if place.page_image]
            page_photos = await self._fetch_photos_by_titles(client, page_image_titles)
        unique_photos = self._dedupe_photos(page_photos + geo_photos)
        photos = self._assign_photo_refs(unique_photos[: limit * PHOTOS_PER_ITEM])
        return NearbyContext(places=places, photos=photos)

    async def _fetch_places(
        self,
        client: httpx.AsyncClient,
        language: str,
        latitude: float,
        longitude: float,
        radius_m: int,
        limit: int,
    ) -> list[tuple[str, _Page]]:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "geosearch",
            "ggscoord": f"{latitude}|{longitude}",
            "ggsradius": str(min(radius_m, MAX_RADIUS_M)),
            "ggslimit": str(limit),
            "prop": "coordinates|extracts|pageimages|info",
            "codistancefrompoint": f"{latitude}|{longitude}",
            "exintro": "1",
            "explaintext": "1",
            "exchars": str(EXTRACT_CHARS),
            "exlimit": "max",
            "piprop": "name",
            "inprop": "url",
        }
        response = await self._get(client, f"https://{language}.wikipedia.org/w/api.php", params)
        if response is None or response.query is None:
            return []
        return [(language, page) for page in response.query.pages if not page.missing and page.fullurl]

    async def _fetch_geo_photos(
        self, client: httpx.AsyncClient, latitude: float, longitude: float, radius_m: int, limit: int
    ) -> list[CommonsPhoto]:
        params = {
            **self._imageinfo_params(),
            "generator": "geosearch",
            "ggsnamespace": "6",
            "ggscoord": f"{latitude}|{longitude}",
            "ggsradius": str(min(radius_m, MAX_RADIUS_M)),
            "ggslimit": str(limit),
            "prop": "imageinfo|coordinates",
            "codistancefrompoint": f"{latitude}|{longitude}",
        }
        return await self._fetch_photos(client, params)

    async def _fetch_photos_by_titles(
        self, client: httpx.AsyncClient, titles: list[str]
    ) -> list[CommonsPhoto]:
        if not titles:
            return []
        params = {
            **self._imageinfo_params(),
            "titles": "|".join(dict.fromkeys(titles)),
            "prop": "imageinfo",
        }
        return await self._fetch_photos(client, params)

    async def _fetch_photos(self, client: httpx.AsyncClient, params: dict[str, str]) -> list[CommonsPhoto]:
        response = await self._get(client, COMMONS_API, params)
        if response is None or response.query is None:
            return []
        photos = (self._to_photo(page) for page in response.query.pages)
        return [photo for photo in photos if photo is not None]

    @staticmethod
    def _imageinfo_params() -> dict[str, str]:
        return {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "iiprop": "url|mime|extmetadata",
            "iiurlwidth": str(THUMB_WIDTH),
            "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription",
        }

    @staticmethod
    async def _get(client: httpx.AsyncClient, url: str, params: dict[str, str]) -> _ApiResponse | None:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return msgspec.json.decode(response.content, type=_ApiResponse)
        except (httpx.HTTPError, msgspec.DecodeError):
            logger.exception("Wikimedia request failed: %s", url)
            return None

    @staticmethod
    def _to_photo(page: _Page) -> CommonsPhoto | None:
        if page.missing or not page.imageinfo:
            return None
        info = page.imageinfo[0]
        if info.mime not in PHOTO_MIME_TYPES:
            return None
        meta = info.extmetadata
        author = html_to_text(meta.artist.value) if meta and meta.artist else None
        license_name = meta.license_short_name.value if meta and meta.license_short_name else None
        description = html_to_text(meta.image_description.value) if meta and meta.image_description else ""
        coordinate = page.coordinates[0] if page.coordinates else None
        return CommonsPhoto(
            ref="",
            file_title=page.title,
            description=description[:500],
            url=info.thumburl or info.url,
            author=author[:512] if author else None,
            license=license_name[:128] if license_name else None,
            source_url=info.descriptionurl,
            latitude=coordinate.lat if coordinate else None,
            longitude=coordinate.lon if coordinate else None,
            distance_m=_distance(coordinate),
        )

    @staticmethod
    def _assign_place_refs(pages: list[tuple[str, _Page]]) -> list[WikiPlace]:
        places: list[WikiPlace] = []
        for index, (language, page) in enumerate(pages, start=1):
            coordinate = page.coordinates[0] if page.coordinates else None
            places.append(
                WikiPlace(
                    ref=f"P{index}",
                    title=page.title,
                    language=language,
                    url=page.fullurl or "",
                    extract=page.extract or "",
                    latitude=coordinate.lat if coordinate else None,
                    longitude=coordinate.lon if coordinate else None,
                    distance_m=_distance(coordinate),
                    page_image=page.pageimage,
                )
            )
        return places

    @staticmethod
    def _dedupe_photos(photos: list[CommonsPhoto]) -> list[CommonsPhoto]:
        unique: dict[str, CommonsPhoto] = {}
        for photo in photos:
            unique.setdefault(photo.file_title, photo)
        return list(unique.values())

    @staticmethod
    def _assign_photo_refs(photos: list[CommonsPhoto]) -> list[CommonsPhoto]:
        for index, photo in enumerate(photos, start=1):
            photo.ref = f"I{index}"
        return photos
