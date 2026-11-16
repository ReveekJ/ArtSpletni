from dataclasses import dataclass, field


@dataclass(slots=True)
class WikiPlace:
    ref: str
    title: str
    language: str
    url: str
    extract: str
    latitude: float | None
    longitude: float | None
    distance_m: int | None
    page_image: str | None


@dataclass(slots=True)
class CommonsPhoto:
    ref: str
    file_title: str
    description: str
    url: str
    author: str | None
    license: str | None
    source_url: str
    latitude: float | None
    longitude: float | None
    distance_m: int | None


@dataclass(slots=True)
class NearbyContext:
    places: list[WikiPlace] = field(default_factory=list)
    photos: list[CommonsPhoto] = field(default_factory=list)


@dataclass(slots=True)
class GossipSubject:
    title: str
    location_name: str | None
    latitude: float
    longitude: float
