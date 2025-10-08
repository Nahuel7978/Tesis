// src/features/jobs/components/JobCard.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Job, JobState } from '@/types/TypeIndex';

interface JobCardProps {
  job: Job;
}

const getStateConfig = (state: JobState) => {
  switch (state) {
    case JobState.WAIT:
      return {
        label: 'En Espera',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-700',
        icon: '⏳'
      };
    case JobState.RUNNING:
      return {
        label: 'En Ejecución',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '▶'
      };
    case JobState.READY:
      return {
        label: 'Completado',
        bgColor: 'bg-green-100',
        textColor: 'text-green-700',
        icon: '✓'
      };
    case JobState.ERROR:
      return {
        label: 'Error',
        bgColor: 'bg-red-100',
        textColor: 'text-red-700',
        icon: '✕'
      };
    case JobState.TERMINATED:
      return {
        label: 'Terminado',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-700',
        icon: '⊗'
      };
    default:
      return {
        label: 'Desconocido',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-700',
        icon: '?'
      };
  }
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const day = date.getDate().toString().padStart(2, '0');
  const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const month = months[date.getMonth()];
  const year = date.getFullYear();
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  
  return `${day} ${month} ${year}, ${hours}:${minutes}`;
};

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const navigate = useNavigate();
  const stateConfig = getStateConfig(job.state);

  const handleClick = () => {
    navigate(`/train/${job.id}`);
  };

  return (
    <div 
      onClick={handleClick}
      className="bg-white rounded-lg p-5 shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 hover:border-gray-300"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {job.worldName}
            </h3>
            <span className={`${stateConfig.bgColor} ${stateConfig.textColor} px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5`}>
              <span>{stateConfig.icon}</span>
              {stateConfig.label}
            </span>
          </div>
          
          <div className="flex items-center gap-6 mt-2 text-sm text-gray-600">
            <div className="flex items-center gap-1.5">
              <span>Iniciado: {formatDate(job.createdAt)}</span>
            </div>
            
            <span>•</span>
            
            <div className="flex items-center gap-1.5">
              <span>Algoritmo: <span className="uppercase font-medium">{job.hyperparameters.model}</span></span>
            </div>
            
            <span>•</span>
            
            <div className="flex items-center gap-1.5">
              <span>Entorno: <span className="font-medium">{job.hyperparameters.def_robot}</span></span>
            </div>
          </div>
        </div>
        
        <div className="text-gray-400 text-2xl ml-4">
          →
        </div>
      </div>
    </div>
  );
};