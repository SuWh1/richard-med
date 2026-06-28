import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signup } from "@/lib/auth-client";
import { AuthShell, Field, SubmitButton } from "@/components/auth/AuthShell";

export function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup(email, password, name || undefined);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось зарегистрироваться");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Регистрация"
      subtitle="Создайте аккаунт — нужен только для личного кабинета"
      footer={
        <>
          Уже есть аккаунт?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Войти
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit}>
        <Field label="Имя" value={name} onChange={setName} autoComplete="name" />
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
          autoComplete="new-password"
        />
        {error && <p className="mb-2 text-sm text-destructive">{error}</p>}
        <SubmitButton loading={loading}>Зарегистрироваться</SubmitButton>
      </form>
    </AuthShell>
  );
}
