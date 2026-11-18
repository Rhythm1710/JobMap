'use client';

import { useTransition } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Mail } from 'lucide-react';
import { Button } from './ui/button';
import { disconnectGmailAction, syncGmailAction } from '@/utils/gmail';
import { GmailStatus } from '@/utils/types';
import { useToast } from '@/components/ui/use-toast';

const NOTICES: Record<string, string> = {
  connected: 'Gmail connected. Run Sync now to import applications.',
  denied: 'Gmail access was not granted.',
  cookie:
    'Gmail connect could not be verified because this browser did not start it. Use Connect Gmail again in this browser.',
  mismatch:
    'Gmail connect did not match this browser session. Use Connect Gmail again in this browser.',
  error: 'Gmail connect failed. Check the ingestion service and the OAuth redirect URI.',
};

function formatSynced(value: string | null): string {
  if (!value) return 'Never synced';
  return `Last synced ${new Date(value).toLocaleString()}`;
}

function GmailSyncPanel({ status }: { status: GmailStatus }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [pending, startTransition] = useTransition();
  const notice = NOTICES[searchParams.get('gmail') || ''];

  function refreshJobs() {
    router.refresh();
    queryClient.invalidateQueries({ queryKey: ['jobs'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
    queryClient.invalidateQueries({ queryKey: ['charts'] });
  }

  function onSync() {
    startTransition(async () => {
      const result = await syncGmailAction();
      if (!result.ok) {
        toast({ description: result.error || 'Gmail sync failed' });
        refreshJobs();
        return;
      }
      toast({
        description: `Synced. ${result.created ?? 0} new, ${result.updated ?? 0} updated.`,
      });
      refreshJobs();
    });
  }

  function onDisconnect() {
    startTransition(async () => {
      const result = await disconnectGmailAction();
      if (!result.ok) {
        toast({ description: result.error || 'Could not disconnect Gmail' });
        return;
      }
      toast({ description: 'Gmail disconnected' });
      refreshJobs();
    });
  }

  return (
    <section className='mb-6 flex flex-col gap-4 rounded-lg bg-muted p-4 sm:mb-8 sm:p-6 lg:flex-row lg:items-center lg:justify-between'>
      <div className='space-y-1'>
        <h2 className='font-semibold flex items-center gap-2'>
          <Mail className='h-4 w-4' aria-hidden='true' />
          Gmail
        </h2>
        {status.connected ? (
          <>
            <p className='text-sm text-muted-foreground'>
              Connected{status.email ? ` as ${status.email}` : ''}. {formatSynced(status.lastSyncedAt)}
            </p>
            {status.lastSyncStatus === 'error' && status.lastSyncError ? (
              <p className='text-sm text-destructive'>{status.lastSyncError}</p>
            ) : null}
            {status.connected && !status.backfillComplete ? (
              <p className='text-sm text-muted-foreground'>
                Older mail is still importing. Sync again to continue.
              </p>
            ) : null}
          </>
        ) : (
          <p className='text-sm text-muted-foreground'>
            Connect Gmail to import application, assessment, interview, rejection, and offer emails.
          </p>
        )}
        {notice ? <p className='text-sm'>{notice}</p> : null}
      </div>
      <div className='flex flex-col gap-2 sm:flex-row sm:flex-wrap'>
        {status.connected ? (
          <>
            <Button
              type='button'
              className='h-11 w-full sm:h-10 sm:w-auto'
              onClick={onSync}
              disabled={pending}
            >
              {pending ? 'Working...' : 'Sync now'}
            </Button>
            <Button
              type='button'
              variant='outline'
              className='h-11 w-full sm:h-10 sm:w-auto'
              onClick={onDisconnect}
              disabled={pending}
            >
              Disconnect
            </Button>
          </>
        ) : (
          <Button asChild className='h-11 w-full sm:h-10 sm:w-auto'>
            <a href='/api/gmail/connect'>Connect Gmail</a>
          </Button>
        )}
      </div>
    </section>
  );
}

export default GmailSyncPanel;
