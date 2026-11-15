import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { type ThemePreference, useTheme } from "@/lib/theme";

const OPTIONS: ThemePreference[] = ["light", "dark", "system"];

export function ThemeSwitcher({ className }: { className?: string }) {
  const { t } = useTranslation();
  const { preference, setPreference } = useTheme();
  return (
    <ToggleGroup
      type="single"
      value={preference}
      aria-label={t("app.theme.title")}
      onValueChange={(value) => {
        const next = OPTIONS.find((option) => option === value);
        if (next) setPreference(next);
      }}
      className={className}
    >
      {OPTIONS.map((option) => (
        <ToggleGroupItem key={option} value={option}>
          {t(`app.theme.${option}`)}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

export function ThemeToggleButton({ className }: { className?: string }) {
  const { t } = useTranslation();
  const { resolved, setPreference } = useTheme();
  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      className={className}
      aria-label={t("app.theme.toggle")}
      onClick={() => setPreference(resolved === "dark" ? "light" : "dark")}
    >
      <Icon name={resolved === "dark" ? "sun" : "moon"} />
    </Button>
  );
}
