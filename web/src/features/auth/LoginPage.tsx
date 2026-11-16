import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Field } from "@/components/sketch/Field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthIntro, YandexEntry } from "@/features/auth/AuthParts";
import { DemoLogin } from "@/features/auth/DemoLogin";
import { useLogin } from "@/features/auth/api";

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") ?? "/me";
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate({ email, password }, { onSuccess: () => navigate(next) });
  };

  return (
    <section className="flex flex-1 flex-col gap-[22px]">
      <AuthIntro title={t("app.auth.loginTitle")} lead={t("app.auth.loginLead")} />
      <DemoLogin next={next} />
      <YandexEntry next={next} />
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label={t("app.auth.email")}>
          {({ id }) => (
            <Input
              id={id}
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          )}
        </Field>
        <div className="flex flex-col gap-2">
          <Field label={t("app.auth.password")}>
            {({ id }) => (
              <Input
                id={id}
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                aria-invalid={login.isError || undefined}
              />
            )}
          </Field>
          <Link to="/reset-password" className="self-end text-[14px] text-brand-text">
            {t("app.auth.forgot")}
          </Link>
        </div>
        <ErrorText error={login.error} code={params.get("error")} />
        <Button variant="secondary" block disabled={login.isPending} className="mt-1">
          {t("app.auth.submitLogin")}
        </Button>
      </form>
      <p className="mt-auto mb-0 text-center text-[15px] text-ink-muted">
        <Link to={`/register?next=${encodeURIComponent(next)}`} className="font-semibold text-ink">
          {t("app.auth.toRegister")}
        </Link>
      </p>
    </section>
  );
}
