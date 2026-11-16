import ChartsContainer from "@/components/ChartsContainer"
import { MobileStats } from "@/components/mobile/MobileStats"
import StatsContainer from "@/components/StatsContainer"
import { getChartsDataAction, getMobileHomeAction, getStatsAction } from "@/utils/actions"
import { getGmailStatusAction } from "@/utils/gmail"
import { JobStatus } from "@/utils/types"
import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query"

async function StatsPage() {
  const queryClient = new QueryClient()
  const [stats, gmail, home] = await Promise.all([
    queryClient.fetchQuery({
      queryKey: ["stats"],
      queryFn: () => getStatsAction(),
    }),
    getGmailStatusAction(),
    getMobileHomeAction(),
  ])
  await queryClient.prefetchQuery({
    queryKey: ["charts"],
    queryFn: () => getChartsDataAction(),
  })
  const total = Object.values(JobStatus).reduce((sum, status) => sum + (stats[status] ?? 0), 0)

  return (
    <>
      <MobileStats
        counts={stats}
        total={total}
        weeks={home.weeks}
        upcoming={home.upcoming}
        gmail={gmail}
      />
      <div className="hidden md:block">
        <HydrationBoundary state={dehydrate(queryClient)}>
          <StatsContainer />
          <ChartsContainer />
        </HydrationBoundary>
      </div>
    </>
  )
}
export default StatsPage
