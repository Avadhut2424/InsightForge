import React from 'react';
import { cn } from '../../lib/utils';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shimmer?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, shimmer = true, ...props }) => {
  return (
    <div
      className={cn(
        'rounded-md bg-zinc-200/80 dark:bg-zinc-800/80',
        shimmer && 'animate-pulse',
        className
      )}
      {...props}
    />
  );
};
