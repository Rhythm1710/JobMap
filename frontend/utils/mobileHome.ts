export type MobileWeek = {
  label: string
  count: number
  current: boolean
}

export type MobileUpcoming = {
  id: string
  initials: string
  title: string
  body: string
  status: string
  gold: boolean
}

const UPCOMING = ["interview", "assessment", "offer"] as const

export function companyInitials(company: string): string {
  const words = company.split(/[^A-Za-z0-9]+/).filter(Boolean)
  const letters = words.slice(0, 2).map((word) => word[0]!.toUpperCase())
  if (letters.length > 0) return letters.join("")
  const compact = company.replace(/[^A-Za-z0-9]/g, "")
  return (compact.slice(0, 2) || "?").toUpperCase()
}

function startOfWeek(date: Date): Date {
  const copy = new Date(date.getTime())
  const day = copy.getDay()
  const sinceMonday = day === 0 ? 6 : day - 1
  copy.setHours(0, 0, 0, 0)
  copy.setDate(copy.getDate() - sinceMonday)
  return copy
}

function addDays(date: Date, days: number): Date {
  const copy = new Date(date.getTime())
  copy.setDate(copy.getDate() + days)
  return copy
}

function weekLabel(date: Date): string {
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" })
}

export function buildWeekBuckets(
  now: Date,
  instants: Array<Date | null | undefined>,
): MobileWeek[] {
  const start = addDays(startOfWeek(now), -7 * 5)
  const buckets: MobileWeek[] = Array.from({ length: 6 }, (_, index) => {
    const week = addDays(start, 7 * index)
    return {
      label: weekLabel(week),
      count: 0,
      current: index === 5,
    }
  })
  for (const instant of instants) {
    if (!instant) continue
    const time = instant.getTime()
    const index = Math.floor((startOfWeek(instant).getTime() - start.getTime()) / (7 * 24 * 60 * 60 * 1000))
    if (index >= 0 && index < buckets.length && time <= now.getTime() + 24 * 60 * 60 * 1000) {
      buckets[index]!.count += 1
    }
  }
  return buckets
}

export function buildUpcoming(
  jobs: Array<{
    id: string
    status: string
    company: string
    position: string
    appliedLabel: string | null
  }>,
): MobileUpcoming[] {
  const rank = new Map<string, number>(UPCOMING.map((status, index) => [status, index]))
  return jobs
    .filter((job) => rank.has(job.status))
    .sort((a, b) => rank.get(a.status)! - rank.get(b.status)!)
    .slice(0, 3)
    .map((job) => {
      const title =
        job.status === "interview"
          ? `Interview · ${job.position}`
          : job.status === "assessment"
            ? "Assessment due"
            : "Offer to review"
      const body =
        job.status === "interview"
          ? job.appliedLabel
            ? `${job.company} · ${job.appliedLabel}`
            : job.company
          : job.appliedLabel
            ? `${job.position} · ${job.company} · ${job.appliedLabel}`
            : `${job.position} · ${job.company}`
      return {
        id: job.id,
        initials: companyInitials(job.company),
        title,
        body,
        status: job.status,
        gold: job.status === "interview",
      }
    })
}
