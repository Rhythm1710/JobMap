import { auth } from "@/auth"
import { NextResponse } from "next/server"
import { isProtectedPath } from "@/utils/authPaths"

export default auth((req) => {
  const { pathname, search } = req.nextUrl
  if (pathname.startsWith("/api/auth")) return NextResponse.next()
  if (!isProtectedPath(pathname)) return NextResponse.next()
  if (req.auth?.user?.id) return NextResponse.next()

  const signInUrl = new URL("/signin", req.nextUrl.origin)
  signInUrl.searchParams.set("callbackUrl", `${pathname}${search}`)
  return NextResponse.redirect(signInUrl)
})

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
}
