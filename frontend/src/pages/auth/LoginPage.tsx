import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signIn } from "@/lib/auth-client";
import { AuthShell, Field, SubmitButton } from "@/components/auth/AuthShell";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const res = await signIn.email({ email, password });
    setLoading(false);
    if (res.error) setError(res.error.message ?? "Не удалось войти");
    else navigate("/cabinet");
  };

  return (
    <AuthShell
      title="Вход"
      subtitle="Войдите в личный кабинет"
      footer={
        <>
          Нет аккаунта?{" "}
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Регистрация
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit}>
        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
          placeholder="you@example.com"
        />
        <Field
          label="Пароль"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />
        {error && <p className="mb-2 text-sm text-destructive">{error}</p>}
        <SubmitButton loading={loading}>Войти</SubmitButton>
      </form>
    </AuthShell>
  );
}
