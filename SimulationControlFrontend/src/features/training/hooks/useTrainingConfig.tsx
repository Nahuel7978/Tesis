import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrainingConfig, DEFAULT_HYPERPARAMETERS, ModelParams } from '@/types/training';
import{TrainingAlgorithm, PolicyType} from '@/types/base';
import { JobsService } from '../../../services/api/jobs';
import { jobRepository } from '@/services/storage/JobRepository';
import { validateTrainingConfig, getValidationErrorMessage } from '../../../utils/validationUtil';

const jobsService = new JobsService();


interface UseTrainingConfigReturn {
  config: TrainingConfig;
  isSubmitting: boolean;
  error: string | null;
  updateWorldFile: (file: File | null) => void;
  updateWorldName: (name: string) => void;
  updateRobotName: (name: string) => void;
  updateAlgorithm: (algorithm: TrainingAlgorithm) => void;
  updateTimesteps: (timesteps: number) => void;
  updateModelParam: (key: string, value: any) => void;
  updatePolicy: (policy: PolicyType) => void;
  updateController: (controller: string) => void;
  updateEnvClass: (envClass: string) => void;
  applyTemplate: (algorithm: TrainingAlgorithm, params: ModelParams, timesteps: number) => void;
  submitTraining: () => Promise<void>;
  clearError: () => void;
  resetForm: () => void;
}

const getInitialConfig = (): TrainingConfig => ({
  worldFile: null,
  worldName: '',
  hyperparameters: {
    def_robot: '',
    controller: '',
    env_class: '',
    model: TrainingAlgorithm.DQN,
    policy: PolicyType.MlpPolicy,
    timesteps: 10000,
    model_params: { 
      learning_rate: DEFAULT_HYPERPARAMETERS[TrainingAlgorithm.DQN].learning_rate ?? 0.001
    }
  }
});

export const useTrainingConfig = (): UseTrainingConfigReturn => {
  const navigate = useNavigate();
  const [config, setConfig] = useState<TrainingConfig>(getInitialConfig());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateWorldFile = useCallback((file: File | null) => {
    setConfig(prev => ({
      ...prev,
      worldFile: file,
    }));
    setError(null);
  }, []);

  const updateWorldName = useCallback((name: string) => {
    setConfig(prev => ({
      ...prev,
      worldName: name
    }));
    setError(null);
  }, []);

  const updateRobotName = useCallback((name: string) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        def_robot: name
      }
    }));
    setError(null);
  }, []);

  const updateAlgorithm = useCallback((algorithm: TrainingAlgorithm) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        model: algorithm,
        model_params: {
          ...DEFAULT_HYPERPARAMETERS[algorithm],
          learning_rate: DEFAULT_HYPERPARAMETERS[algorithm].learning_rate ?? 0.001
        }
      }
    }));
  }, []);

  const updateTimesteps = useCallback((timesteps: number) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        timesteps
      }
    }));
  }, []);

  const updateModelParam = useCallback((key: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        model_params: {
          ...prev.hyperparameters.model_params,
          [key]: value
        }
      }
    }));
  }, []);

  const updatePolicy = useCallback((policy: PolicyType) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        policy
      }
    }));
  }, []);

  const updateController = useCallback((controller: string) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        controller
      }
    }));
  }, []);

  const updateEnvClass = useCallback((envClass: string) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        env_class: envClass
      }
    }));
  }, []);

  const applyTemplate = useCallback((
    algorithm: TrainingAlgorithm,
    params: ModelParams,
    timesteps: number
  ) => {
    setConfig(prev => ({
      ...prev,
      hyperparameters: {
        ...prev.hyperparameters,
        model: algorithm,
        timesteps,
        model_params: { ...params }
      }
    }));
  }, []);

  const submitTraining = useCallback(async () => {
    setError(null);

    // Validar configuración
    const validation = validateTrainingConfig(config);
    if (!validation.isValid) {
      setError(getValidationErrorMessage(validation.errors));
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await jobsService.createJob(
        config.worldFile!,
        config.hyperparameters
      );

      // Guardar el job en el almacenamiento local
      const newJob = {
        id: response.job_id,
        state: 'WAIT' as any,
        worldName: config.worldName,
        hyperparameters: config.hyperparameters,
        createdAt: new Date().toISOString(),
        lastUpdated: new Date().toISOString()
      };

      jobRepository.saveJob(newJob)

      console.log('[useTrainingConfig] Job created successfully:', response.job_id);

      navigate('/dashboard')

    } catch (err: any) {
      console.error('[useTrainingConfig] Error creating job:', err);
      
      if (err.response?.status === 400) {
        setError('Datos inválidos. Verifica la configuración del entrenamiento.');
      } else if (err.response?.status === 413) {
        setError('El archivo es demasiado grande. Máximo permitido: 100MB');
      } else if (err.response?.status === 500) {
        setError('Error en el servidor. Por favor, intenta más tarde.');
      } else if (err.response?.status === 503) {
        setError('El servicio no está disponible temporalmente. Intenta más tarde.');
      } else if (err.code === 'ECONNABORTED') {
        setError('Tiempo de espera agotado. Verifica tu conexión.');
      } else if (err.code === 'ERR_NETWORK') {
        setError('No se pudo conectar con el servidor. Verifica tu conexión.');
      } else {
        setError(
          err.response?.data?.message || 
          err.response?.data?.detail ||
          'Error al crear el entrenamiento. Por favor, intenta nuevamente.'
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [config, navigate]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const resetForm = useCallback(() => {
    setConfig(getInitialConfig());
    setError(null);
  }, []);

  return {
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
    applyTemplate,
    submitTraining,
    clearError,
    resetForm
  };
};