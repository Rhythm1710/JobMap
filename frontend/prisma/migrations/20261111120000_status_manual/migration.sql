-- The owner can lock a status against automatic ghosting.
-- Existing hand-entered rows were given their status by the owner.

ALTER TABLE "Job" ADD COLUMN "statusManual" BOOLEAN NOT NULL DEFAULT false;

UPDATE "Job" SET "statusManual" = true WHERE "source" = 'manual';
