/**
 * Binds a Gmail OAuth attempt to the browser that started it.
 * The route handlers set and clear the cookie. This module stays free of Next.js
 * so the cookie rules can be tested without a server.
 */

export const GMAIL_OAUTH_COOKIE = "gmail_oauth_nonce"
export const OAUTH_COOKIE_MAX_AGE_SECONDS = 10 * 60

export const MISSING_OAUTH_COOKIE =
  "Gmail connect could not be verified because this browser did not start it. Use Connect Gmail again in this browser."

export type OauthCookieOptions = {
  httpOnly: true
  secure: boolean
  sameSite: "lax"
  path: "/api/gmail"
  maxAge: number
}

export function createBrowserNonce(): string {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")
}

export function cookieIsSecure(requestUrl: string, forwardedProto: string | null): boolean {
  const proto = forwardedProto?.split(",")[0]?.trim()
  if (proto) return proto === "https"
  return new URL(requestUrl).protocol === "https:"
}

export function gmailOauthCookieOptions(secure: boolean): OauthCookieOptions {
  return {
    httpOnly: true,
    // Secure is set on HTTPS (Vercel sets x-forwarded-proto). Local http omits it
    // so the browser will store the cookie. SameSite=Lax is required: Strict would
    // drop the cookie on the top-level redirect back from accounts.google.com.
    secure,
    sameSite: "lax",
    path: "/api/gmail",
    maxAge: OAUTH_COOKIE_MAX_AGE_SECONDS,
  }
}

export function gateOauthCallback(
  cookieNonce: string | undefined | null
): { ok: true } | { ok: false; reason: "missing"; message: string } {
  if (!cookieNonce || !cookieNonce.trim()) {
    return { ok: false, reason: "missing", message: MISSING_OAUTH_COOKIE }
  }
  return { ok: true }
}
