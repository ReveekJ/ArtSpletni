from typing import Annotated
from uuid import UUID

import msgspec

from app.db.models import AchievementRule, RuleParams
from app.lib.exceptions import BadRequestError

Positive = Annotated[int, msgspec.Meta(gt=0)]
Hour = Annotated[int, msgspec.Meta(ge=0, le=23)]


class CountParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    count: Positive


class RouteParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    route_id: UUID


class OptionalRouteParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    route_id: UUID | None = None


class WithinParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    hours: Positive
    route_id: UUID | None = None


class FirstFinishersParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    count: Positive
    route_id: UUID | None = None


class TimeWindowParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    from_hour: Hour
    to_hour: Hour


class StreakParams(msgspec.Struct, rename="camel", forbid_unknown_fields=True):
    days: Positive


AnyParams = (
    CountParams
    | RouteParams
    | OptionalRouteParams
    | WithinParams
    | FirstFinishersParams
    | TimeWindowParams
    | StreakParams
)

RULE_PARAMS: dict[AchievementRule, type[AnyParams]] = {
    AchievementRule.POINTS_UNLOCKED: CountParams,
    AchievementRule.ROUTE_COMPLETED: RouteParams,
    AchievementRule.ROUTES_COMPLETED: CountParams,
    AchievementRule.ROUTE_COMPLETED_FULL: OptionalRouteParams,
    AchievementRule.ROUTE_COMPLETED_WITHIN: WithinParams,
    AchievementRule.ROUTE_FIRST_FINISHERS: FirstFinishersParams,
    AchievementRule.OFFERS_REDEEMED: CountParams,
    AchievementRule.PARTNER_POINTS_VISITED: CountParams,
    AchievementRule.SCAN_TIME_WINDOW: TimeWindowParams,
    AchievementRule.POINTS_IN_DAY: CountParams,
    AchievementRule.DAYS_STREAK: StreakParams,
}

UNLOCK_RULES = frozenset(
    {
        AchievementRule.POINTS_UNLOCKED,
        AchievementRule.PARTNER_POINTS_VISITED,
        AchievementRule.SCAN_TIME_WINDOW,
        AchievementRule.POINTS_IN_DAY,
        AchievementRule.DAYS_STREAK,
    }
)
COMPLETION_RULES = frozenset(
    {
        AchievementRule.ROUTE_COMPLETED,
        AchievementRule.ROUTES_COMPLETED,
        AchievementRule.ROUTE_COMPLETED_FULL,
        AchievementRule.ROUTE_COMPLETED_WITHIN,
        AchievementRule.ROUTE_FIRST_FINISHERS,
    }
)
REDEMPTION_RULES = frozenset({AchievementRule.OFFERS_REDEEMED})


def parse_params(rule: AchievementRule, raw: RuleParams) -> AnyParams:
    try:
        return msgspec.convert(raw, type=RULE_PARAMS[rule])
    except msgspec.ValidationError as exc:
        raise BadRequestError(f"Invalid parameters for {rule}: {exc}", code="invalid_rule_params") from exc


def dump_params(params: AnyParams) -> RuleParams:
    raw: RuleParams = msgspec.to_builtins(params)
    return raw
