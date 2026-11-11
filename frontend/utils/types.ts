import * as z from "zod"

export enum JobStatus {
  Applied = "applied",
  Assessment = "assessment",
  Interview = "interview",
  Offer = "offer",
  Rejected = "rejected",
  Ghosted = "ghosted",
  Withdrawn = "withdrawn",
}

export enum JobMode {
  FullTime = "full-time",
  PartTime = "part-time",
  Internship = "internship",
}

export enum JobSource {
  Manual = "manual",
  Gmail = "gmail",
  Agent = "agent",
}

const LEGACY_STATUS: Record<string, JobStatus> = {
  pending: JobStatus.Applied,
  declined: JobStatus.Rejected,
  decline: JobStatus.Rejected,
}

export function canonicalStatus(status: string): string {
  return LEGACY_STATUS[status] ?? status
}

export const STATUS_FILTER_VALUES: Record<string, string[]> = {
  [JobStatus.Applied]: [JobStatus.Applied, "pending"],
  [JobStatus.Rejected]: [JobStatus.Rejected, "declined", "decline"],
}

export type JobType = {
  id: string
  createdAt: Date | string
  updatedAt: Date | string
  clerkId: string
  position: string
  company: string
  location: string
  status: string
  mode: string
  source: string
  gmailMessageId: string | null
  gmailThreadId: string | null
  appliedAt: Date | string | null
  jobUrl: string | null
  notes: string | null
  companyKey: string
  roleKey: string
  manuallyEdited: boolean
}

export type GmailStatus = {
  connected: boolean
  email: string | null
  lastSyncedAt: string | null
  lastSyncStatus: string | null
  lastSyncError: string | null
  backfillComplete: boolean
}

const httpUrl = z
  .string()
  .max(500)
  .refine((value) => value === "" || /^https?:\/\/\S+$/i.test(value), {
    message: "Enter a valid http(s) URL.",
  })

export const createAndEditJobSchema = z.object({
  position: z.string().min(2, {
    message: "position must be at least 2 characters.",
  }),
  company: z.string().min(2, {
    message: "company must be at least 2 characters.",
  }),
  location: z.string().min(2, {
    message: "location must be at least 2 characters.",
  }),
  status: z.nativeEnum(JobStatus),
  mode: z.nativeEnum(JobMode),
  jobUrl: httpUrl,
  notes: z.string().max(5000),
  appliedAt: z.string().regex(/^$|^\d{4}-\d{2}-\d{2}$/, "Use a valid date."),
})

export type CreateAndEditJobType = z.infer<typeof createAndEditJobSchema>

export function emptyJobForm(): CreateAndEditJobType {
  return {
    position: "",
    company: "",
    location: "",
    status: JobStatus.Applied,
    mode: JobMode.FullTime,
    jobUrl: "",
    notes: "",
    appliedAt: "",
  }
}

export function gmailThreadUrl(threadId: string): string {
  return `https://mail.google.com/mail/u/0/#inbox/${threadId}`
}
