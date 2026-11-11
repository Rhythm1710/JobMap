"use server"

import { auth } from "@clerk/nextjs/server"
import { redirect } from "next/navigation"
import prisma from "./db"
import { requestGmailDisconnect, requestGmailSync } from "./ingestion"
import { GmailStatus } from "./types"

function requireUser(): string {
  const { userId } = auth()
  if (!userId) {
    redirect("/")
  }
  return userId
}

export async function getGmailStatusAction(): Promise<GmailStatus> {
  const userId = requireUser()
  const row = await prisma.gmailConnection.findUnique({
    where: { clerkId: userId },
    select: {
      email: true,
      lastSyncedAt: true,
      lastSyncStatus: true,
      lastSyncError: true,
      backfillComplete: true,
    },
  })
  if (!row) {
    return {
      connected: false,
      email: null,
      lastSyncedAt: null,
      lastSyncStatus: null,
      lastSyncError: null,
      backfillComplete: false,
    }
  }
  return {
    connected: true,
    email: row.email,
    lastSyncedAt: row.lastSyncedAt ? row.lastSyncedAt.toISOString() : null,
    lastSyncStatus: row.lastSyncStatus,
    lastSyncError: row.lastSyncError,
    backfillComplete: row.backfillComplete,
  }
}

export async function syncGmailAction(): Promise<{
  ok: boolean
  error?: string
  created?: number
  updated?: number
  skipped?: number
}> {
  const userId = requireUser()
  try {
    return await requestGmailSync(userId)
  } catch (error) {
    console.error(error)
    return { ok: false, error: "Ingestion service is not configured" }
  }
}

export async function disconnectGmailAction(): Promise<{ ok: boolean; error?: string }> {
  const userId = requireUser()
  try {
    return await requestGmailDisconnect(userId)
  } catch (error) {
    console.error(error)
    return { ok: false, error: "Ingestion service is not configured" }
  }
}
