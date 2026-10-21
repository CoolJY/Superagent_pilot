/** Set before building Next.js; this public value contains no credentials. */
export const AIR_GAP_MODE = process.env.NEXT_PUBLIC_AIR_GAP_MODE === "true";
export const SERVER_MANAGED_MODEL = AIR_GAP_MODE || process.env.NEXT_PUBLIC_SERVER_MANAGED_MODEL === "true";
export const MODEL_LABEL = process.env.NEXT_PUBLIC_MODEL_LABEL || "AI Assistant";
