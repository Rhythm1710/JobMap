"use server"

import prisma from "./db"
import { auth } from "@clerk/nextjs/server"
import {
  JobType,
  CreateAndEditJobType,
  createAndEditJobSchema,
  JobStatus,
  canonicalStatus,
  STATUS_FILTER_VALUES,
} from "./types"
import { normalizeKey, normalizeRole } from "./normalize"
import { redirect } from "next/navigation"
import { Prisma } from "@prisma/client"
import dayjs from "dayjs"

function authenticateAndRedirect(): string {
  const { userId } = auth()

  if (!userId) {
    redirect("/")
  }
  return userId
}

function presentJob<T extends { status: string }>(job: T): T {
  return { ...job, status: canonicalStatus(job.status) }
}

function appliedAtFromForm(value: string): Date | null {
  if (!value) return null
  return new Date(`${value}T00:00:00.000Z`)
}

export async function createJobAction(
  values: CreateAndEditJobType
): Promise<JobType | null> {
  const userId = authenticateAndRedirect()
  try {
    const parsed = createAndEditJobSchema.parse(values)
    const job = await prisma.job.create({
      data: {
        position: parsed.position,
        company: parsed.company,
        location: parsed.location,
        status: parsed.status,
        mode: parsed.mode,
        clerkId: userId,
        source: "manual",
        jobUrl: parsed.jobUrl || null,
        notes: parsed.notes.trim() || null,
        appliedAt: appliedAtFromForm(parsed.appliedAt) ?? new Date(),
        companyKey: normalizeKey(parsed.company),
        roleKey: normalizeRole(parsed.position),
        manuallyEdited: false,
      },
    })
    return presentJob(job)
  } catch (error) {
    console.error(error)
    return null
  }
}

type GetAllJobsActionTypes = {
  search?: string
  jobStatus?: string
  jobSource?: string
  page?: number
  limit?: number
}

export async function getAllJobsAction({
  search,
  jobStatus,
  jobSource,
  page = 1,
  limit = 10,
}: GetAllJobsActionTypes): Promise<{
  jobs: JobType[]
  count: number
  page: number
  totalPages: number
}> {
  const userId = authenticateAndRedirect()

  try {
    let whereClause: Prisma.JobWhereInput = {
      clerkId: userId,
    }
    if (search) {
      whereClause = {
        ...whereClause,
        OR: [
          { position: { contains: search, mode: "insensitive" } },
          { company: { contains: search, mode: "insensitive" } },
        ],
      }
    }
    if (jobStatus && jobStatus !== "all") {
      whereClause = {
        ...whereClause,
        status: { in: STATUS_FILTER_VALUES[jobStatus] ?? [jobStatus] },
      }
    }
    if (jobSource && jobSource !== "all") {
      whereClause = {
        ...whereClause,
        source: jobSource,
      }
    }
    const skip = (page - 1) * limit

    const jobs = await prisma.job.findMany({
      where: whereClause,
      skip,
      take: limit,
      orderBy: [
        { appliedAt: { sort: "desc", nulls: "last" } },
        { createdAt: "desc" },
      ],
    })
    const count: number = await prisma.job.count({
      where: whereClause,
    })
    const totalPages = Math.ceil(count / limit)
    return { jobs: jobs.map((job) => presentJob(job)), count, page, totalPages }
  } catch (error) {
    console.error(error)
    return { jobs: [], count: 0, page: 1, totalPages: 0 }
  }
}

export async function deleteJobAction(id: string): Promise<JobType | null> {
  const userId = authenticateAndRedirect()

  try {
    const job = await prisma.job.delete({
      where: {
        id,
        clerkId: userId,
      },
    })
    return presentJob(job)
  } catch (error) {
    return null
  }
}

export async function getSingleJobAction(id: string): Promise<JobType | null> {
  let job: JobType | null = null
  const userId = authenticateAndRedirect()

  try {
    const row = await prisma.job.findUnique({
      where: {
        id,
        clerkId: userId,
      },
    })
    job = row ? presentJob(row) : null
  } catch (error) {
    job = null
  }
  if (!job) {
    redirect("/jobs")
  }
  return job
}

export async function updateJobAction(
  id: string,
  values: CreateAndEditJobType
): Promise<JobType | null> {
  const userId = authenticateAndRedirect()

  try {
    const parsed = createAndEditJobSchema.parse(values)
    const existing = await prisma.job.findUnique({
      where: { id, clerkId: userId },
    })
    if (!existing) return null
    const identityChanged =
      existing.company !== parsed.company ||
      existing.position !== parsed.position ||
      existing.location !== parsed.location ||
      existing.mode !== parsed.mode ||
      (existing.jobUrl || "") !== (parsed.jobUrl || "")
    const job = await prisma.job.update({
      where: {
        id,
        clerkId: userId,
      },
      data: {
        position: parsed.position,
        company: parsed.company,
        location: parsed.location,
        status: parsed.status,
        mode: parsed.mode,
        jobUrl: parsed.jobUrl || null,
        notes: parsed.notes.trim() || null,
        appliedAt: appliedAtFromForm(parsed.appliedAt),
        companyKey: normalizeKey(parsed.company),
        roleKey: normalizeRole(parsed.position),
        manuallyEdited: existing.manuallyEdited || identityChanged,
      },
    })
    return presentJob(job)
  } catch (error) {
    return null
  }
}

export async function getStatsAction(): Promise<Record<JobStatus, number>> {
  const userId = authenticateAndRedirect()
  try {
    const stats = await prisma.job.groupBy({
      by: ["status"],
      _count: {
        status: true,
      },
      where: {
        clerkId: userId,
      },
    })
    const counts = stats.reduce((acc, curr) => {
      acc[curr.status] = curr._count.status
      return acc
    }, {} as Record<string, number>)

    const result = Object.values(JobStatus).reduce((acc, status) => {
      acc[status] = counts[status] ?? 0
      return acc
    }, {} as Record<JobStatus, number>)
    result[JobStatus.Applied] += counts.pending ?? 0
    result[JobStatus.Rejected] += (counts.declined ?? 0) + (counts.decline ?? 0)
    return result
  } catch (error) {
    redirect("/jobs")
  }
}

export async function getChartsDataAction(): Promise<
  Array<{ date: string; count: number }>
> {
  const userId = authenticateAndRedirect()
  const twelveMonthsAgo = dayjs().subtract(12, "month").toDate()
  try {
    const jobs = await prisma.job.findMany({
      where: {
        clerkId: userId,
        OR: [
          { appliedAt: { gte: twelveMonthsAgo } },
          { appliedAt: null, createdAt: { gte: twelveMonthsAgo } },
        ],
      },
      orderBy: {
        appliedAt: "asc",
      },
    })

    const applicationsPerMonth = jobs.reduce((acc, job) => {
      const date = dayjs(job.appliedAt ?? job.createdAt).format("MMM YY")
      const existingEntry = acc.find((entry) => entry.date === date)
      if (existingEntry) {
        existingEntry.count += 1
      } else {
        acc.push({ date, count: 1 })
      }
      return acc
    }, [] as Array<{ date: string; count: number }>)

    return applicationsPerMonth
  } catch (error) {
    redirect("/jobs")
  }
}
