import assert from "node:assert/strict"
import test from "node:test"
import { jobsListPageQuery } from "./jobsPageQuery.ts"

test("changing page keeps the job source filter", () => {
  const current = new URLSearchParams(
    "search=stripe&jobStatus=applied&jobSource=gmail&page=2",
  )
  const next = new URLSearchParams(jobsListPageQuery(current, 3))
  assert.equal(next.get("search"), "stripe")
  assert.equal(next.get("jobStatus"), "applied")
  assert.equal(next.get("jobSource"), "gmail")
  assert.equal(next.get("page"), "3")
})

test("a missing job source stays empty instead of being dropped", () => {
  const current = new URLSearchParams("search=&jobStatus=interview")
  const next = new URLSearchParams(jobsListPageQuery(current, 1))
  assert.equal(next.get("jobSource"), "")
  assert.equal(next.get("jobStatus"), "interview")
  assert.equal(next.get("page"), "1")
})
