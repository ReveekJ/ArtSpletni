from dataclasses import dataclass

from app.db.models import AchievementRule, RuleParams

RU = "ru"


@dataclass(frozen=True, slots=True)
class AchievementSeed:
    code: str
    title: dict[str, str]
    description: dict[str, str]
    rule: AchievementRule
    params: RuleParams
    is_hidden: bool = False


STARTER_ACHIEVEMENTS: tuple[AchievementSeed, ...] = (
    AchievementSeed(
        "first_gossip",
        {RU: "Первая сплетня"},
        {RU: "Отсканируй первую метку"},
        AchievementRule.POINTS_UNLOCKED,
        {"count": 1},
    ),
    AchievementSeed(
        "gossip_collector",
        {RU: "Собиратель слухов"},
        {RU: "Открой 10 точек"},
        AchievementRule.POINTS_UNLOCKED,
        {"count": 10},
    ),
    AchievementSeed(
        "chief_gossip",
        {RU: "Главный сплетник"},
        {RU: "Открой 50 точек"},
        AchievementRule.POINTS_UNLOCKED,
        {"count": 50},
    ),
    AchievementSeed(
        "district_expert",
        {RU: "Знаток района"},
        {RU: "Пройди 3 разных маршрута"},
        AchievementRule.ROUTES_COMPLETED,
        {"count": 3},
    ),
    AchievementSeed(
        "sniffed_it_all",
        {RU: "Всё вынюхала"},
        {RU: "Пройди маршрут вместе со всеми необязательными точками"},
        AchievementRule.ROUTE_COMPLETED_FULL,
        {},
    ),
    AchievementSeed(
        "word_of_mouth",
        {RU: "Сарафанное радио"},
        {RU: "Пройди маршрут быстрее чем за 3 часа"},
        AchievementRule.ROUTE_COMPLETED_WITHIN,
        {"hours": 3},
    ),
    AchievementSeed(
        "first_to_know",
        {RU: "Первая узнала"},
        {RU: "Войди в десятку первых, кто прошёл маршрут"},
        AchievementRule.ROUTE_FIRST_FINISHERS,
        {"count": 10},
    ),
    AchievementSeed(
        "regular",
        {RU: "Завсегдатай"},
        {RU: "Используй 3 предложения партнёров"},
        AchievementRule.OFFERS_REDEEMED,
        {"count": 3},
    ),
    AchievementSeed(
        "socialite",
        {RU: "Светская львица"},
        {RU: "Загляни к 5 партнёрам"},
        AchievementRule.PARTNER_POINTS_VISITED,
        {"count": 5},
    ),
    AchievementSeed(
        "night_gossip",
        {RU: "Ночная сплетница"},
        {RU: "Открой точку между 23:00 и 5:00"},
        AchievementRule.SCAN_TIME_WINDOW,
        {"fromHour": 23, "toHour": 5},
        is_hidden=True,
    ),
    AchievementSeed(
        "gossip_marathon",
        {RU: "Марафон слухов"},
        {RU: "Открой 8 точек за один день"},
        AchievementRule.POINTS_IN_DAY,
        {"count": 8},
    ),
    AchievementSeed(
        "cant_keep_quiet",
        {RU: "Не держит в себе"},
        {RU: "Открывай точки 3 дня подряд"},
        AchievementRule.DAYS_STREAK,
        {"days": 3},
        is_hidden=True,
    ),
)
