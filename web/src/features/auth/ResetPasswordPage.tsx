import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Field } from "@/components/sketch/Field";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { AuthIntro } from "@/features/auth/AuthParts";
import { useConfirmReset, useRequestReset } from "@/features/auth/api";

export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const token = params.get("token");
  const request = useRequestReset();
  const confirm = useConfirmReset();
  const [value, setValue] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (token) confirm.mutate({ token, password: value });
    else request.mutate(value);
  };

  const done = token ? confirm.isSuccess : request.isSuccess;
  return (
    <section className="flex flex-1 flex-col gap-[22px]">
      <AuthIntro title={t("app.auth.resetTitle")} lead={token ? undefined : t("app.auth.resetLead")} />
      {done ? (
        <>
          <Alert variant="success">
            <Icon name="check" />
            <AlertDescription>{token ? t("app.auth.resetDone") : t("app.auth.resetSent")}</AlertDescription>
          </Alert>
          <Button asChild variant="secondary" block>
            <Link to="/login">{t("app.nav.login")}</Link>
          </Button>
        </>
      ) : (
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label={token ? t("app.auth.newPassword") : t("app.auth.email")}>
            {({ id }) => (
              <Input
                id={id}
                type={token ? "password" : "email"}
                minLength={token ? 8 : undefined}
                required
                autoComplete={token ? "new-password" : "email"}
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
            )}
          </Field>
          <ErrorText error={token ? confirm.error : request.error} />
          <Button block disabled={request.isPending || confirm.isPending} className="mt-1">
            {token ? t("app.auth.resetSave") : t("app.auth.resetSend")}
          </Button>
        </form>
      )}
    </section>
  );
}
