import { useId } from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { type LocalizedOut, type LocalizedValue } from "@/features/admin/localized";
import { LANGUAGES } from "@/i18n";

const LANGUAGE_NAMES: Record<string, string> = { ru: "Русский", en: "English", zh: "中文" };

interface LocalizedInputProps {
  label: string;
  value: LocalizedValue;
  original?: LocalizedOut;
  multiline?: boolean;
  required?: boolean;
  onChange: (value: LocalizedValue) => void;
}

export function LocalizedInput({
  label,
  value,
  original,
  multiline,
  required,
  onChange,
}: LocalizedInputProps) {
  const { t } = useTranslation();
  const id = useId();
  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-2 border-0 p-0">
      <legend className="mb-2 p-0 text-label">{label}</legend>
      <Tabs defaultValue={LANGUAGES[0]} className="gap-0">
        <TabsList aria-label={label}>
          {LANGUAGES.map((lang, index) => {
            const missing = index > 0 && !value[lang];
            return (
              <TabsTrigger key={lang} value={lang} lang={lang} className="h-9 px-3.5 text-[13px]">
                {LANGUAGE_NAMES[lang] ?? lang.toUpperCase()}
                {missing ? (
                  <span
                    role="img"
                    aria-label={t("app.admin.untranslated")}
                    className="size-[7px] rounded-full border border-dashed border-pencil-solid"
                  />
                ) : null}
              </TabsTrigger>
            );
          })}
        </TabsList>
        {LANGUAGES.map((lang, index) => {
          const field = original?.[lang];
          const isMachine = field?.machine === true && field.text === (value[lang] ?? "");
          const inputId = `${id}-${lang}`;
          const props = {
            id: inputId,
            lang,
            "aria-label": `${label} · ${lang.toUpperCase()}`,
            value: value[lang] ?? "",
            required: required && index === 0,
            onChange: (event: { target: { value: string } }) =>
              onChange({ ...value, [lang]: event.target.value }),
          };
          return (
            <TabsContent
              key={lang}
              value={lang}
              forceMount
              className="flex flex-col gap-2 pt-3 data-[state=inactive]:hidden"
            >
              {multiline ? <Textarea rows={4} {...props} /> : <Input {...props} />}
              {isMachine ? (
                <Badge variant="note" className="self-start">
                  {t("app.admin.machine")}
                </Badge>
              ) : null}
            </TabsContent>
          );
        })}
      </Tabs>
      {LANGUAGES.slice(1).some((lang) => !value[lang]) ? (
        <p className="sk-hint">{t("app.admin.translateHint")}</p>
      ) : null}
    </fieldset>
  );
}
