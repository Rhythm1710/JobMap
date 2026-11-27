import assert from "node:assert/strict"
import test from "node:test"
import { isProtectedPath, safeCallbackPath } from "./authPaths.ts"

test("protected paths match the routes Clerk protected", () => {
  for (const path of ["/add-job", "/jobs", "/jobs/abc", "/stats"]) {
    assert.equal(isProtectedPath(path), true, path)
  }
  for (const path of ["/", "/signin", "/api/auth/callback/google", "/api/gmail/callback"]) {
    assert.equal(isProtectedPath(path), false, path)
  }
})

test("sign-in only redirects to a relative in-app path", () => {
  assert.equal(safeCallbackPath("/add-job"), "/add-job")
  assert.equal(safeCallbackPath("/jobs?gmail=connected"), "/jobs?gmail=connected")
  assert.equal(safeCallbackPath(undefined), "/jobs")
  assert.equal(safeCallbackPath("https://evil.example/jobs"), "/jobs")
  assert.equal(safeCallbackPath("//evil.example"), "/jobs")
})
