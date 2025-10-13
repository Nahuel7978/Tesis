import { Job, JobState } from '@/types/TypeIndex';
import { Info } from 'lucide-react';
import {useRef} from 'react';

interface JobActionsProps {
  job: Job;
  isStopping: boolean;
  onStopTraining: () => void;
  onDownloadModel: () => void;
  onDownloadTensorboard: () => void;
  onDownloadCheckpoint: () => void;
  onDeleteJob: () => void;
}

const JobActions = ({
  job,
  isStopping,
  onStopTraining,
  onDownloadModel,
  onDownloadTensorboard,
  onDownloadCheckpoint,
  onDeleteJob,
}: JobActionsProps) => {

  const renderActions = () => {
    switch (job.state) {
      case JobState.WAIT:
        return (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 text-lg">
              ⏳ Este job está en espera para ser ejecutado
            </p>
            <p className="text-yellow-600 text-sm mt-2">
              El entrenamiento comenzará en breve...
            </p>
          </div>
        );

      case JobState.RUNNING:
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Acciones</h2>
            <button
              onClick={onStopTraining}
              disabled={isStopping}
              className="w-full md:w-auto px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isStopping ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Deteniendo...
                </>
              ) : (
                <>
                  ⏹️ Detener Entrenamiento
                </>
              )}
            </button>
            <p className="text-sm text-gray-600 mt-3">
              ⚠️ Esta acción cancelará el entrenamiento y no se podrá reanudar
            </p>
          </div>
        );

      case JobState.READY:
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Acciones</h2>
            <div className="flex flex-col md:flex-row gap-4">
              <button
                onClick={onDownloadModel}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                ⬇️ Descargar Modelo Final
              </button>
              <button
                onClick={onDownloadTensorboard}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors flex items-center justify-center gap-2"
              >
                📊 Descargar Tensorboard
              </button>
            </div>
            <p className="text-sm text-green-600 mt-3 text-center">
              ✅ Entrenamiento completado exitosamente
            </p>
          </div>
        );

      case JobState.ERROR:
        return (
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="text-red-800 font-semibold mb-2">❌ Error en el entrenamiento</h3>
              <p className="text-red-600 text-sm">
                El entrenamiento falló debido a:
              </p>
              {job.errors ? (
                <p className="text-red-600 text-sm italic mt-1">
                  {job.errors}
                </p>
              ) : (
                <p className='text-red-600 text-sm italic mt-1'>Un error inesperado</p>
              )}
            </div>
            
            <div className="flex flex-col md:flex-row gap-4">
              <button
                onClick={onDownloadCheckpoint}
                className="flex-1 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center justify-center gap-2"
              >
                ⬇️ Descargar Checkpoint
              </button>
              <button
                onClick={onDeleteJob}
                className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
              >
                🗑️ Eliminar del Historial
              </button>
            </div>
          </div>
        );

      case JobState.CANCELLED:
        return (
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-6 text-center space-y-4">
            <p className="text-gray-800 text-lg">
              ⏹️ Este entrenamiento fue cancelado
            </p>
            <button
              onClick={onDeleteJob}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              🗑️ Eliminar del Historial
            </button>
          </div>
        );

      case JobState.TERMINATED:
        return (
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="text-orange-800 font-semibold mb-2">⚠️ Job Terminado</h3>
              <p className="text-orange-600 text-sm">
                Este job ha sido marcado para eliminación. Tienes 1 hora para descargar los archivos
                antes de que se eliminen permanentemente del servidor.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={onDownloadModel}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                ⬇️ Descargar Modelo
              </button>
              <button
                onClick={onDownloadTensorboard}
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors flex items-center justify-center gap-2"
              >
                📊 Descargar Tensorboard
              </button>
              <button
                onClick={onDeleteJob}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
              >
                🗑️ Eliminar Historial
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return <div>{renderActions()}</div>;
};

export default JobActions;