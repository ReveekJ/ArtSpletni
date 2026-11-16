import msgspec

from app.domain.gossip.types import GossipSubject, NearbyContext

SYSTEM_PROMPT = """You are a witty local storyteller for an art audio-guide app.
Write short "gossip" stories about a place and what is near it: funny, mystical, romantic,
spooky, odd historical trivia, urban legends. Tone: playful, a bit cheeky, never mean.

Hard rules:
- Base stories on the provided places and photos. If you have web search, you may use it and
  add the pages you used to "extra_links" (real URLs only, never invent URLs).
- Never write about private or currently living people. Historical figures, buildings,
  streets, folklore are fine.
- Never present invented events as facts. Myths, rumours and urban legends must be labelled:
  veracity "legend" for myths/urban legends, "unverified" for rumours and unconfirmed stories,
  "documented" only when the provided sources support it.
- "source_refs" lists the place refs (like "P1") the story relies on.
- "photo_ref" is a photo ref (like "I2") from the provided list that fits the story, or null.
  Never output image URLs.
- "place_ref" is the place ref the story is about, or null if it is about the point itself.
- category is one of: fun, mystic, romance, legend, history.
- Each story: title up to 80 characters, text 300-700 characters.
- Provide every story in these languages: {languages}.

Answer with a single JSON object and nothing else:
{{"items": [{{"category": "...", "veracity": "...", "place_name": "...", "place_ref": "P1",
"photo_ref": "I1", "source_refs": ["P1"], "extra_links": [{{"url": "...", "title": "..."}}],
"localizations": {{"<language code>": {{"title": "...", "text": "..."}}}}}}]}}"""


def build_system_prompt(languages: list[str]) -> str:
    return SYSTEM_PROMPT.format(languages=", ".join(languages))


def build_user_prompt(subject: GossipSubject, context: NearbyContext, max_items: int) -> str:
    payload = {
        "max_stories": max_items,
        "point": {
            "title": subject.title,
            "location_name": subject.location_name,
            "latitude": subject.latitude,
            "longitude": subject.longitude,
        },
        "places": [
            {
                "ref": place.ref,
                "title": place.title,
                "language": place.language,
                "distance_m": place.distance_m,
                "extract": place.extract,
            }
            for place in context.places
        ],
        "photos": [
            {
                "ref": photo.ref,
                "file": photo.file_title,
                "description": photo.description,
                "distance_m": photo.distance_m,
            }
            for photo in context.photos
        ],
    }
    return msgspec.json.encode(payload).decode()
