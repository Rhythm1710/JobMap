import { Control } from 'react-hook-form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';

type CustomFormFieldProps = {
  name: string;
  control: Control<any>;
  labelText?: string;
  labelClassName?: string;
  type?: string;
  placeholder?: string;
};

export function CustomFormField({
  name,
  control,
  labelText,
  labelClassName,
  type = 'text',
  placeholder,
}: CustomFormFieldProps) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className='min-w-0 gap-1.5'>
          <FormLabel className={`capitalize text-[12px] font-semibold text-[#09090B] md:text-sm md:font-medium ${labelClassName ?? ''}`}>
            {labelText || name}
          </FormLabel>
          <FormControl>
            <Input
              type={type}
              placeholder={placeholder}
              className='h-[42px] min-w-0 rounded-[10px] border-[#E4E4E7] px-3 text-[14px] placeholder:text-[#A1A1AA] md:h-10 md:rounded-md'
              {...field}
              value={field.value ?? ''}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

type CustomFormTextareaProps = {
  name: string;
  control: Control<any>;
  labelText?: string;
};

export function CustomFormTextarea({
  name,
  control,
  labelText,
}: CustomFormTextareaProps) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className='col-span-2 min-w-0 gap-1.5 lg:col-span-3'>
          <FormLabel className='text-[12px] font-semibold capitalize text-[#09090B] md:text-sm md:font-medium'>
            {labelText || name}
          </FormLabel>
          <FormControl>
            <Textarea
              className='h-[72px] min-h-0 min-w-0 rounded-[10px] border-[#E4E4E7] px-3 py-2.5 text-[14px] md:h-auto md:min-h-[96px] md:rounded-md'
              {...field}
              value={field.value ?? ''}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

type CustomFormSelectProps = {
  name: string;
  control: Control<any>;
  items: string[];
  labelText?: string;
};

export function CustomFormSelect({
  name,
  control,
  items,
  labelText,
}: CustomFormSelectProps) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className='min-w-0 gap-1.5'>
          <FormLabel className='text-[12px] font-semibold capitalize text-[#09090B] md:text-sm md:font-medium'>
            {labelText || name}
          </FormLabel>
          <Select onValueChange={field.onChange} value={field.value}>
            <FormControl>
              <SelectTrigger className='h-[42px] rounded-[10px] border-[#E4E4E7] text-[14px] md:h-10 md:rounded-md'>
                <SelectValue />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {items.map((item) => {
                return (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          <FormMessage />
        </FormItem>
      )}
    />
  );
}
export default CustomFormSelect;
