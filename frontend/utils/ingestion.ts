/**
 * Server-only client for the Python ingestion service.
 * Do not import this module from a client component.
 */

type SyncResponse = {
  ok: boolean
  error?: string
  created?: number
  updated?: number
  ignored?: number
  deferred?: number
  skipped?: number
  errors?: number
  lastSyncedAt?: string | null
  backfillComplete?: boolean
}

function serviceBase(): string {
  const url = process.env.PYTHON_SERVICE_URL
  if (!url) {
    throw new Error("PYTHON_SERVICE_URL is not set")
  }
  return url.replace(/\/$/, "")
}

function serviceHeaders(): HeadersInit {
  const secret = process.env.SERVICE_SECRET
  if (!secret) {
    throw new Error("SERVICE_SECRET is not set")
  }
  return {
    Authorization: `Bearer ${secret}`,
    "Content-Type": "application/json",
  }
}

async function postJson(path: string, clerkId: string): Promise<Response> {
  return fetch(`${serviceBase()}${path}`, {
    method: "POST",
    headers: serviceHeaders(),
    body: JSON.stringify({ clerkId }),
    cache: "no-store",
  })
}

export async function buildGmailConnectUrl(clerkId: string): Promise<string> {
  const response = await postJson("/gmail/oauth/start", clerkId)
  if (!response.ok) {
    throw new Error("Could not start Gmail connect")
  }
  const data = (await response.json()) as { url?: string }
  if (!data.url) {
    throw new Error("Ingestion service did not return a connect URL")
  }
  return data.url
}

export async function requestGmailSync(clerkId: string): Promise<SyncResponse> {
  const response = await postJson("/gmail/sync", clerkId)
  let data: SyncResponse & { detail?: string } = { ok: response.ok }
  try {
    data = { ...data, ...(await response.json()) }
  } catch {
    data = { ok: false, error: "Gmail sync failed" }
  }
  if (!response.ok) {
    return {
      ok: false,
      error: typeof data.detail === "string" ? data.detail : "Gmail sync failed",
    }
  }
  return { ...data, ok: true }
}

export async function requestGmailDisconnect(
  clerkId: string
): Promise<{ ok: boolean; error?: string }> {
  const response = await postJson("/gmail/disconnect", clerkId)
  if (!response.ok) {
    return { ok: false, error: "Could not disconnect Gmail" }
  }
  return { ok: true }
}
