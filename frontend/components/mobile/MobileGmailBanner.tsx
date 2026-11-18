"use client"

import { useTransition } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { syncGmailAction } from "@/utils/gmail"
import { GmailStatus } from "@/utils/types"
import { useToast } from "@/components/ui/use-toast"

function formatSynced(value: string | null): string {
  if (!value) return "Not synced yet"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not synced yet"
  const day = date.toLocaleDateString("en-GB", { day: "numeric", month: "short" })
  const time = date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
  return `Synced ${day}, ${time}`
}

function MailIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 6h16v12H4z" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  )
}

export function MobileGmailBanner({ status }: { status: GmailStatus }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [pending, startTransition] = useTransition()

  function onSync() {
    startTransition(async () => {
      const result = await syncGmailAction()
      if (!result.ok) {
        toast({ description: result.error || "Gmail sync failed" })
      } else {
        toast({
          description: `Synced. ${result.created ?? 0} new, ${result.updated ?? 0} updated.`,
        })
      }
      router.refresh()
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
      queryClient.invalidateQueries({ queryKey: ["stats"] })
      queryClient.invalidateQueries({ queryKey: ["charts"] })
    })
  }

  const subtitle = status.connected
    ? `${status.email ?? "Connected"} · ${formatSynced(status.lastSyncedAt)}`
    : "Import application mail from Gmail."

  return (
    <section className="flex items-center gap-2.5 rounded-[12px] bg-[#F4F4F5] px-3 py-2.5">
      <div className="grid h-7 w-7 shrink-0 place-items-center rounded-[8px] bg-white text-[#09090B]">
        <MailIcon />
      </div>
      <div className="min-w-0 flex-1">
        <strong className="block text-[13px] font-semibold text-[#09090B]">
          {status.connected ? "Gmail connected" : "Gmail"}
        </strong>
        <span className="mt-px block text-[11px] leading-[1.35] text-[#71717A]">{subtitle}</span>
        {status.connected && status.lastSyncStatus === "error" && status.lastSyncError ? (
          <span className="mt-px block text-[11px] text-destructive">{status.lastSyncError}</span>
        ) : null}
      </div>
      {status.connected ? (
        <button
          type="button"
          onClick={onSync}
          disabled={pending}
          className="h-8 shrink-0 rounded-[8px] border border-[#E4E4E7] bg-white px-2.5 text-[12px] font-semibold text-[#09090B] disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B]"
        >
          {pending ? "Syncing" : "Sync now"}
        </button>
      ) : (
        <a
          href="/api/gmail/connect"
          className="inline-flex h-8 shrink-0 items-center rounded-[8px] border border-[#E4E4E7] bg-white px-2.5 text-[12px] font-semibold text-[#09090B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18181B]"
        >
          Connect
        </a>
      )}
    </section>
  )
}
