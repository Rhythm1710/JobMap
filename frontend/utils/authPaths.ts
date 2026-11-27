const FALLBACK_CALLBACK = "/jobs"

/** Same paths Clerk's middleware protected: /add-job, /jobs(.*), /stats. */
export function isProtectedPath(pathname: string): boolean {
  return pathname === "/add-job" || pathname === "/stats" || pathname.startsWith("/jobs")
}

/** Relative in-app paths only, so the sign-in redirect cannot leave this host. */
export function safeCallbackPath(value: string | null | undefined): string {
  if (!value) return FALLBACK_CALLBACK
  if (!value.startsWith("/")) return FALLBACK_CALLBACK
  if (value.startsWith("//") || value.startsWith("/\\")) return FALLBACK_CALLBACK
  if (value.includes("://") || value.includes("\\")) return FALLBACK_CALLBACK
  return value
}
