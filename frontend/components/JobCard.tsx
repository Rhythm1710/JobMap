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
      <CardHeader>
        <div className='flex items-start justify-between gap-3'>
          <CardTitle>{job.position}</CardTitle>
          <Badge variant='outline' className='capitalize shrink-0'>
            {job.source}
          </Badge>
        </div>
        <CardDescription>{job.company}</CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className='mt-4 grid grid-cols-2 gap-4'>
        <JobInfo icon={<Briefcase />} text={job.mode} />
        <JobInfo icon={<MapPin />} text={job.location} />
        <JobInfo icon={<CalendarDays />} text={date} />
        <Badge className='w-32 justify-center'>
          <JobInfo icon={<RadioTower className='w-4 h-4' />} text={job.status} />
        </Badge>
      </CardContent>
      <CardFooter className='flex flex-wrap gap-4'>
        <Button asChild size='sm'>
          <Link href={`/jobs/${job.id}`}>edit</Link>
        </Button>
        <DeleteJobButton id={job.id} />
        {job.gmailThreadId ? (
          <Button asChild size='sm' variant='outline'>
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
          <Button asChild size='sm' variant='outline'>
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
