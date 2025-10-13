import { JobState, WebSocketState } from '@/types/TypeIndex';

interface JobStateDisplayProps {
  state: JobState;
  wsState?: WebSocketState;
}

const JobStateDisplay = ({ state, wsState }: JobStateDisplayProps) => {
  const getStateConfig = () => {
    switch (state) {
      case JobState.WAIT:
        return {
          label: 'En Espera',
          color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: '⏳',
        };
      case JobState.RUNNING:
        return {
          label: wsState === WebSocketState.CONNECTED ? 'En Ejecución (Conectado)' : 'En Ejecución',
          color: 'bg-blue-100 text-blue-800 border-blue-300',
          icon: '▶️',
        };
      case JobState.READY:
        return {
          label: 'Completado',
          color: 'bg-green-100 text-green-800 border-green-300',
          icon: '✅',
        };
      case JobState.ERROR:
        return {
          label: 'Error',
          color: 'bg-red-100 text-red-800 border-red-300',
          icon: '❌',
        };
      case JobState.CANCELLED:
        return {
          label: 'Cancelado',
          color: 'bg-gray-100 text-gray-800 border-gray-300',
          icon: '⏹️',
        };
      case JobState.TERMINATED:
        return {
          label: 'Terminado (Eliminar en 1h)',
          color: 'bg-orange-100 text-orange-800 border-orange-300',
          icon: '⚠️',
        };
      default:
        return {
          label: 'Desconocido',
          color: 'bg-gray-100 text-gray-800 border-gray-300',
          icon: '❓',
        };
    }
  };

  const config = getStateConfig();

  return (
    <div className={`px-4 py-2 rounded-lg border-2 ${config.color} font-semibold flex items-center gap-2 text-sm sm:text-lg`}> {/* Ajuste de padding, font-size */}
      <span className="text-xl sm:text-2xl">{config.icon}</span> {/* Ajuste de font-size del icono */}
      <span className="text-sm sm:text-lg whitespace-nowrap">{config.label}</span> {/* Ajuste de font-size del label y no-wrap */}
    </div>
  );
};

export default JobStateDisplay;