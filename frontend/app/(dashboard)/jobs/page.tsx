import { Suspense } from "react"
import JobsList from "@/components/JobsList"
import SearchForm from "@/components/SearchForm"
import GmailSyncPanel from "@/components/GmailSyncPanel"
import { MobileJobs } from "@/components/mobile/MobileJobs"
import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query"
import { getAllJobsAction, getJobFacetsAction } from "@/utils/actions"
import { getGmailStatusAction } from "@/utils/gmail"

export const dynamic = "force-dynamic"

async function AllJobsPage() {
  const queryClient = new QueryClient()

  const [, gmailStatus, facets] = await Promise.all([
    queryClient.prefetchQuery({
      queryKey: ["jobs", "", "all", "all", 1],
      queryFn: () => getAllJobsAction({}),
    }),
    getGmailStatusAction(),
    getJobFacetsAction(),
  ])
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Suspense fallback={<h2 className="text-xl">Please wait...</h2>}>
        <MobileJobs facets={facets} />
        <div className="hidden md:block">
          <GmailSyncPanel status={gmailStatus} />
          <SearchForm />
          <JobsList />
        </div>
      </Suspense>
    </HydrationBoundary>
  )
}

export default AllJobsPage
