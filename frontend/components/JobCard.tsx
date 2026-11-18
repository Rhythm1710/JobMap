import { gmailThreadUrl, JobType } from '@/utils/types';
import { MapPin, Briefcase, CalendarDays, RadioTower } from 'lucide-react';

import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Separator } from './ui/separator';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import JobInfo from './JobInfo';
import DeleteJobButton from './DeleteJobButton';

function JobCard({ job }: { job: JobType }) {
  const when = job.appliedAt || job.createdAt;
  const date = new Date(when).toLocaleDateString();
  return (
    <Card className='bg-muted'>
      <CardHeader className='p-4 sm:p-6'>
        <div className='flex items-start justify-between gap-3'>
          <CardTitle className='min-w-0 break-words text-xl sm:text-2xl'>
            {job.position}
          </CardTitle>
          <Badge variant='outline' className='shrink-0 capitalize'>
            {job.source}
          </Badge>
        </div>
        <CardDescription className='break-words'>{job.company}</CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className='mt-4 grid grid-cols-1 gap-3 p-4 pt-0 sm:grid-cols-2 sm:gap-4 sm:p-6 sm:pt-0'>
        <JobInfo icon={<Briefcase />} text={job.mode} />
        <JobInfo icon={<MapPin />} text={job.location} />
        <JobInfo icon={<CalendarDays />} text={date} />
        <Badge className='w-fit max-w-full justify-center md:w-32'>
          <JobInfo icon={<RadioTower className='w-4 h-4' />} text={job.status} />
        </Badge>
      </CardContent>
      <CardFooter className='grid grid-cols-2 gap-2 p-4 pt-0 sm:flex sm:flex-wrap sm:items-center sm:gap-4 sm:p-6 sm:pt-0'>
        <Button asChild className='h-11 w-full sm:h-9 sm:w-auto'>
          <Link href={`/jobs/${job.id}`}>edit</Link>
        </Button>
        <div className='[&>button]:h-11 [&>button]:w-full sm:[&>button]:h-9 sm:[&>button]:w-auto'>
          <DeleteJobButton id={job.id} />
        </div>
        {job.gmailThreadId ? (
          <Button asChild variant='outline' className='h-11 w-full sm:h-9 sm:w-auto'>
            <a
              href={gmailThreadUrl(job.gmailThreadId)}
              target='_blank'
              rel='noreferrer'
            >
              email
            </a>
          </Button>
        ) : null}
        {job.jobUrl ? (
          <Button asChild variant='outline' className='h-11 w-full sm:h-9 sm:w-auto'>
            <a href={job.jobUrl} target='_blank' rel='noreferrer'>
              posting
            </a>
          </Button>
        ) : null}
      </CardFooter>
    </Card>
  );
}
export default JobCard;
