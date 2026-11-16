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
