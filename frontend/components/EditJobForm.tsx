'use client';

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';

import {
  JobStatus,
  JobMode,
  createAndEditJobSchema,
  CreateAndEditJobType,
  emptyJobForm,
  gmailThreadUrl,
  JobType,
} from '@/utils/types';

import { Button } from '@/components/ui/button';
import { Form } from '@/components/ui/form';
import { Badge } from '@/components/ui/badge';

import {
  CustomFormField,
  CustomFormSelect,
  CustomFormTextarea,
} from './FormComponents';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { getSingleJobAction, updateJobAction } from '@/utils/actions';
import { useToast } from '@/components/ui/use-toast';
import { useRouter } from 'next/navigation';

function dateInputValue(value: Date | string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
}

function toFormValues(job: JobType): CreateAndEditJobType {
  const applied = dateInputValue(job.appliedAt);
  return {
    position: job.position || '',
    company: job.company || '',
    location: job.location || '',
    status: (Object.values(JobStatus) as string[]).includes(job.status)
      ? (job.status as JobStatus)
      : JobStatus.Applied,
    mode: (Object.values(JobMode) as string[]).includes(job.mode)
      ? (job.mode as JobMode)
      : JobMode.FullTime,
    jobUrl: job.jobUrl || '',
    notes: job.notes || '',
    appliedAt: applied,
  };
}

function EditJobForm({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const router = useRouter();

  const { data } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getSingleJobAction(jobId),
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (values: CreateAndEditJobType) => updateJobAction(jobId, values),
    onSuccess: (updated) => {
      if (!updated) {
        toast({
          description: 'there was an error',
        });
        return;
      }
      toast({ description: 'job updated' });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['job', jobId] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['charts'] });
      router.push('/jobs');
    },
  });

  const form = useForm<CreateAndEditJobType>({
    resolver: zodResolver(createAndEditJobSchema),
    defaultValues: data ? toFormValues(data) : emptyJobForm(),
  });

  useEffect(() => {
    if (data) {
      form.reset(toFormValues(data));
    }
  }, [data, form]);

  function onSubmit(values: CreateAndEditJobType) {
    mutate(values);
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className='bg-muted p-8 rounded'
      >
        <div className='flex flex-wrap items-center gap-3 mb-6'>
          <h2 className='capitalize font-semibold text-4xl'>edit job</h2>
          {data?.source ? (
            <Badge variant='outline' className='capitalize'>
              {data.source}
            </Badge>
          ) : null}
        </div>
        {data?.gmailThreadId ? (
          <p className='mb-6 text-sm'>
            <a
              className='underline'
              href={gmailThreadUrl(data.gmailThreadId)}
              target='_blank'
              rel='noreferrer'
            >
              Open the Gmail thread
            </a>
          </p>
        ) : null}
        <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-3 items-start'>
          <CustomFormField name='position' control={form.control} />
          <CustomFormField name='company' control={form.control} />
          <CustomFormField name='location' control={form.control} />
          <CustomFormSelect
            name='status'
            control={form.control}
            labelText='job status'
            items={Object.values(JobStatus)}
          />
          <CustomFormSelect
            name='mode'
            control={form.control}
            labelText='job mode'
            items={Object.values(JobMode)}
          />
          <CustomFormField
            name='appliedAt'
            control={form.control}
            labelText='applied date'
            type='date'
          />
          <CustomFormField
            name='jobUrl'
            control={form.control}
            labelText='job url'
            type='url'
          />
          <CustomFormTextarea
            name='notes'
            control={form.control}
            labelText='notes'
          />
          <Button
            type='submit'
            className='self-end capitalize'
            disabled={isPending}
          >
            {isPending ? 'updating...' : 'edit job'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
export default EditJobForm;
