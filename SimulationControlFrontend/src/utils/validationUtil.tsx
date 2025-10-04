import { TrainingConfig} from '@/types/training';
import {TrainingAlgorithm } from '@/types/base';

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * Valida la configuración completa del entrenamiento
 */
export const validateTrainingConfig = (config: TrainingConfig): ValidationResult => {
  const errors: ValidationError[] = [];

  // Validar archivo del mundo
  if (!config.worldFile) {
    errors.push({
      field: 'worldFile',
      message: 'Debes seleccionar un archivo .zip del mundo de Webots'
    });
  } else {
    if (!config.worldFile.name.toLowerCase().endsWith('.zip')) {
      errors.push({
        field: 'worldFile',
        message: 'El archivo debe tener extensión .zip'
      });
    }

    // Validar tamaño (100MB máximo)
    const maxSize = 100 * 1024 * 1024; // 100MB en bytes
    if (config.worldFile.size > maxSize) {
      errors.push({
        field: 'worldFile',
        message: 'El archivo excede el tamaño máximo de 100MB'
      });
    }
  }

  // Validar nombre del robot
  if (!config.hyperparameters.def_robot.trim()) {
    errors.push({
      field: 'def_robot',
      message: 'Debes especificar el nombre del robot (DEF)'
    });
  } else if (config.hyperparameters.def_robot.includes(' ')) {
    errors.push({
      field: 'def_robot',
      message: 'El nombre del robot no debe contener espacios'
    });
  }

  // Validar timesteps
  if (config.hyperparameters.timesteps <= 0) {
    errors.push({
      field: 'timesteps',
      message: 'Los episodios totales deben ser mayor a 0'
    });
  }

  if (config.hyperparameters.timesteps > 10000000) {
    errors.push({
      field: 'timesteps',
      message: 'Los episodios totales no deben exceder 10,000,000'
    });
  }

  // Validar hiperparámetros del modelo
  const paramErrors = validateModelParams(
    config.hyperparameters.model,
    config.hyperparameters.model_params
  );
  errors.push(...paramErrors);

  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Valida los hiperparámetros específicos del modelo
 */
export const validateModelParams = (
  algorithm: TrainingAlgorithm,
  params: any
): ValidationError[] => {
  const errors: ValidationError[] = [];

  // Validaciones comunes
  if (params.learning_rate !== undefined) {
    if (params.learning_rate <= 0) {
      errors.push({
        field: 'learning_rate',
        message: 'El learning rate debe ser mayor a 0'
      });
    }
    if (params.learning_rate > 1) {
      errors.push({
        field: 'learning_rate',
        message: 'El learning rate no debe ser mayor a 1'
      });
    }
  }

  if (params.batch_size !== undefined) {
    if (params.batch_size <= 0) {
      errors.push({
        field: 'batch_size',
        message: 'El batch size debe ser mayor a 0'
      });
    }
    if (!Number.isInteger(params.batch_size)) {
      errors.push({
        field: 'batch_size',
        message: 'El batch size debe ser un número entero'
      });
    }
  }

  if (params.gamma !== undefined) {
    if (params.gamma < 0 || params.gamma > 1) {
      errors.push({
        field: 'gamma',
        message: 'Gamma debe estar entre 0 y 1'
      });
    }
  }

  // Validaciones específicas por algoritmo
  switch (algorithm) {
    case TrainingAlgorithm.DQN:
      if (params.target_update_interval !== undefined) {
        if (params.target_update_interval <= 0) {
          errors.push({
            field: 'target_update_interval',
            message: 'Target update interval debe ser mayor a 0'
          });
        }
      }
      if (params.exploration_initial_eps !== undefined) {
        if (params.exploration_initial_eps < 0 || params.exploration_initial_eps > 1) {
          errors.push({
            field: 'exploration_initial_eps',
            message: 'Epsilon inicial debe estar entre 0 y 1'
          });
        }
      }
      if (params.exploration_final_eps !== undefined) {
        if (params.exploration_final_eps < 0 || params.exploration_final_eps > 1) {
          errors.push({
            field: 'exploration_final_eps',
            message: 'Epsilon final debe estar entre 0 y 1'
          });
        }
      }
      break;

    case TrainingAlgorithm.PPO:
    case TrainingAlgorithm.A2C:
      if (params.n_steps !== undefined) {
        if (params.n_steps <= 0) {
          errors.push({
            field: 'n_steps',
            message: 'N steps debe ser mayor a 0'
          });
        }
      }
      if (params.ent_coef !== undefined) {
        if (params.ent_coef < 0) {
          errors.push({
            field: 'ent_coef',
            message: 'Entropy coefficient debe ser mayor o igual a 0'
          });
        }
      }
      if (params.vf_coef !== undefined) {
        if (params.vf_coef < 0) {
          errors.push({
            field: 'vf_coef',
            message: 'Value function coefficient debe ser mayor o igual a 0'
          });
        }
      }
      break;

    case TrainingAlgorithm.SAC:
    case TrainingAlgorithm.TD3:
    case TrainingAlgorithm.DDPG:
      if (params.tau !== undefined) {
        if (params.tau < 0 || params.tau > 1) {
          errors.push({
            field: 'tau',
            message: 'Tau debe estar entre 0 y 1'
          });
        }
      }
      if (params.buffer_size !== undefined) {
        if (params.buffer_size <= 0) {
          errors.push({
            field: 'buffer_size',
            message: 'Buffer size debe ser mayor a 0'
          });
        }
      }
      break;
  }

  return errors;
};

/**
 * Formatea un error de validación para mostrarlo al usuario
 */
export const formatValidationError = (error: ValidationError): string => {
  return error.message;
};

/**
 * Obtiene todos los errores como un mensaje único
 */
export const getValidationErrorMessage = (errors: ValidationError[]): string => {
  if (errors.length === 0) return '';
  if (errors.length === 1 && errors[0]) return errors[0].message;
  
  return `Se encontraron ${errors.length} errores:\n${errors.map(e => `• ${e.message}`).join('\n')}`;
};