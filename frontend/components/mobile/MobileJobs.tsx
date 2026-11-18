"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { getAllJobsAction } from "@/utils/actions"
import { companyInitials } from "@/utils/mobileHome"
import { jobsFilterQuery, jobsListPageQuery } from "@/utils/jobsPageQuery"
import { JobType } from "@/utils/types"
import { MobilePageTitle } from "./MobileStats"
import { SourcePill, StatusPill } from "./StatusPill"

export type JobFacets = {
  total: number
  interview: number
  offer: number
  applied: number
  gmail: number
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true" className="shrink-0">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  )
}

function PinIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 21s7-5.2 7-11a7 7 0 1 0-14 0c0 5.8 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.2" />
    </svg>
  )
}

function BriefcaseIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V6a4 4 0 0 1 8 0v1" />
    </svg>
  )
}

function CalendarIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M8 3v4M16 3v4M3 10h18" />
    </svg>
  )
}

function appliedLabel(job: JobType): string {
  const when = job.appliedAt || job.createdAt
  const date = new Date(when)
  if (Number.isNaN(date.getTime())) return "Applied"
  return `Applied ${date.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`
}

function Chip({
  on,
  href,
  label,
  count,
}: {
  on: boolean
  href: string
  label: string
  count?: number
}) {
  return (
    <Link
      href={href}
      aria-current={on ? "true" : undefined}
      className={`inline-flex h-8 shrink-0 items-center gap-1 whitespace-nowrap rounded-full border px-3 text-[12px] font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B] ${
        on ? "border-[#18181B] bg-[#18181B] text-white" : "border-[#E4E4E7] bg-white text-[#71717A]"
      }`}
    >
      {label}
      {count == null ? null : <span className="text-[11px] font-medium opacity-75">{count}</span>}
    </Link>
  )
}

export function MobileJobs({
  facets,
  rows,
}: {
  facets: JobFacets
  rows?: { jobs: JobType[]; count: number; page?: number; totalPages?: number }
}) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const search = searchParams.get("search") || ""
  const jobStatus = searchParams.get("jobStatus") || "all"
  const jobSource = searchParams.get("jobSource") || "all"
  const pageNumber = Number(searchParams.get("page")) || 1
  const gmailOn = jobSource === "gmail" && (jobStatus === "all" || jobStatus === "")
  const statusOn = (value: string) => !gmailOn && jobStatus === value
  const allOn = !gmailOn && (jobStatus === "all" || jobStatus === "")

  const { data, isPending } = useQuery({
    queryKey: ["jobs", search, jobStatus, jobSource, pageNumber],
    queryFn: () => getAllJobsAction({ search, jobStatus, jobSource, page: pageNumber }),
    enabled: !rows,
  })
  const jobs = rows?.jobs || data?.jobs || []
  const count = rows?.count ?? data?.count ?? 0
  const page = rows?.page || data?.page || pageNumber
  const totalPages = rows?.totalPages ?? data?.totalPages ?? 0
  const pending = !rows && isPending

  function filterHref(status: string, source: string) {
    const query = jobsFilterQuery(search, status, source)
    return query ? `/jobs?${query}` : "/jobs"
  }

  function onSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = String(new FormData(event.currentTarget).get("search") || "")
    const query = jobsFilterQuery(value, jobStatus, jobSource)
    router.push(query ? `/jobs?${query}` : "/jobs")
  }

  function goToPage(nextPage: number) {
    router.push(`/jobs?${jobsListPageQuery(searchParams, nextPage)}`)
  }

  return (
    <div className="md:hidden">
      <MobilePageTitle
        title="Jobs"
        subtitle={pending ? "Loading applications" : `${jobs.length} of ${count} applications`}
      />
      <div className="flex flex-col gap-3">
        <form onSubmit={onSearch}>
          <label className="flex h-10 items-center gap-2 rounded-[10px] bg-[#F4F4F5] px-3 text-[#71717A]">
            <SearchIcon />
            <input
              key={search}
              name="search"
              defaultValue={search}
              placeholder="Search roles or companies"
              aria-label="Search roles or companies"
              className="w-full bg-transparent text-[14px] text-[#09090B] outline-none placeholder:text-[#A1A1AA]"
            />
          </label>
        </form>
        <div className="flex gap-1.5 overflow-x-auto">
          <Chip on={allOn} href={filterHref("all", "all")} label="All" count={facets.total} />
          <Chip on={statusOn("interview")} href={filterHref("interview", "all")} label="Interview" count={facets.interview} />
          <Chip on={statusOn("offer")} href={filterHref("offer", "all")} label="Offer" count={facets.offer} />
          <Chip on={statusOn("applied")} href={filterHref("applied", "all")} label="Applied" count={facets.applied} />
          <Chip on={gmailOn} href={filterHref("all", "gmail")} label="Gmail" />
        </div>
        <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 pt-3">
          {pending ? <p className="pb-3 text-[13px] text-[#71717A]">Loading...</p> : null}
          {!pending && jobs.length === 0 ? (
            <p className="pb-3 text-[13px] text-[#71717A]">No jobs match.</p>
          ) : null}
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="flex items-start gap-2.5 border-t border-[#E4E4E7] py-2.5 text-inherit no-underline first:border-t-0 first:pt-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B]"
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-[10px] text-[12px] font-bold tracking-[-0.02em] ${
                  job.status === "interview" ? "bg-[#F8B500] text-[#18181B]" : "bg-[#18181B] text-white"
                }`}
              >
                {companyInitials(job.company)}
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-[14px] font-semibold tracking-[-0.02em] text-[#09090B]">{job.position}</h3>
                <div className="mt-px text-[12px] text-[#71717A]">{job.company}</div>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px] text-[#71717A]">
                  <span className="inline-flex items-center gap-[3px]"><PinIcon />{job.location}</span>
                  <span className="inline-flex items-center gap-[3px]"><BriefcaseIcon />{job.mode}</span>
                  <span className="inline-flex items-center gap-[3px]"><CalendarIcon />{appliedLabel(job)}</span>
                  <SourcePill source={job.source} />
                </div>
              </div>
              <span className="mt-px">
                <StatusPill status={job.status} />
              </span>
            </Link>
          ))}
          <div className="h-3" />
        </section>
        {totalPages > 1 ? (
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              className="h-10 rounded-[10px] border border-[#E4E4E7] bg-white px-3 text-[13px] font-semibold text-[#09090B] disabled:opacity-50"
              disabled={page <= 1}
              onClick={() => goToPage(page - 1)}
            >
              Previous
            </button>
            <p className="text-[12px] text-[#71717A]">{page} / {totalPages}</p>
            <button
              type="button"
              className="h-10 rounded-[10px] border border-[#E4E4E7] bg-white px-3 text-[13px] font-semibold text-[#09090B] disabled:opacity-50"
              disabled={page >= totalPages}
              onClick={() => goToPage(page + 1)}
            >
              Next
            </button>
          </div>
        ) : null}
      </div>
    </div>
  )
}
