'use client';
import { Input } from './ui/input';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Button } from './ui/button';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { JobSource, JobStatus } from '@/utils/types';

function SearchContainer() {
  const searchParams = useSearchParams();
  const search = searchParams.get('search') || '';
  const jobStatus = searchParams.get('jobStatus') || 'all';
  const jobSource = searchParams.get('jobSource') || 'all';
  const router = useRouter();
  const pathname = usePathname();
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const params = new URLSearchParams();

    const formData = new FormData(e.currentTarget);
    const searchValue = formData.get('search') as string;
    const statusValue = formData.get('jobStatus') as string;
    const sourceValue = formData.get('jobSource') as string;
    params.set('search', searchValue);
    params.set('jobStatus', statusValue);
    params.set('jobSource', sourceValue);

    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <form
      className='bg-muted mb-16 p-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 rounded-lg'
      onSubmit={handleSubmit}
    >
      <Input
        type='text'
        placeholder='Search Jobs'
        name='search'
        aria-label='Search jobs'
        defaultValue={search}
      />
      <Select defaultValue={jobStatus} name='jobStatus'>
        <SelectTrigger aria-label='Filter by status'>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {['all', ...Object.values(JobStatus)].map((status) => {
            return (
              <SelectItem key={status} value={status}>
                {status}
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
      <Select defaultValue={jobSource} name='jobSource'>
        <SelectTrigger aria-label='Filter by source'>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {['all', ...Object.values(JobSource)].map((source) => {
            return (
              <SelectItem key={source} value={source}>
                {source}
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
      <Button type='submit'>Search</Button>
    </form>
  );
}
export default SearchContainer;
