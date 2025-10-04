import React from 'react';
import { TrainingAlgorithm } from '@/types/base';
import {  ModelParams } from '@/types/training';
import HyperparameterInput from './HyperparameterInput';

interface HyperparametersSectionProps {
  algorithm: TrainingAlgorithm;
  modelParams: ModelParams;
  onParamChange: (key: string, value: any) => void;
}

// Definición de hiperparámetros por algoritmo
const ALGORITHM_PARAMS: Record<TrainingAlgorithm, Array<{
  key: keyof ModelParams;
  label: string;
  type: 'number' | 'integer';
  min?: number;
  max?: number;
  step?: number;
  description?: string;
}>> = {
  [TrainingAlgorithm.DQN]: [
    // DQN
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje del optimizador' },
    { key: 'buffer_size', label: 'Tamaño del Buffer', type: 'integer', min: 1000, max: 10000000, step: 100000, description: 'Tamaño máximo del buffer de repetición' },
    { key: 'batch_size', label: 'Tamaño del Lote', type: 'integer', min: 16, step: 32, description: 'Tamaño del minibatch para actualización' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento (0.99 es común)' },
    { key: 'target_update_interval', label: 'Actualización Objetivo', type: 'integer', min: 100, step: 1000, description: 'Frecuencia de actualización de la red objetivo' },
    { key: 'exploration_initial_eps', label: 'Epsilon Inicial', type: 'number', min: 0, max: 1, step: 0.05, description: 'Epsilon inicial para exploración' },
    { key: 'exploration_final_eps', label: 'Epsilon Final', type: 'number', min: 0, max: 1, step: 0.01, description: 'Epsilon final después del decaimiento' },
    { key: 'exploration_fraction', label: 'Fracción de Exploración', type: 'number', min: 0.01, max: 1.0, step: 0.01, description: 'Fracción del entrenamiento para el decaimiento de Epsilon' },
  ],
  [TrainingAlgorithm.PPO]: [
    // PPO
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje del optimizador' },
    { key: 'n_steps', label: 'N Pasos', type: 'integer', min: 128, step: 128, description: 'Número de pasos por entorno antes de cada actualización' },
    { key: 'batch_size', label: 'Tamaño del Lote', type: 'integer', min: 16, step: 32, description: 'Tamaño del minibatch para optimización' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento' },
    { key: 'n_epochs', label: 'N Épocas', type: 'integer', min: 1, max: 20, step: 1, description: 'Número de pasadas sobre los datos recopilados' },
    { key: 'gae_lambda', label: 'GAE Lambda', type: 'number', min: 0.0, max: 1.0, step: 0.05, description: 'Parámetro Lambda para GAE' },
    { key: 'clip_range', label: 'Rango de Clipping', type: 'number', min: 0.05, max: 0.5, step: 0.01, description: 'Parámetro de clipping para la pérdida de la política' },
    { key: 'ent_coef', label: 'Coeficiente Entropía', type: 'number', min: 0.0, max: 0.1, step: 0.001, description: 'Coeficiente de la pérdida de entropía' },
    { key: 'vf_coef', label: 'Coef. Función Valor', type: 'number', min: 0.1, max: 1.0, step: 0.05, description: 'Coeficiente de la pérdida de la función de valor' },
  ],
  [TrainingAlgorithm.A2C]: [
    // A2C (Similar a PPO, pero sin n_epochs, clip_range, etc.)
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje del optimizador' },
    { key: 'n_steps', label: 'N Pasos', type: 'integer', min: 1, step: 1, description: 'Número de pasos por entorno antes de cada actualización' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento' },
    { key: 'gae_lambda', label: 'GAE Lambda', type: 'number', min: 0.0, max: 1.0, step: 0.05, description: 'Parámetro Lambda para GAE' },
    { key: 'ent_coef', label: 'Coeficiente Entropía', type: 'number', min: 0.0, max: 0.1, step: 0.001, description: 'Coeficiente de la pérdida de entropía' },
    { key: 'vf_coef', label: 'Coef. Función Valor', type: 'number', min: 0.1, max: 1.0, step: 0.05, description: 'Coeficiente de la pérdida de la función de valor' },
    { key: 'rms_prop_eps', label: 'RMSProp Epsilon', type: 'number', min: 1e-7, max: 1e-4, step: 1e-6, description: 'Valor épsilon para el optimizador RMSprop' },
  ],
  [TrainingAlgorithm.SAC]: [
    // SAC
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje (comúnmente 3e-4)' },
    { key: 'buffer_size', label: 'Tamaño del Buffer', type: 'integer', min: 1000, max: 10000000, step: 100000, description: 'Tamaño máximo del buffer de repetición' },
    { key: 'batch_size', label: 'Tamaño del Lote', type: 'integer', min: 32, step: 32, description: 'Tamaño del minibatch' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento' },
    { key: 'tau', label: 'Tau (Soft Update)', type: 'number', min: 0.001, max: 0.1, step: 0.001, description: 'Coeficiente de actualización suave para la red objetivo' },
  ],
  [TrainingAlgorithm.TD3]: [
    // TD3
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje (comúnmente 1e-3)' },
    { key: 'buffer_size', label: 'Tamaño del Buffer', type: 'integer', min: 1000, max: 10000000, step: 100000, description: 'Tamaño máximo del buffer de repetición' },
    { key: 'batch_size', label: 'Tamaño del Lote', type: 'integer', min: 32, step: 32, description: 'Tamaño del minibatch' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento' },
    { key: 'tau', label: 'Tau (Soft Update)', type: 'number', min: 0.001, max: 0.1, step: 0.001, description: 'Coeficiente de actualización suave' },
    { key: 'policy_delay', label: 'Retraso de Política', type: 'integer', min: 1, max: 10, step: 1, description: 'Número de actualizaciones de la Q-network antes de actualizar la Política' },
    { key: 'target_policy_noise', label: 'Ruido de Política Objetivo', type: 'number', min: 0.0, max: 1.0, step: 0.01, description: 'Desviación estándar del ruido añadido a la acción objetivo' },
  ],
  [TrainingAlgorithm.DDPG]: [
    // DDPG (Similar a TD3, pero sin los refinamientos de delay/noise)
    { key: 'learning_rate', label: 'Tasa de Aprendizaje', type: 'number', min: 1e-6, max: 0.1, step: 0.0001, description: 'Tasa de aprendizaje (comúnmente 1e-3)' },
    { key: 'buffer_size', label: 'Tamaño del Buffer', type: 'integer', min: 1000, max: 10000000, step: 100000, description: 'Tamaño máximo del buffer de repetición' },
    { key: 'batch_size', label: 'Tamaño del Lote', type: 'integer', min: 32, step: 32, description: 'Tamaño del minibatch' },
    { key: 'gamma', label: 'Gamma', type: 'number', min: 0.8, max: 1.0, step: 0.001, description: 'Factor de descuento' },
    { key: 'tau', label: 'Tau (Soft Update)', type: 'number', min: 0.001, max: 0.1, step: 0.001, description: 'Coeficiente de actualización suave' },
  ],
};

const HyperparametersSection: React.FC<HyperparametersSectionProps> = ({
  algorithm,
  modelParams,
  onParamChange,
}) => {
  const params = ALGORITHM_PARAMS[algorithm];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        <u>Hiperparámetros</u>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ">
        {params.map((param) => (
          <HyperparameterInput
            key={param.key}
            label={param.label}
            value={modelParams[param.key] ?? 0}
            type={param.type}
            min={param.min ?? undefined}
            max={param.max ?? undefined}
            step={param.step ?? undefined}
            description={param.description ?? undefined}
            onChange={(value) => onParamChange(param.key as string, value)}
          />
        ))}
      </div>

      {/* Info box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Nota:</strong> Los valores predeterminados están optimizados para la mayoría de casos.
          Ajusta los hiperparámetros según las características específicas de tu entorno de entrenamiento.
        </p>
      </div>
    </div>
  );
};

export default HyperparametersSection;