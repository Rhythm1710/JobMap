"use server"

import prisma from "./db"
import { currentUserId } from "./currentUser"
import { requestGmailDisconnect, requestGmailSync } from "./ingestion"
import { GmailStatus } from "./types"

function requireUser(): Promise<string> {
  return currentUserId()
}

export async function getGmailStatusAction(): Promise<GmailStatus> {
  const userId = await requireUser()
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
  const userId = await requireUser()
  try {
    return await requestGmailSync(userId)
  } catch (error) {
    console.error(error)
    return { ok: false, error: "Ingestion service is not configured" }
  }
}

export async function disconnectGmailAction(): Promise<{ ok: boolean; error?: string }> {
  const userId = await requireUser()
  try {
    return await requestGmailDisconnect(userId)
  } catch (error) {
    console.error(error)
    return { ok: false, error: "Ingestion service is not configured" }
  }
}
