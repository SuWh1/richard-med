import { type FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { emailOtp } from "@/lib/auth-client";
import { AuthShell, Field, SubmitButton } from "@/components/auth/AuthShell";

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get("email") ?? "";
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resent, setResent] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const res = await emailOtp.verifyEmail({ email, otp });
    setLoading(false);
    if (res.error) setError(res.error.message ?? "Неверный код");
    else navigate("/cabinet");
  };

  const resend = async () => {
    await emailOtp.sendVerificationOtp({ email, type: "email-verification" });
    setResent(true);
  };

  return (
    <AuthShell
      title="Подтвердите email"
      subtitle={`Мы отправили код на ${email || "вашу почту"}`}
      footer={
        <button type="button" onClick={resend} className="text-primary hover:underline">
          {resent ? "Код отправлен повторно" : "Отправить код ещё раз"}
        </button>
      }
    >
      <form onSubmit={onSubmit}>
        <Field
          label="Код из письма"
          value={otp}
          onChange={setOtp}
          placeholder="6 цифр"
          autoComplete="one-time-code"
        />
        {error && <p className="mb-2 text-sm text-destructive">{error}</p>}
        <SubmitButton loading={loading}>Подтвердить</SubmitButton>
      </form>
    </AuthShell>
  );
}
