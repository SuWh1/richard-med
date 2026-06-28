import { LoginForm } from "@/components/login-form";

export function LoginPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-4 md:p-6">
      <div className="w-full max-w-3xl">
        <LoginForm />
      </div>
    </div>
  );
}
