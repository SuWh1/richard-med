import { betterAuth } from "better-auth";
import { admin, emailOTP, jwt } from "better-auth/plugins";
import { dash } from "@better-auth/infra";
import { Pool } from "pg";

// Admins are granted by email allowlist (env override; defaults to the two owners).
const ADMIN_EMAILS = (
  process.env.ADMIN_EMAILS ?? "aidyn.fatikh@gmail.com,apasdauren70@gmail.com"
)
  .split(",")
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

const isProd = process.env.NODE_ENV === "production";

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL,
  secret: process.env.BETTER_AUTH_SECRET,
  database: new Pool({ connectionString: process.env.DATABASE_URL }),
  trustedOrigins: (process.env.BETTER_AUTH_TRUSTED_ORIGINS ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: true,
  },
  databaseHooks: {
    user: {
      create: {
        before: async (user) => ({
          data: {
            ...user,
            role: ADMIN_EMAILS.includes(user.email.toLowerCase()) ? "admin" : "user",
          },
        }),
      },
    },
  },
  plugins: [
    emailOTP({
      otpLength: 6,
      expiresIn: 600,
      async sendVerificationOTP({ email, otp }) {
        // Local/dev: print the code (no email secrets locally). Prod: send real email.
        if (!isProd) {
          console.log(`[dev OTP] ${email} -> ${otp}`);
          return;
        }
        // TODO(prod): wire your email provider here (Resend/SES/etc.) via env secrets.
      },
    }),
    admin(),
    jwt(), // exposes /api/auth/jwks for the FastAPI backend to verify sessions
    // Better Auth hosted dashboard — only when an API key is configured.
    ...(process.env.BETTER_AUTH_API_KEY ? [dash()] : []),
  ],
});
