import { Suspense } from "react"
import JobsList from "@/components/JobsList"
import SearchForm from "@/components/SearchForm"
import GmailSyncPanel from "@/components/GmailSyncPanel"
import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query"
import { getAllJobsAction } from "@/utils/actions"
import { getGmailStatusAction } from "@/utils/gmail"

export const dynamic = "force-dynamic"

async function AllJobsPage() {
  const queryClient = new QueryClient()

  const [, gmailStatus] = await Promise.all([
    queryClient.prefetchQuery({
      queryKey: ["jobs", "", "all", "all", 1],
      queryFn: () => getAllJobsAction({}),
    }),
    getGmailStatusAction(),
  ])
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Suspense fallback={<h2 className="text-xl">Please wait...</h2>}>
        <GmailSyncPanel status={gmailStatus} />
        <SearchForm />
        <JobsList />
      </Suspense>
    </HydrationBoundary>
  )
}

export default AllJobsPage
