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

// On Vercel, fall back to the project's production URL if BETTER_AUTH_URL isn't set.
const vercelUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : undefined;
const baseURL = process.env.BETTER_AUTH_URL ?? vercelUrl;

const trustedOrigins = [
  ...(process.env.BETTER_AUTH_TRUSTED_ORIGINS ?? "").split(",").map((s) => s.trim()),
  vercelUrl,
].filter((s): s is string => Boolean(s));

const connectionString = process.env.DATABASE_URL;
// Managed/cloud Postgres needs TLS; localhost does not.
const needsSsl =
  !!connectionString && !/localhost|127\.0\.0\.1/.test(connectionString);

export const auth = betterAuth({
  baseURL,
  secret: process.env.BETTER_AUTH_SECRET,
  database: new Pool({
    connectionString,
    ssl: needsSsl ? { rejectUnauthorized: false } : undefined,
  }),
  trustedOrigins,
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
