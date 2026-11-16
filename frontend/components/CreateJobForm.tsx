'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';

import {
  JobStatus,
  JobMode,
  createAndEditJobSchema,
  CreateAndEditJobType,
  emptyJobForm,
} from '@/utils/types';

import { Form } from '@/components/ui/form';
import { Button } from './ui/button';
import {
  CustomFormField,
  CustomFormSelect,
  CustomFormTextarea,
} from './FormComponents';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createJobAction } from '@/utils/actions';
import { useToast } from '@/components/ui/use-toast';
import { useRouter } from 'next/navigation';

function CreateJobForm() {
  const form = useForm<CreateAndEditJobType>({
    resolver: zodResolver(createAndEditJobSchema),
    defaultValues: emptyJobForm(),
  });
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const router = useRouter();
  const { mutate, isPending } = useMutation({
    mutationFn: (values: CreateAndEditJobType) => createJobAction(values),
    onSuccess: (data) => {
      if (!data) {
        toast({
          description: 'there was an error',
        });
        return;
      }
      toast({ description: 'job created' });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['charts'] });

      router.push('/jobs');
    },
  });

  function onSubmit(values: CreateAndEditJobType) {
    mutate(values);
  }
  return (
    <Form {...form}>
      <form
        className='rounded bg-muted p-4 sm:p-8'
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <h2 className='mb-6 text-2xl font-semibold capitalize sm:text-4xl'>add job</h2>
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
            className='h-11 w-full self-end capitalize sm:h-10 sm:w-auto'
            disabled={isPending}
          >
            {isPending ? 'loading...' : 'create job'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
export default CreateJobForm;
