import assert from "node:assert/strict"
import test from "node:test"
import { DEFAULT_CREATE_STATUS, statusManualOnCreate } from "./statusManual.ts"

test("create sets statusManual only for an explicit status, so default applied stays ghost-eligible", () => {
  assert.equal(DEFAULT_CREATE_STATUS, "applied")
  assert.equal(statusManualOnCreate("applied"), false)

  for (const status of [
    "assessment",
    "interview",
    "offer",
    "rejected",
    "ghosted",
    "withdrawn",
  ]) {
    assert.equal(statusManualOnCreate(status), true, status)
  }
})
