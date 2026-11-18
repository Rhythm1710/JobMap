import EditJobForm from "@/components/EditJobForm"
import { MobileJobDetail } from "@/components/mobile/MobileJobDetail"
import { getSingleJobAction } from "@/utils/actions"

import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query"

async function JobDetailPage({ params }: { params: { id: string } }) {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ["job", params.id],
    queryFn: () => getSingleJobAction(params.id),
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <MobileJobDetail jobId={params.id} />
      <div className="hidden md:block">
        <EditJobForm jobId={params.id} />
      </div>
    </HydrationBoundary>
  )
}
export default JobDetailPage
