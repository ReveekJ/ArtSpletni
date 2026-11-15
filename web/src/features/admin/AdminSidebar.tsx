import { useTranslation } from "react-i18next";
import { NavLink, useNavigate } from "react-router-dom";

import { Logo } from "@/components/sketch/Logo";
import { ThemeToggleButton } from "@/components/ThemeSwitcher";
import { Button } from "@/components/ui/button";
import { Icon, type IconName } from "@/components/ui/icon";
import { useCurrentUser, useLogout } from "@/features/auth/api";
import { cn } from "@/lib/utils";

const SECTIONS: { key: string; icon: IconName }[] = [
  { key: "points", icon: "headphones" },
  { key: "routes", icon: "route" },
  { key: "partners", icon: "gift" },
  { key: "achievements", icon: "sparkle" },
  { key: "moderation", icon: "list" },
  { key: "analytics", icon: "chart" },
];

export function AdminSidebar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useCurrentUser();
  const logout = useLogout();
  const name = user?.displayName ?? user?.email ?? "";

  return (
    <aside className="box-border flex flex-col gap-5 border-b-[1.5px] border-solid border-ink px-[18px] py-5 lg:sticky lg:top-0 lg:h-dvh lg:w-[248px] lg:shrink-0 lg:gap-7 lg:border-r-[1.5px] lg:border-b-0 lg:py-6">
      <div className="flex items-center justify-between gap-3 lg:flex-col lg:items-start lg:gap-1.5">
        <NavLink to="/" aria-label={t("app.nav.home")} className="inline-flex">
          <Logo height={38} />
        </NavLink>
        <span className="text-[13px] font-semibold text-ink-muted">{t("app.admin.editorial")}</span>
      </div>
      <nav
        aria-label={t("app.admin.navAria")}
        className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible lg:pb-0"
      >
        {SECTIONS.map((section) => (
          <NavLink
            key={section.key}
            to={`/admin/${section.key}`}
            className={({ isActive }) =>
              cn(
                "box-border flex h-11 shrink-0 items-center gap-2.5 rounded-wobble border-[1.5px] border-solid px-3 text-[15px] font-semibold no-underline transition-colors duration-150",
                isActive
                  ? "border-ink bg-wash text-ink shadow-sketch"
                  : "border-transparent text-ink-muted hover:text-ink",
              )
            }
          >
            <Icon name={section.icon} />
            {t(`app.admin.${section.key}`)}
          </NavLink>
        ))}
      </nav>
      <div className="flex items-center gap-2.5 border-t border-solid border-rule pt-4 lg:mt-auto">
        <span aria-hidden="true" className="sk-avatar size-9 shrink-0 bg-note text-[15px]">
          {name.slice(0, 1).toUpperCase()}
        </span>
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate text-[14px] font-semibold">{name}</span>
          <span className="text-[12px] text-ink-muted">{t("app.admin.roleAdmin")}</span>
        </span>
        <ThemeToggleButton className="size-9" />
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={t("app.nav.logout")}
          onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/") })}
        >
          <Icon name="logout" size={18} />
        </Button>
      </div>
    </aside>
  );
}
