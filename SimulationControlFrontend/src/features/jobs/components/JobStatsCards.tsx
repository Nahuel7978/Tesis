// src/features/jobs/components/JobStatsCards.tsx
import React from 'react';
import { Job, JobState } from '@/types/TypeIndex';

interface JobStatsCardsProps {
  jobs: Job[];
}

export const JobStatsCards: React.FC<JobStatsCardsProps> = ({ jobs }) => {
  const stats = {
    total: jobs.length,
    running: jobs.filter(j => j.state === JobState.RUNNING).length,
    completed: jobs.filter(j => j.state === JobState.READY).length,
    errors: jobs.filter(j => j.state === JobState.ERROR).length,
  };

  const cards = [
    {
      label: 'Total Jobs',
      value: stats.total,
      icon: '📝',
      bgColor: 'bg-blue-50',
      iconBg: 'bg-blue-100',
      textColor: 'text-blue-600'
    },
    {
      label: 'En Ejecución',
      value: stats.running,
      icon: '▶',
      bgColor: 'bg-blue-50',
      iconBg: 'bg-blue-400',
      textColor: 'text-blue-700'
    },
    {
      label: 'Completados',
      value: stats.completed,
      icon: '✓',
      bgColor: 'bg-green-50',
      iconBg: 'bg-green-400',
      textColor: 'text-green-700'
    },
    {
      label: 'Con Errores',
      value: stats.errors,
      icon: '⚠',
      bgColor: 'bg-red-50',
      iconBg: 'bg-red-400',
      textColor: 'text-red-700'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <div 
          key={index}
          className={`${card.bgColor} rounded-lg p-6 flex items-center justify-between`}
        >
          <div>
            <p className="text-sm text-gray-600 mb-1">{card.label}</p>
            <p className={`text-3xl font-bold ${card.textColor}`}>
              {card.value}
            </p>
          </div>
          <div className={`${card.iconBg} w-10 h-10 rounded-lg flex items-center justify-center text-white text-xl`}>
            {card.icon}
          </div>
        </div>
      ))}
    </div>
  );
};