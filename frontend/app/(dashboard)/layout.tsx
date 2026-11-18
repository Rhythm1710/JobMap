import Navbar from "@/components/Navbar"
import Sidebar from "@/components/Sidebar"
import { MobileHeader } from "@/components/mobile/MobileHeader"
import { PhoneTabBar } from "@/components/mobile/PhoneTabBar"

import { PropsWithChildren } from "react"

export const dynamic = "force-dynamic"

function layout({ children }: PropsWithChildren) {
  return (
    <main className="md:grid lg:grid-cols-5">
      <div className="hidden lg:block lg:col-span-1 lg:min-h-screen">
        <Sidebar />
      </div>
      <div className="flex min-h-dvh flex-col md:block md:min-h-0 lg:col-span-4">
        <MobileHeader />
        <div className="hidden md:block">
          <Navbar />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto pb-2.5 pl-[max(16px,env(safe-area-inset-left))] pr-[max(16px,env(safe-area-inset-right))] md:overflow-visible md:px-8 md:py-16 lg:px-16">
          {children}
        </div>
        <PhoneTabBar />
      </div>
    </main>
  )
}
export default layout
