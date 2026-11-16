import { GmailStatus, JobStatus } from "@/utils/types"
import { MobileUpcoming, MobileWeek } from "@/utils/mobileHome"
import { MobileGmailBanner } from "./MobileGmailBanner"
import { StatusPill } from "./StatusPill"
import { WeekChart } from "./WeekChart"

const TILES: { key: JobStatus; label: string; tile: string; number: string }[] = [
  { key: JobStatus.Applied, label: "applied", tile: "bg-[#F4F4F5]", number: "text-[#09090B]" },
  { key: JobStatus.Assessment, label: "assessments", tile: "bg-[#F4F4F5]", number: "text-[#09090B]" },
  { key: JobStatus.Interview, label: "interviews", tile: "bg-[#FFF6D6]", number: "text-[#7A5A00]" },
  { key: JobStatus.Offer, label: "offers", tile: "bg-[#ECF8EF]", number: "text-[#157A3A]" },
  { key: JobStatus.Rejected, label: "rejected", tile: "bg-[#F4F4F5]", number: "text-[#B91C1C]" },
  { key: JobStatus.Ghosted, label: "ghosted", tile: "bg-[#F4F4F5]", number: "text-[#09090B]" },
]

export function MobilePageTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="pb-2.5">
      <h1 className="text-[22px] font-bold leading-[1.2] tracking-[-0.03em] text-[#09090B]">
        {title}
      </h1>
      {subtitle ? (
        <p className="mt-0.5 text-[13px] leading-[1.4] text-[#71717A]">{subtitle}</p>
      ) : null}
    </div>
  )
}

export function MobileStats({
  counts,
  total,
  weeks,
  upcoming,
  gmail,
}: {
  counts: Record<JobStatus, number>
  total: number
  weeks: MobileWeek[]
  upcoming: MobileUpcoming[]
  gmail: GmailStatus
}) {
  return (
    <div className="md:hidden">
      <MobilePageTitle title="Your pipeline" subtitle={`${total} applications`} />
      <div className="flex flex-col gap-3">
        <MobileGmailBanner status={gmail} />
        <div className="grid grid-cols-3 gap-2">
          {TILES.map((tile) => (
            <div key={tile.key} className={`rounded-[12px] px-2.5 pb-[11px] pt-2.5 ${tile.tile}`}>
              <div className={`text-[22px] font-bold leading-none tracking-[-0.04em] ${tile.number}`}>
                {counts[tile.key] ?? 0}
              </div>
              <div className="mt-1 text-[11px] font-medium capitalize text-[#71717A]">{tile.label}</div>
            </div>
          ))}
        </div>
        <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 py-3">
          <div className="mb-2.5 flex items-baseline justify-between">
            <h2 className="text-[13px] font-semibold text-[#09090B]">Applications by week</h2>
            <span className="text-[11px] text-[#71717A]">Last 6 weeks</span>
          </div>
          <WeekChart weeks={weeks} />
        </section>
        <section className="rounded-[12px] border border-[#E4E4E7] bg-white px-3.5 py-3">
          <div className="mb-2.5 flex items-baseline justify-between">
            <h2 className="text-[13px] font-semibold text-[#09090B]">Coming up</h2>
            <span className="text-[11px] text-[#71717A]">
              {upcoming.length === 0 ? "None" : `${upcoming.length} open`}
            </span>
          </div>
          {upcoming.length === 0 ? (
            <p className="text-[12px] text-[#71717A]">Nothing scheduled from interview, assessment, or offer.</p>
          ) : (
            upcoming.map((item, index) => (
              <div
                key={item.id}
                className={`flex items-start gap-2.5 ${index === 0 ? "pt-0" : "border-t border-[#E4E4E7] py-[7px]"} ${index > 0 ? "" : ""}`}
              >
                <div
                  className={`grid h-9 w-9 shrink-0 place-items-center rounded-[10px] text-[12px] font-bold tracking-[-0.02em] ${
                    item.gold ? "bg-[#F8B500] text-[#18181B]" : "bg-[#18181B] text-white"
                  }`}
                >
                  {item.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-[13px] font-semibold text-[#09090B]">{item.title}</h3>
                  <p className="mt-px text-[12px] leading-[1.35] text-[#71717A]">{item.body}</p>
                </div>
                <span className="mt-px">
                  <StatusPill status={item.status} />
                </span>
              </div>
            ))
          )}
        </section>
      </div>
    </div>
  )
}
