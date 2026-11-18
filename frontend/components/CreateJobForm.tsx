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
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <div className='pb-2.5 md:hidden'>
          <h1 className='text-[22px] font-bold leading-[1.2] tracking-[-0.03em] text-[#09090B]'>
            Add a job
          </h1>
          <p className='mt-0.5 text-[13px] leading-[1.4] text-[#71717A]'>
            Add a role you applied to.
          </p>
        </div>
        <div className='md:rounded md:bg-muted md:p-8'>
          <h2 className='mb-6 hidden text-4xl font-semibold capitalize md:block'>add job</h2>
          <div className='grid grid-cols-2 items-start gap-2 md:gap-4 lg:grid-cols-3'>
            <div className='col-span-2 md:col-span-1'>
              <CustomFormField name='position' control={form.control} labelText='Position' />
            </div>
            <CustomFormField name='company' control={form.control} labelText='Company' />
            <CustomFormField name='location' control={form.control} labelText='Location' />
            <CustomFormSelect
              name='status'
              control={form.control}
              labelText='Status'
              items={Object.values(JobStatus)}
            />
            <CustomFormSelect
              name='mode'
              control={form.control}
              labelText='Mode'
              items={Object.values(JobMode)}
            />
            <CustomFormField
              name='appliedAt'
              control={form.control}
              labelText='Applied on'
              labelClassName='!normal-case'
              type='date'
            />
            <CustomFormField
              name='jobUrl'
              control={form.control}
              labelText='Job URL'
              labelClassName='!normal-case'
              type='url'
              placeholder='https://…'
            />
            <CustomFormTextarea name='notes' control={form.control} labelText='Notes' />
            <Button
              type='submit'
              className='col-span-2 mt-1 h-11 w-full border-transparent bg-[#F8B500] text-[13px] font-semibold text-[#18181B] hover:bg-[#F8B500]/90 md:col-span-1 md:mt-0 md:h-10 md:w-auto md:self-end md:border-primary md:bg-primary md:text-primary-foreground'
              disabled={isPending}
            >
              <span className='md:hidden'>{isPending ? 'Saving...' : 'Save job'}</span>
              <span className='hidden capitalize md:inline'>{isPending ? 'loading...' : 'create job'}</span>
            </Button>
            <p className='col-span-2 text-center text-[11px] text-[#71717A] md:hidden'>
              Or connect Gmail on the Jobs screen to import applications automatically.
            </p>
          </div>
        </div>
      </form>
    </Form>
  );
}
export default CreateJobForm;
