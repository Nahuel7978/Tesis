import React from 'react';
import { FileArchive, Brain, Target, Settings2, Clock } from 'lucide-react';
import { TrainingConfig } from '@/types/training';

interface TrainingSummaryProps {
  config: TrainingConfig;
  isVisible: boolean;
}

const TrainingSummary: React.FC<TrainingSummaryProps> = ({ config, isVisible }) => {
  if (!isVisible) return null;

  const { worldFile, hyperparameters } = config;
  const { def_robot, model, model_params, policy } = hyperparameters;


  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6 mt-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Settings2 className="w-5 h-5 text-blue-600" />
        Resumen de Configuración
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-4">
        {/* World File */}
        {worldFile && (
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <FileArchive className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700"><strong>Mundo</strong></p>
                <p className="text-sm text-gray-900 truncate">{worldFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(worldFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Robot */}
        {def_robot && (
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-700"><strong>Robot</strong></p>
                <p className="text-sm text-gray-900">{def_robot}</p>
              </div>
            </div>
          </div>
        )}

        {/* Algorithm */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <Brain className="w-5 h-5 text-purple-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-700"><strong>Algoritmo</strong></p>
              <p className="text-sm text-gray-900">{model}</p>
              <p className="text-xs text-gray-500">
                Learning Rate: {model_params.learning_rate}
              </p>
            </div>
          </div>
        </div>

        {/* Policy */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-orange-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-700 "><strong>Policy</strong></p>
              <p className="text-sm text-gray-900">
                {policy}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Parameters */}
      <div className="mt-4 pt-4 border-t border-blue-200">
        <p className="text-xs font-medium text-gray-700 mb-2">
          Hiperparámetros clave:
        </p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(model_params)
            .filter(([_, value]) => value !== undefined)
            .slice(0, 6)
            .map(([key, value]) => (
              <span
                key={key}
                className="px-3 py-1 bg-white text-xs rounded-full border border-blue-200 text-gray-700"
              >
                {key}: <strong>{typeof value === 'number' ? value.toFixed(4) : value}</strong>
              </span>
            ))}
        </div>
      </div>
    </div>
  );
};

export default TrainingSummary;