'use client';
import { useQuery } from '@tanstack/react-query';
import { getStatsAction } from '@/utils/actions';
import StatsCard, { StatsLoadingCard } from './StatsCard';
import { JobStatus } from '@/utils/types';

const CARDS: { key: JobStatus; title: string }[] = [
  { key: JobStatus.Applied, title: 'applied' },
  { key: JobStatus.Assessment, title: 'assessments' },
  { key: JobStatus.Interview, title: 'interviews' },
  { key: JobStatus.Offer, title: 'offers' },
  { key: JobStatus.Rejected, title: 'rejected' },
  { key: JobStatus.Ghosted, title: 'ghosted' },
  { key: JobStatus.Withdrawn, title: 'withdrawn' },
];

function StatsContainer() {
  const { data, isPending } = useQuery({
    queryKey: ['stats'],
    queryFn: () => getStatsAction(),
  });

  if (isPending)
    return (
      <div className='grid md:grid-cols-2 gap-4 lg:grid-cols-3'>
        {CARDS.map((card) => (
          <StatsLoadingCard key={card.key} />
        ))}
      </div>
    );

  return (
    <div className='grid md:grid-cols-2 gap-4 lg:grid-cols-3'>
      {CARDS.map((card) => (
        <StatsCard key={card.key} title={card.title} value={data?.[card.key] || 0} />
      ))}
    </div>
  );
}
export default StatsContainer;
