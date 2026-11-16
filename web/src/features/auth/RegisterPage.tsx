import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ApiError } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Field } from "@/components/sketch/Field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthIntro, YandexEntry } from "@/features/auth/AuthParts";
import { useRegister } from "@/features/auth/api";

export default function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") ?? "/me";
  const register = useRegister();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const emailTaken = register.error instanceof ApiError && register.error.code === "email_taken";

  const submit = (event: FormEvent) => {
    event.preventDefault();
    register.mutate(
      { email, password, displayName: displayName.trim() || null },
      { onSuccess: () => navigate(next) },
    );
  };

  return (
    <section className="flex flex-1 flex-col gap-[22px]">
      <AuthIntro title={t("app.auth.registerTitle")} lead={t("app.auth.registerLead")} />
      <YandexEntry next={next} />
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label={t("app.auth.displayName")}>
          {({ id }) => (
            <Input
              id={id}
              value={displayName}
              maxLength={100}
              autoComplete="nickname"
              onChange={(e) => setDisplayName(e.target.value)}
            />
          )}
        </Field>
        <Field
          label={t("app.auth.email")}
          error={
            emailTaken ? (
              <>
                {t("app.errors.email_taken")}.{" "}
                <Link to={`/login?next=${encodeURIComponent(next)}`} className="font-semibold text-danger">
                  {t("app.nav.login")}
                </Link>
              </>
            ) : undefined
          }
        >
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              aria-invalid={invalid || undefined}
              aria-describedby={describedBy}
            />
          )}
        </Field>
        <Field label={t("app.auth.password")} hint={t("app.auth.passwordHint")}>
          {({ id, describedBy }) => (
            <Input
              id={id}
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              aria-describedby={describedBy}
            />
          )}
        </Field>
        {emailTaken ? null : <ErrorText error={register.error} />}
        <Button variant="secondary" block disabled={register.isPending} className="mt-1">
          {t("app.auth.submitRegister")}
        </Button>
      </form>
      <p className="mt-auto mb-0 text-center text-[15px] text-ink-muted">
        <Link to={`/login?next=${encodeURIComponent(next)}`} className="font-semibold text-ink">
          {t("app.auth.toLogin")}
        </Link>
      </p>
    </section>
  );
}
