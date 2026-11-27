import assert from "node:assert/strict"
import test from "node:test"
import { isClerkUserId, legacyClerkIdToAdopt, stableUserId } from "./identity.ts"

const clerkId = "user_2i6ZOgrlYTxxcqo26PlMfmt3Xiz"
const googleSub = "109876543210987654321"

test("the session user id is the Google subject, not a random id", () => {
  assert.equal(
    stableUserId({ providerAccountId: googleSub, profileSub: googleSub }),
    googleSub,
  )
  assert.equal(stableUserId({ profileSub: googleSub }), googleSub)
  assert.equal(stableUserId({ providerAccountId: "  ", profileSub: googleSub }), googleSub)
  assert.equal(stableUserId({}), null)
})

test("a Clerk id is recognized and a Google subject is not", () => {
  assert.equal(isClerkUserId(clerkId), true)
  assert.equal(isClerkUserId(googleSub), false)
  assert.equal(isClerkUserId("user_"), false)
})

test("legacy rows are adopted only when one Gmail email matches a Clerk id", () => {
  const rows = [{ clerkId, email: "Owner@Gmail.com" }]
  assert.equal(legacyClerkIdToAdopt(rows, "owner@gmail.com", googleSub), clerkId)
  assert.equal(legacyClerkIdToAdopt(rows, "other@gmail.com", googleSub), null)
  assert.equal(legacyClerkIdToAdopt(rows, "owner@gmail.com", clerkId), null)
  assert.equal(
    legacyClerkIdToAdopt(
      [
        { clerkId, email: "owner@gmail.com" },
        { clerkId: "user_2otherClerkId0000000000", email: "owner@gmail.com" },
      ],
      "owner@gmail.com",
      googleSub,
    ),
    null,
  )
  assert.equal(
    legacyClerkIdToAdopt(
      [{ clerkId: googleSub, email: "owner@gmail.com" }],
      "owner@gmail.com",
      "another-google-sub",
    ),
    null,
  )
})
