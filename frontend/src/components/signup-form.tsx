import { type ComponentProps, type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signup } from "@/lib/auth-client";
import { cn } from "@/components/ui/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Logo } from "@/components/Logo";
import { BrandPanel } from "@/components/auth/BrandPanel";

export function SignupForm({ className, ...props }: ComponentProps<"div">) {
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
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" onSubmit={onSubmit}>
            <FieldGroup>
              <div className="flex flex-col items-center gap-1 text-center">
                <Logo />
                <h1 className="mt-3 text-2xl font-bold">Регистрация</h1>
                <p className="text-muted-foreground">
                  Аккаунт нужен только для личного кабинета
                </p>
              </div>
              <Field>
                <FieldLabel htmlFor="name">Имя</FieldLabel>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="password">Пароль</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
              </Field>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Field>
                <Button type="submit" disabled={loading}>
                  {loading ? "Создаём…" : "Зарегистрироваться"}
                </Button>
              </Field>
              <FieldDescription className="text-center">
                Уже есть аккаунт?{" "}
                <Link
                  to="/login"
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  Войти
                </Link>
              </FieldDescription>
            </FieldGroup>
          </form>
          <BrandPanel />
        </CardContent>
      </Card>
    </div>
  );
}
