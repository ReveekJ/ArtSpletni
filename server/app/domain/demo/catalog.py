from dataclasses import dataclass
from pathlib import Path

from app.db.models import MapVisibility, OrderingMode
from app.domain.auth.demo import DEMO_PARTNER_NAME

ASSETS_DIR = Path(__file__).parent / "assets"


@dataclass(frozen=True, slots=True)
class OfferSeed:
    title: dict[str, str]
    terms: dict[str, str] | None = None
    promo_code: str | None = None
    ttl_hours: int | None = None
    redemption_limit: int | None = None
    valid_days: int | None = None


@dataclass(frozen=True, slots=True)
class PartnerSeed:
    key: str
    name: str
    description: dict[str, str]
    offers: tuple[OfferSeed, ...] = ()


@dataclass(frozen=True, slots=True)
class PointSeed:
    key: str
    title: dict[str, str]
    latitude: float
    longitude: float
    address: str
    story: str
    partner: str | None = None
    offer: OfferSeed | None = None
    hint: str | None = None
    is_required: bool = True
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouteSeed:
    slug: str
    title: dict[str, str]
    description: str
    ordering_mode: OrderingMode
    map_visibility: MapVisibility
    points: tuple[PointSeed, ...]
    is_repeatable: bool = False


PARTNERS: tuple[PartnerSeed, ...] = (
    PartnerSeed(
        key="coffee",
        name=DEMO_PARTNER_NAME,
        description={"ru": "Кофейня на Вайнера, где новости города рождаются между двумя капучино."},
        offers=(
            OfferSeed(
                title={"ru": "−10% на завтраки до 11:00", "en": "10% off breakfast before 11:00"},
                terms={"ru": "Назовите промокод на кассе. Не суммируется с другими акциями."},
                promo_code="MORNING10",
                valid_days=120,
            ),
        ),
    ),
    PartnerSeed(
        key="books",
        name="Книжная лавка «Уральский переплёт»",
        description={"ru": "Маленький книжный про Урал: краеведение, комиксы и открытки с Плотинкой."},
    ),
    PartnerSeed(
        key="bar",
        name="Бар «Шёпот»",
        description={"ru": "Камерный бар у Патриарших: лимонады, настойки и сплетни вполголоса."},
        offers=(
            OfferSeed(
                title={"ru": "Второй лимонад бесплатно", "en": "Second lemonade on the house"},
                terms={"ru": "При заказе любого лимонада. Только по будням."},
                redemption_limit=50,
            ),
        ),
    ),
    PartnerSeed(
        key="bakery",
        name="Пекарня «Булка на Покровке»",
        description={"ru": "Пекарня с утренними круассанами и самыми свежими слухами Покровки."},
    ),
)
