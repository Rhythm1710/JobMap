import { cookies } from "next/headers"
import { NextResponse } from "next/server"
import { completeGmailOauth } from "@/utils/ingestion"
import {
  GMAIL_OAUTH_COOKIE,
  cookieIsSecure,
  gateOauthCallback,
  gmailOauthCookieOptions,
} from "@/utils/oauthBinding"

export const dynamic = "force-dynamic"

function finish(request: Request, gmail: string) {
  const secure = cookieIsSecure(request.url, request.headers.get("x-forwarded-proto"))
  const response = NextResponse.redirect(new URL(`/jobs?gmail=${gmail}`, request.url))
  response.cookies.set(GMAIL_OAUTH_COOKIE, "", {
    ...gmailOauthCookieOptions(secure),
    maxAge: 0,
  })
  return response
}

export async function GET(request: Request) {
  const url = new URL(request.url)
  const code = url.searchParams.get("code")
  const state = url.searchParams.get("state")
  const oauthError = url.searchParams.get("error")
  const cookieNonce = cookies().get(GMAIL_OAUTH_COOKIE)?.value

  if (oauthError || !code || !state) {
    return finish(request, "denied")
  }

  const gate = gateOauthCallback(cookieNonce)
  if (!gate.ok) {
    return finish(request, "cookie")
  }

  try {
    const result = await completeGmailOauth(code, state, cookieNonce as string)
    if (!result.ok) {
      const mismatch = result.status === 403 && result.error.includes("did not match")
      return finish(request, mismatch ? "mismatch" : "error")
    }
    return finish(request, "connected")
  } catch (error) {
    console.error(error)
    return finish(request, "error")
  }
}
