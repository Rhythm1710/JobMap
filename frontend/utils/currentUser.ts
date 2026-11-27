import { auth } from "@/auth"
import { redirect } from "next/navigation"
import prisma from "./db"
import { legacyClerkIdToAdopt } from "./identity"

const adopted = new Set<string>()

async function adoptLegacyClerkRows(userId: string, email: string): Promise<void> {
  const rows = await prisma.gmailConnection.findMany({
    where: { email: { equals: email.trim(), mode: "insensitive" } },
    select: { clerkId: true, email: true },
  })
  const oldId = legacyClerkIdToAdopt(rows, email, userId)
  if (!oldId) return
  await prisma.$transaction([
    prisma.job.updateMany({ where: { clerkId: oldId }, data: { clerkId: userId } }),
    prisma.gmailMessage.updateMany({ where: { clerkId: oldId }, data: { clerkId: userId } }),
    prisma.gmailConnection.update({ where: { clerkId: oldId }, data: { clerkId: userId } }),
  ])
}

/** Signed-in Auth.js user id (Google `sub`). Redirects home when there is no session. */
export async function currentUserId(): Promise<string> {
  const session = await auth()
  const userId = session?.user?.id
  if (!userId) redirect("/")

  const email = session.user.email
  if (email && !adopted.has(userId)) {
    try {
      await adoptLegacyClerkRows(userId, email)
      adopted.add(userId)
    } catch (error) {
      console.error(error)
    }
  }
  return userId
}
