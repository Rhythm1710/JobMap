import { auth } from "@clerk/nextjs/server"
import { NextResponse } from "next/server"
import { buildGmailConnectUrl } from "@/utils/ingestion"

export const dynamic = "force-dynamic"

export async function GET(request: Request) {
  const { userId } = auth()
  if (!userId) {
    return NextResponse.redirect(new URL("/", request.url))
  }
  try {
    const url = await buildGmailConnectUrl(userId)
    return NextResponse.redirect(url)
  } catch (error) {
    console.error(error)
    return NextResponse.redirect(new URL("/jobs?gmail=error", request.url))
  }
}
