import assert from "node:assert/strict"
import test from "node:test"
import { buildUpcoming, buildWeekBuckets, companyInitials } from "./mobileHome.ts"

test("company initials use the first two words", () => {
  assert.equal(companyInitials("Northwind Labs"), "NL")
  assert.equal(companyInitials("Cedar & Co."), "CC")
  assert.equal(companyInitials("Harbor Health"), "HH")
})

test("week buckets count the last six weeks and mark the current one", () => {
  const now = new Date(2026, 10, 16, 12)
  const weeks = buildWeekBuckets(now, [
    new Date(2026, 10, 16, 8),
    new Date(2026, 10, 17, 8),
    new Date(2026, 9, 1, 8),
  ])
  assert.equal(weeks.length, 6)
  assert.equal(weeks[5]?.current, true)
  assert.equal(weeks[5]?.count, 2)
  assert.equal(weeks.reduce((sum, week) => sum + week.count, 0), 2)
})

test("upcoming uses real jobs and does not invent a clock time", () => {
  const rows = buildUpcoming([
    {
      id: "1",
      status: "offer",
      company: "Kiteworks Studio",
      position: "iOS Engineer",
      appliedLabel: "20 Oct",
    },
    {
      id: "2",
      status: "interview",
      company: "Northwind Labs",
      position: "Product Designer",
      appliedLabel: null,
    },
    {
      id: "3",
      status: "applied",
      company: "Harbor Health",
      position: "Intern",
      appliedLabel: "12 Nov",
    },
  ])
  assert.deepEqual(
    rows.map((row) => row.status),
    ["interview", "offer"],
  )
  assert.equal(rows[0]?.gold, true)
  assert.equal(rows[1]?.gold, false)
  assert.equal(rows[0]?.title, "Interview · Product Designer")
  assert.equal(rows[0]?.body, "Northwind Labs")
  assert.equal(rows[1]?.body, "iOS Engineer · Kiteworks Studio · 20 Oct")
  assert.equal(rows[0]?.body.includes(":"), false)
})
