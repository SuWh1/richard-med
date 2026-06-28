import { toNodeHandler } from "better-auth/node";

import { auth } from "../_lib/auth";

// Vercel serverless function: mounts the whole Better Auth API at /api/auth/*.
// Better Auth reads the raw request body, so disable Vercel's body parser.
export const config = { api: { bodyParser: false } };

export default toNodeHandler(auth);
