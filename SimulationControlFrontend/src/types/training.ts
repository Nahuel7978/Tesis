import { TrainingAlgorithm, PolicyType } from './base';

// Model hyperparameters - extensible for different algorithms
export interface ModelParams {
  verbose?: number;
  learning_rate?: number;
  batch_size?: number;
  gamma?: number;
  // DQN specific
  target_update_interval?: number;
  exploration_initial_eps?: number;
  exploration_final_eps?: number;
  // PPO specific
  n_steps?: number;
  ent_coef?: number;
  vf_coef?: number;
  // SAC specific
  tau?: number;
  buffer_size?: number;
  // Add more as needed
  [key: string]: any; // Allow flexibility for custom params
}

// Complete hyperparameters structure sent to API
export interface TrainingHyperparameters {
  def_robot: string;
  controller: string;
  env_class: string;
  model: TrainingAlgorithm;
  policy: PolicyType;
  timesteps: number;
  model_params: ModelParams;
}

// Form data structure for training configuration
export interface TrainingConfig {
  worldFile: File | null;
  worldName: string;
  hyperparameters: TrainingHyperparameters;
}

// Default hyperparameters for each algorithm
export const DEFAULT_HYPERPARAMETERS: Record<TrainingAlgorithm, Partial<ModelParams>> = {
    [TrainingAlgorithm.DQN]: {
      verbose: 2,
      learning_rate: 0.0003,
      batch_size: 64,
      gamma: 0.99,
      target_update_interval: 1000,
      exploration_initial_eps: 1.0,
      exploration_final_eps: 0.05
    },
    [TrainingAlgorithm.PPO]: {
      verbose: 2,
      learning_rate: 0.0003,
      batch_size: 64,
      gamma: 0.99,
      n_steps: 2048,
      ent_coef: 0.0,
      vf_coef: 0.5
    },
    [TrainingAlgorithm.A2C]: {
      verbose: 2,
      learning_rate: 0.0007,
      gamma: 0.99,
      ent_coef: 0.01,
      vf_coef: 0.25
    },
    [TrainingAlgorithm.SAC]: {
      verbose: 2,
      learning_rate: 0.0003,
      batch_size: 256,
      gamma: 0.99,
      tau: 0.005,
      buffer_size: 1000000
    },
    [TrainingAlgorithm.TD3]: {
      verbose: 2,
      learning_rate: 0.001,
      batch_size: 256,
      gamma: 0.99,
      tau: 0.005,
      buffer_size: 1000000
    },
    [TrainingAlgorithm.DDPG]: {
      verbose: 2,
      learning_rate: 0.001,
      batch_size: 128,
      gamma: 0.99,
      tau: 0.001,
      buffer_size: 1000000
    }
  };