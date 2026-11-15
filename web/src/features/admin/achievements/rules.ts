import type { Schemas } from "@/api/client";

export type Achievement = Schemas["AdminAchievementOut"];
export type Rule = Schemas["AchievementInput"]["rule"];
export type Params = Schemas["AchievementInput"]["params"];

export interface ParamField {
  name: "count" | "routeId" | "hours" | "fromHour" | "toHour" | "days";
  optional?: boolean;
}

export const RULE_FIELDS: Record<Rule, ParamField[]> = {
  points_unlocked: [{ name: "count" }],
  route_completed: [{ name: "routeId" }],
  routes_completed: [{ name: "count" }],
  route_completed_full: [{ name: "routeId", optional: true }],
  route_completed_within: [{ name: "hours" }, { name: "routeId", optional: true }],
  route_first_finishers: [{ name: "count" }, { name: "routeId", optional: true }],
  offers_redeemed: [{ name: "count" }],
  partner_points_visited: [{ name: "count" }],
  scan_time_window: [{ name: "fromHour" }, { name: "toHour" }],
  points_in_day: [{ name: "count" }],
  days_streak: [{ name: "days" }],
};

export const RULES = Object.keys(RULE_FIELDS) as Rule[];
