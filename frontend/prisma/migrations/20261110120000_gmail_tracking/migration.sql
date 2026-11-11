-- Extend Job for email-derived tracking and migrate the original status vocabulary.
-- pending -> applied, declined/decline -> rejected. interview is unchanged.

ALTER TABLE "Job" ADD COLUMN "source" TEXT NOT NULL DEFAULT 'manual';
ALTER TABLE "Job" ADD COLUMN "gmailMessageId" TEXT;
ALTER TABLE "Job" ADD COLUMN "gmailThreadId" TEXT;
ALTER TABLE "Job" ADD COLUMN "appliedAt" TIMESTAMP(3);
ALTER TABLE "Job" ADD COLUMN "jobUrl" TEXT;
ALTER TABLE "Job" ADD COLUMN "notes" TEXT;
ALTER TABLE "Job" ADD COLUMN "companyKey" TEXT NOT NULL DEFAULT '';
ALTER TABLE "Job" ADD COLUMN "roleKey" TEXT NOT NULL DEFAULT '';
ALTER TABLE "Job" ADD COLUMN "manuallyEdited" BOOLEAN NOT NULL DEFAULT false;

UPDATE "Job" SET "status" = 'applied' WHERE "status" IN ('pending', 'PENDING');
UPDATE "Job" SET "status" = 'rejected' WHERE "status" IN ('declined', 'decline', 'DECLINE', 'DECLINED');
UPDATE "Job" SET "status" = 'interview' WHERE "status" IN ('INTERVIEW');
UPDATE "Job" SET "appliedAt" = "createdAt" WHERE "appliedAt" IS NULL;

-- NULL gmailThreadId values stay distinct in Postgres, so existing manual rows are allowed.
CREATE UNIQUE INDEX "Job_clerkId_gmailThreadId_key" ON "Job"("clerkId", "gmailThreadId");
CREATE INDEX "Job_clerkId_companyKey_roleKey_idx" ON "Job"("clerkId", "companyKey", "roleKey");
CREATE INDEX "Job_clerkId_status_idx" ON "Job"("clerkId", "status");

CREATE TABLE "GmailConnection" (
    "id" TEXT NOT NULL,
    "clerkId" TEXT NOT NULL,
    "email" TEXT,
    "accessTokenEnc" TEXT NOT NULL,
    "refreshTokenEnc" TEXT NOT NULL,
    "tokenExpiry" TIMESTAMP(3),
    "scopes" TEXT NOT NULL DEFAULT 'https://www.googleapis.com/auth/gmail.readonly',
    "historyId" TEXT,
    "backfillBefore" TIMESTAMP(3),
    "backfillComplete" BOOLEAN NOT NULL DEFAULT false,
    "lastSyncedAt" TIMESTAMP(3),
    "lastSyncStatus" TEXT,
    "lastSyncError" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "GmailConnection_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "GmailConnection_clerkId_key" ON "GmailConnection"("clerkId");

CREATE TABLE "GmailMessage" (
    "id" TEXT NOT NULL,
    "clerkId" TEXT NOT NULL,
    "gmailMessageId" TEXT NOT NULL,
    "gmailThreadId" TEXT NOT NULL,
    "jobId" TEXT,
    "disposition" TEXT NOT NULL,
    "statusHint" TEXT,
    "subject" TEXT,
    "receivedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GmailMessage_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "GmailMessage_clerkId_gmailMessageId_key" ON "GmailMessage"("clerkId", "gmailMessageId");
CREATE INDEX "GmailMessage_clerkId_gmailThreadId_idx" ON "GmailMessage"("clerkId", "gmailThreadId");

ALTER TABLE "GmailMessage" ADD CONSTRAINT "GmailMessage_jobId_fkey"
    FOREIGN KEY ("jobId") REFERENCES "Job"("id") ON DELETE SET NULL ON UPDATE CASCADE;
