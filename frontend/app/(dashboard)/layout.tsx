import Navbar from "@/components/Navbar"
import Sidebar, { PhoneTabBar } from "@/components/Sidebar"

import { PropsWithChildren } from "react"

export const dynamic = "force-dynamic"

function layout({ children }: PropsWithChildren) {
  return (
    <>
      <main className="grid lg:grid-cols-5">
        <div className="hidden lg:block lg:col-span-1 lg:min-h-screen">
          <Sidebar />
        </div>
        <div className="lg:col-span-4">
          <Navbar />
          <div className="px-3 py-4 pb-24 sm:px-8 sm:py-16 lg:px-16">{children}</div>
        </div>
      </main>
      <PhoneTabBar />
    </>
  )
}
export default layout
