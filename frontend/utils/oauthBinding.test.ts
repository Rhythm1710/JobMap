import assert from "node:assert/strict"
import test from "node:test"
import {
  MISSING_OAUTH_COOKIE,
  cookieIsSecure,
  createBrowserNonce,
  gateOauthCallback,
  gmailOauthCookieOptions,
} from "./oauthBinding.ts"

test("the connect cookie is httpOnly, short-lived, and SameSite=Lax", () => {
  const secure = gmailOauthCookieOptions(true)
  assert.equal(secure.httpOnly, true)
  assert.equal(secure.secure, true)
  assert.equal(secure.sameSite, "lax")
  assert.equal(secure.path, "/api/gmail")
  assert.equal(secure.maxAge, 600)

  const local = gmailOauthCookieOptions(false)
  assert.equal(local.secure, false)
  assert.equal(local.httpOnly, true)
})

test("https requests, including a forwarded proto, set the Secure flag", () => {
  assert.equal(cookieIsSecure("https://jobmap.example/api/gmail/connect", null), true)
  assert.equal(cookieIsSecure("http://localhost:3000/api/gmail/connect", "https"), true)
  assert.equal(cookieIsSecure("http://localhost:3000/api/gmail/connect", null), false)
})

test("a callback without the connect cookie is rejected", () => {
  for (const missing of [undefined, null, "", "   "]) {
    const result = gateOauthCallback(missing)
    assert.equal(result.ok, false)
    if (!result.ok) {
      assert.equal(result.reason, "missing")
      assert.equal(result.message, MISSING_OAUTH_COOKIE)
    }
  }
})

test("a callback with the connect cookie is allowed to continue", () => {
  const nonce = createBrowserNonce()
  assert.equal(nonce.length, 64)
  assert.deepEqual(gateOauthCallback(nonce), { ok: true })
})
