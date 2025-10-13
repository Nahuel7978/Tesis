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
    case JobState.CANCELLED:
      return {
        label: 'Cancelado',
        color: 'bg-gray-100 text-gray-800 border-gray-300',
        icon: '⏹️',
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
    navigate(`/trainPage/${job.id}`);
  };

  return (
    <div 
      onClick={handleClick}
      className="bg-white rounded-lg p-5 shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 hover:border-gray-300"
    >
          
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between">
      <div className="flex-1 w-full"> {/* Añadir w-full para ocupar todo el ancho disponible */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mb-2 sm:mb-0"> {/* Ajustes para el título y el estado */}
          <h3 className="text-lg font-semibold text-gray-900">
            {job.worldName}
          </h3>
          <span className={`${stateConfig.bgColor} ${stateConfig.textColor} px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 self-start sm:self-auto`}> {/* self-start para alinear en móvil */}
            <span>{stateConfig.icon}</span>
            {stateConfig.label}
          </span>
        </div>

        {/* Información adicional: reorganizar para que se apile en pantallas pequeñas */}
        <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-6 mt-2 text-sm text-gray-600">
          <div className="flex items-center gap-1.5">
            <span>Iniciado: {formatDate(job.createdAt)}</span>
          </div>

          {/* El separador solo se muestra en pantallas medianas y más grandes */}
          <span className="hidden md:block">•</span>

          <div className="flex items-center gap-1.5">
            <span>Algoritmo: <span className="uppercase font-medium">{job.hyperparameters.model}</span></span>
          </div>

          <span className="hidden md:block">•</span>

          <div className="flex items-center gap-1.5">
            <span>Entorno: <span className="font-medium">{job.hyperparameters.def_robot}</span></span>
          </div>
        </div>
      </div>

      <div className="text-gray-400 text-2xl mt-4 sm:mt-0 sm:ml-4 self-end sm:self-auto"> {/* Ajuste para el icono de flecha */}
        →
      </div>
    </div>

      
  </div>
  );
};