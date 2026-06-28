import "dotenv/config";
import { createServer } from "node:http";

import { toNodeHandler } from "better-auth/node";

import { auth } from "./api/_lib/auth";

// Local dev only: serves the SAME Better Auth config the Vercel function deploys.
// Vite proxies /api/auth → here. OTP codes print to this server's console.
const handler = toNodeHandler(auth);
const port = Number(process.env.AUTH_PORT ?? 3001);

createServer((req, res) => {
  if (req.url?.startsWith("/api/auth")) {
    handler(req, res);
    return;
  }
  res.statusCode = 404;
  res.end("not found");
}).listen(port, () => {
  console.log(`🔐 Auth server → http://localhost:${port}/api/auth`);
});
