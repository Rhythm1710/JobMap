const PILL: Record<string, string> = {
  applied: "bg-[#F4F4F5] text-[#3F3F46]",
  assessment: "bg-[#EEF4FF] text-[#1D4ED8]",
  interview: "bg-[#FFF6D6] text-[#7A5A00]",
  offer: "bg-[#ECF8EF] text-[#157A3A]",
  rejected: "bg-[#FEF2F2] text-[#B91C1C]",
  ghosted: "bg-[#F5F0EB] text-[#9A3412]",
  withdrawn: "bg-[#F4F4F5] text-[#71717A]",
}

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex h-[22px] shrink-0 items-center rounded-full px-2 text-[11px] font-semibold capitalize ${
        PILL[status] ?? "bg-[#F4F4F5] text-[#3F3F46]"
      }`}
    >
      {status}
    </span>
  )
}

export function SourcePill({ source }: { source: string }) {
  return (
    <span className="inline-flex h-[22px] items-center rounded-full bg-[#F4F4F5] px-2 text-[11px] font-semibold text-[#71717A]">
      {source}
    </span>
  )
}
