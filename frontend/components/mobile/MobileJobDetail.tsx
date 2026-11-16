"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { getSingleJobAction } from "@/utils/actions"
import { companyInitials } from "@/utils/mobileHome"
import { gmailThreadUrl, JobType } from "@/utils/types"
import EditJobForm from "@/components/EditJobForm"
import { StatusPill } from "./StatusPill"

function MailIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 6h16v12H4z" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  )
}

function LinkIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 5h5v5" />
      <path d="M20 4 10 14" />
      <path d="M11 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5" />
    </svg>
  )
}

const actionClass =
  "inline-flex h-10 flex-1 items-center justify-center gap-1.5 rounded-[10px] border px-3 text-[13px] font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B]"

function longDate(value: Date | string | null): string {
  if (!value) return "Not set"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not set"
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
}

export function MobileJobDetail({ jobId, job }: { jobId: string; job?: JobType }) {
  const [editing, setEditing] = useState(false)
  const { data: loaded, isPending } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getSingleJobAction(jobId),
    enabled: !job,
  })
  const data = job ?? loaded

  if (!data) {
    return <p className="text-[13px] text-[#71717A] md:hidden">{isPending ? "Loading..." : "Job not found."}</p>
  }
  if (editing) {
    return (
      <div className="md:hidden">
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="mb-3 text-[15px] font-medium text-[#09090B]"
        >
          Back to details
        </button>
        <EditJobForm jobId={jobId} />
      </div>
    )
  }

  const gold = data.status === "interview"
  return (
    <div className="md:hidden">
      <div className="flex items-start gap-2.5 pb-2.5">
        <div
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-[12px] text-[14px] font-bold tracking-[-0.02em] ${
            gold ? "bg-[#F8B500] text-[#18181B]" : "bg-[#18181B] text-white"
          }`}
        >
          {companyInitials(data.company)}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-[22px] font-bold leading-[1.2] tracking-[-0.03em] text-[#09090B]">
            {data.position}
          </h1>
          <p className="mt-0.5 text-[13px] text-[#71717A]">{data.company}</p>
        </div>
        <span className="mt-px">
          <StatusPill status={data.status} />
        </span>
      </div>
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          {data.gmailThreadId ? (
            <a className={`${actionClass} border-[#E4E4E7] bg-white text-[#09090B]`} href={gmailThreadUrl(data.gmailThreadId)} target="_blank" rel="noreferrer">
              <MailIcon /> Email
            </a>
          ) : null}
          {data.jobUrl ? (
            <a className={`${actionClass} border-[#E4E4E7] bg-white text-[#09090B]`} href={data.jobUrl} target="_blank" rel="noreferrer">
              <LinkIcon /> Posting
            </a>
          ) : null}
          <button type="button" className={`${actionClass} border-[#18181B] bg-[#18181B] text-white`} onClick={() => setEditing(true)}>
            Edit
          </button>
        </div>
        <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 py-3">
          <div className="grid grid-cols-2 gap-x-3 gap-y-2.5">
            <div>
              <div className="text-[11px] font-medium text-[#71717A]">Location</div>
              <div className="mt-0.5 text-[13px] font-semibold text-[#09090B]">{data.location}</div>
            </div>
            <div>
              <div className="text-[11px] font-medium text-[#71717A]">Mode</div>
              <div className="mt-0.5 text-[13px] font-semibold text-[#09090B]">{data.mode}</div>
            </div>
            <div>
              <div className="text-[11px] font-medium text-[#71717A]">Applied</div>
              <div className="mt-0.5 text-[13px] font-semibold text-[#09090B]">{longDate(data.appliedAt)}</div>
            </div>
            <div>
              <div className="text-[11px] font-medium text-[#71717A]">Source</div>
              <div className="mt-0.5 text-[13px] font-semibold text-[#09090B]">{data.source}</div>
            </div>
          </div>
        </section>
        {data.notes ? (
          <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 py-3">
            <h2 className="mb-2.5 text-[13px] font-semibold text-[#09090B]">Notes</h2>
            <p className="whitespace-pre-wrap text-[13px] leading-[1.5] text-[#09090B]">{data.notes}</p>
          </section>
        ) : null}
        {data.gmailThreadId ? (
          <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 py-3">
            <div className="mb-2.5 flex items-baseline justify-between">
              <h2 className="text-[13px] font-semibold text-[#09090B]">Activity</h2>
              <span className="text-[11px] text-[#71717A]">Gmail thread</span>
            </div>
            <div className="grid grid-cols-[16px_1fr] gap-2.5">
              <div className="mt-[3px] h-3 w-3 rounded-full border-2 border-white bg-[#F8B500] shadow-[0_0_0_1.5px_#F8B500]" />
              <div>
                <h3 className="text-[13px] font-semibold text-[#09090B]">Email thread</h3>
                <p className="mt-px text-[12px] text-[#71717A]">Open the Gmail thread for this application.</p>
              </div>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  )
}
