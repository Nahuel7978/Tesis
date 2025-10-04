import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import BasicConfigSection from '../features/training/components/BasicConfigSection'; // Ensure this path is correct
import HyperparametersSection from '../features/training/components/HyperparametersSection';
import TrainingSummary from '../features/training/components/TrainingSummary';
import { useTrainingConfig } from '../features/training/hooks/useTrainingConfig';

const TrainingConfigPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    config,
    isSubmitting,
    error,
    updateWorldFile,
    updateWorldName,
    updateRobotName,
    updateAlgorithm,
    updateTimesteps,
    updateModelParam,
    updatePolicy,
    updateController,
    updateEnvClass,
    submitTraining,
    clearError
  } = useTrainingConfig();

  const isFormValid = !!(config.worldFile && config.hyperparameters.def_robot.trim());

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button
            onClick={() => navigate('/test')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Volver al Dashboard</span>
          </button>
          
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Configurar Nuevo Entrenamiento
            </h1>
            <p className="text-gray-600 mt-2">
              Selecciona el algoritmo, hiperparámetros y entorno para tu entrenamiento
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3 animate-in fade-in duration-200">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button
              onClick={clearError}
              className="text-red-600 hover:text-red-800 text-xl leading-none"
            >
              ×
            </button>
          </div>
        )}

        {/* Basic Configuration */}
        <BasicConfigSection
          worldFile={config.worldFile}
          worldName={config.worldName}
          robotName={config.hyperparameters.def_robot}
          controllerName={config.hyperparameters.controller}
          envClass={config.hyperparameters.env_class}
          policy={config.hyperparameters.policy}
          algorithm={config.hyperparameters.model}
          timesteps={config.hyperparameters.timesteps}
          onWorldFileChange={updateWorldFile}
          onWorldNameChange={updateWorldName}
          onRobotNameChange={updateRobotName}
          onControllerNameChange={updateController}
          onEnvClassChange={updateEnvClass}
          onPolicyChange={updatePolicy}
          onAlgorithmChange={updateAlgorithm}
          onTimestepsChange={updateTimesteps}
        />

        {/* Hyperparameters */}
        <HyperparametersSection
          algorithm={config.hyperparameters.model}
          modelParams={config.hyperparameters.model_params}
          onParamChange={updateModelParam}
        />

        {/* Training Summary */}
        <TrainingSummary
          config={config}
          isVisible={isFormValid}
        />

        {/* Action Buttons */}
        <div className="mt-8 flex justify-end gap-4 pb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
            disabled={isSubmitting}
          >
            Cancelar
          </button>
          <button
            onClick={submitTraining}
            disabled={isSubmitting || !isFormValid}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Creando Entrenamiento...
              </>
            ) : (
              <>
                Iniciar Entrenamiento
              </>
            )}
          </button>
        </div>

        {/* Help Text */}
        {!isFormValid && (
          <div className="mb-8 text-center">
            <p className="text-sm text-gray-500">
              Completa los campos obligatorios para continuar
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrainingConfigPage;