import Navbar from "@/components/Navbar"
import Sidebar from "@/components/Sidebar"
import ChartsContainer from "@/components/ChartsContainer"
import StatsContainer from "@/components/StatsContainer"
import { getStatsAction } from "@/utils/actions"
import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query"

import { PropsWithChildren } from "react"

function layout({ children }: PropsWithChildren) {
  return (
    <main className="grid lg:grid-cols-5">
      <div className="hidden lg:block lg:col-span-1 lg:min-h-screen">
        <Sidebar />
      </div>
      <div className="lg:col-span-4">
        <Navbar />
        <div className="py-16 px-4 sm:px-8 lg:px-16">{children}</div>
      </div>
    </main>
  )
}
export default layout
