import React from 'react';
import { CheckCircle, XCircle, Clock, Play, Ban } from 'lucide-react';
import type { RunStatus } from '@/types';

interface StatusBadgeProps {
  status: RunStatus | string;
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const styles = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };

  const icons = {
    pending: Clock,
    running: Play,
    completed: CheckCircle,
    failed: XCircle,
    cancelled: Ban,
  };

  const Icon = icons[status as RunStatus] || Clock;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as RunStatus] || styles.pending} ${className}`}
    >
      <Icon className="h-3 w-3 mr-1" />
      {status}
    </span>
  );
};

export default StatusBadge;
