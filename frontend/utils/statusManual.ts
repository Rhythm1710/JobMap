/**
 * Default status on the add-job form (`JobStatus.Applied`).
 * A string, not the TypeScript enum, so node:test can load this module.
 */
export const DEFAULT_CREATE_STATUS = "applied"

/**
 * A new job starts on `applied`. That row stays eligible for auto-ghost.
 * Any other status was chosen on create, so it is protected the same way an
 * edited status is (`updateJobAction` sets `statusManual` when the stored
 * status changes).
 */
export function statusManualOnCreate(status: string): boolean {
  return status !== DEFAULT_CREATE_STATUS
}
