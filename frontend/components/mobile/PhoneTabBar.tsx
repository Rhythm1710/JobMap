"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

function StatsIcon() {
  return (
    <svg className="h-[22px] w-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 3v18h18" />
      <path d="M7 14l4-4 3 3 5-7" />
    </svg>
  )
}

function JobsIcon() {
  return (
    <svg className="h-[22px] w-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M9 4v16" />
    </svg>
  )
}

function AddIcon() {
  return (
    <svg className="h-[22px] w-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

const TABS = [
  { href: "/stats", label: "Stats", icon: StatsIcon, active: (path: string) => path === "/stats" || path.startsWith("/stats/") },
  { href: "/jobs", label: "Jobs", icon: JobsIcon, active: (path: string) => path === "/jobs" || path.startsWith("/jobs/") },
  { href: "/add-job", label: "Add", icon: AddIcon, active: (path: string) => path === "/add-job" },
]

export function PhoneTabBar() {
  const pathname = usePathname()

  return (
    <nav
      aria-label="Primary"
      className="flex border-t border-[#E4E4E7] bg-white md:hidden"
      style={{
        paddingTop: 6,
        paddingLeft: "max(8px, env(safe-area-inset-left))",
        paddingRight: "max(8px, env(safe-area-inset-right))",
        paddingBottom: "env(safe-area-inset-bottom)",
      }}
    >
      {TABS.map((tab) => {
        const on = tab.active(pathname)
        const Icon = tab.icon
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={on ? "page" : undefined}
            className={`flex flex-1 flex-col items-center gap-[3px] pt-1 text-[10px] font-semibold tracking-[0.01em] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B] ${
              on ? "text-[#09090B]" : "text-[#71717A]"
            }`}
          >
            <span
              className={`grid h-7 w-11 place-items-center rounded-[16px] ${
                on ? "bg-[#FFF6D6] text-[#7A5A00]" : ""
              }`}
            >
              <Icon />
            </span>
            {tab.label}
          </Link>
        )
      })}
    </nav>
  )
}
