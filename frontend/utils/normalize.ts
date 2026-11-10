// Keep this list identical to backend/app/jobs/normalize.py.
const DROP = new Set([
  "inc",
  "llc",
  "ltd",
  "corp",
  "co",
  "company",
  "incorporated",
  "limited",
  "plc",
])

export function normalizeKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token && !DROP.has(token))
    .join(" ")
}

export function normalizeRole(value: string): string {
  return normalizeKey(value)
    .replace(/\b(role|position|opening|opportunity)\b/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .join(" ")
}
