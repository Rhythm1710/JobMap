/**
 * The Auth.js user id is the Google account subject (`sub`).
 * `account.providerAccountId` is that subject. Without this, Auth.js mints a
 * new random user id on every sign-in when no database adapter is configured.
 */
export function stableUserId(input: {
  providerAccountId?: string | null
  profileSub?: string | null
}): string | null {
  const fromAccount = input.providerAccountId?.trim()
  if (fromAccount) return fromAccount
  const fromProfile = input.profileSub?.trim()
  if (fromProfile) return fromProfile
  return null
}

/** Clerk user ids look like `user_2abc...`. Google subjects are numeric. */
export function isClerkUserId(id: string): boolean {
  return /^user_[A-Za-z0-9]+$/.test(id)
}

/**
 * If the signed-in Google email matches exactly one Gmail connection that is
 * still keyed by a Clerk id, that id should be rewritten to the Google subject.
 * Any other shape is left untouched so two accounts are never merged.
 */
export function legacyClerkIdToAdopt(
  connections: ReadonlyArray<{ clerkId: string; email: string | null }>,
  email: string,
  userId: string,
): string | null {
  const normalized = email.trim().toLowerCase()
  if (!normalized || !userId || isClerkUserId(userId)) return null
  const matches = connections.filter((row) => {
    const rowEmail = row.email?.trim().toLowerCase()
    return rowEmail === normalized && isClerkUserId(row.clerkId) && row.clerkId !== userId
  })
  if (matches.length !== 1) return null
  return matches[0].clerkId
}
