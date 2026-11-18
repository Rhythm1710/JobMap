"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Mark } from "./Mark"

function BackChevron() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m15 18-6-6 6-6" />
    </svg>
  )
}

export function MobileHeader({ path }: { path?: string }) {
  const pathname = usePathname()
  const current = path ?? pathname
  const detail = current.startsWith("/jobs/")

  return (
    <header
      className="flex items-center gap-2.5 md:hidden"
      style={{
        paddingTop: "calc(6px + env(safe-area-inset-top))",
        paddingRight: "max(16px, env(safe-area-inset-right))",
        paddingBottom: 10,
        paddingLeft: "max(16px, env(safe-area-inset-left))",
      }}
    >
      {detail ? (
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1 text-[15px] font-medium text-[#09090B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B]"
        >
          <BackChevron />
          Jobs
        </Link>
      ) : (
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <Mark />
          <div className="text-[17px] font-bold tracking-[-0.03em] text-[#09090B]">
            JobMap
          </div>
        </div>
      )}
    </header>
  )
}
