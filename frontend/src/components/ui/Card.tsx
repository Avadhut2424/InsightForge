import React from 'react';
import { cn } from '../../lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'muted' | 'subtle';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      default: 'bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs shadow-zinc-950/5',
      muted: 'bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200/60 dark:border-zinc-800/60',
      subtle: 'bg-transparent border border-zinc-200 dark:border-zinc-800',
    };

    return (
      <div
        ref={ref}
        className={cn('rounded-xl transition-all duration-150', variants[variant], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
