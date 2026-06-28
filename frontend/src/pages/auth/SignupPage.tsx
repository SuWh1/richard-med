import { SignupForm } from "@/components/signup-form";

export function SignupPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-4 md:p-6">
      <div className="w-full max-w-3xl">
        <SignupForm />
      </div>
    </div>
  );
}
