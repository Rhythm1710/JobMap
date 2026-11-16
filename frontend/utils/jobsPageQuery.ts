type QueryReader = {
  get(name: string): string | null
}

/** Preserve the jobs filters, including jobSource, when the page changes. */
export function jobsListPageQuery(current: QueryReader, page: number): string {
  const params = new URLSearchParams({
    search: current.get("search") || "",
    jobStatus: current.get("jobStatus") || "",
    jobSource: current.get("jobSource") || "",
    page: String(page),
  })
  return params.toString()
}

/** One chip is on at a time. Search text stays. */
export function jobsFilterQuery(
  search: string,
  jobStatus: string,
  jobSource: string,
): string {
  const params = new URLSearchParams()
  if (search) params.set("search", search)
  if (jobStatus && jobStatus !== "all") params.set("jobStatus", jobStatus)
  if (jobSource && jobSource !== "all") params.set("jobSource", jobSource)
  return params.toString()
}
