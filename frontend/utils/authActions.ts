"use server"

import { signIn, signOut } from "@/auth"
import { safeCallbackPath } from "./authPaths"

export async function signInWithGoogle(formData: FormData) {
  const callbackUrl = safeCallbackPath(String(formData.get("callbackUrl") ?? ""))
  await signIn("google", { redirectTo: callbackUrl })
}

export async function signOutToHome() {
  await signOut({ redirectTo: "/" })
}
