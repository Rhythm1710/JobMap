import { auth } from "@clerk/nextjs/server"
import { NextResponse } from "next/server"
import { buildGmailConnectUrl } from "@/utils/ingestion"
import {
  GMAIL_OAUTH_COOKIE,
  cookieIsSecure,
  createBrowserNonce,
  gmailOauthCookieOptions,
} from "@/utils/oauthBinding"

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  const { userId } = auth()
  if (!userId) {
    return NextResponse.redirect(new URL("/", request.url))
  }
  const secure = cookieIsSecure(request.url, request.headers.get("x-forwarded-proto"))
  try {
    const nonce = createBrowserNonce()
    const url = await buildGmailConnectUrl(userId, nonce)
    const response = NextResponse.redirect(url)
    response.cookies.set(GMAIL_OAUTH_COOKIE, nonce, gmailOauthCookieOptions(secure))
    return response
  } catch (error) {
    console.error(error)
    return NextResponse.redirect(new URL("/jobs?gmail=error", request.url))
  }
}
