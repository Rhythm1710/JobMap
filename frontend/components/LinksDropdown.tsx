import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { AlignLeft } from 'lucide-react';
import { Button } from './ui/button';
import links from '@/utils/links';
import Link from 'next/link';

function DropdownLinks() {
  return (
    <div className='hidden sm:block lg:hidden'>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant='outline' size='icon' className='h-11 w-11'>
            <AlignLeft />
            <span className='sr-only'>Toggle links</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className='w-52 lg:hidden'
          align='start'
          sideOffset={25}
        >
          {links.map((link) => {
            return (
              <DropdownMenuItem key={link.href}>
                <Link href={link.href} className='flex items-center gap-x-2 '>
                  {link.icon} <span className='capitalize'>{link.label}</span>
                </Link>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
export default DropdownLinks;
