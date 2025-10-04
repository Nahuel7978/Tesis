import { TrainingAlgorithm, PolicyType } from './base';

// Model hyperparameters - extensible for different algorithms
export interface ModelParams {
  // Common to most algorithms
  learning_rate: number;
  gamma?: number; // Discount factor
  batch_size?: number;
  n_steps?: number; // Number of steps to run for each environment per update
  policy_delay?: number; // Delay for policy updates (TD3 only)
  target_policy_noise?: number; // Noise added to target policy during critic update (TD3 only)
  target_noise_clip?: number; // Range to clip target policy noise (TD3 only)
  verbose?: number;
  max_grad_norm?: number;
  
  // Replay Buffer / Off-Policy Specific (DQN, SAC, TD3, DDPG)
  buffer_size?: number; // Replay buffer size
  learning_starts?: number; // Number of steps before learning starts
  train_freq?: number;
  gradient_steps?: number;

  // DQN Specific
  tau?: number; // Polyak factor for target update 
  target_update_interval?: number;
  exploration_fraction?: number;
  exploration_initial_eps?: number;
  exploration_final_eps?: number;

  // PPO/A2C Specific
  ent_coef?: number | string; // Entropy coefficient
  vf_coef?: number; // Value function coefficient
  n_epochs?: number; // Number of epoch when optimizing the surrogate loss (PPO)
  gae_lambda?: number; // Factor for trade-off of bias vs variance for Generalized Advantage Estimator
  clip_range?: number; // Clipping parameter for the policy loss (PPO only)
  normalize_advantage?: boolean; // Whether to normalize the advantage (PPO only)
  use_sde?: boolean; // Whether to use State Dependent Exploration (SDE)
  sde_sample_freq?: number; // Sample a new noise every n steps when using SDE
  use_sde_at_warmup?: boolean; // Whether to use SDE at the beginning of training (SAC only)
  target_kl: number | undefined; // Target KL divergence threshold (PPO only)
  rms_prop_eps?: number; // Epsilon value for the RMSprop optimizer (A2C only)
  // Allow flexibility for custom params or parameters not explicitly listed
  [key: string]: any; 
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
      learning_rate:0.0001,
      buffer_size:1000000,
      learning_starts:100,
      batch_size:32,
      tau: 1.0,
      gamma: 0.99,
      train_freq:4,
      gradient_steps:1, 
      n_steps:1, 
      target_update_interval:10000, 
      exploration_fraction:0.1, 
      exploration_initial_eps:1.0, 
      exploration_final_eps:0.05, 
      max_grad_norm:10, 
      verbose:2
    },
    [TrainingAlgorithm.PPO]: {
      learning_rate:0.0003,
      n_steps:2048,
      batch_size:64,
      n_epochs:10,
      gamma:0.99,
      gae_lambda:0.95,
      clip_range:0.2,
      normalize_advantage:true,
      ent_coef:0.0,
      vf_coef:0.5,
      max_grad_norm:0.5,
      use_sde:false,
      sde_sample_freq:-1,
      target_kl:undefined,
      verbose:2
    },
    [TrainingAlgorithm.A2C]: {
      learning_rate:0.0007,
      n_steps:5,
      amma:0.99,
      gae_lambda:1.0,
      ent_coef:0.0,
      vf_coef:0.5,
      max_grad_norm:0.5,
      rms_prop_eps:1e-05,
      use_sde:false,
      sde_sample_freq:-1,
      normalize_advantage:false,
      verbose:2
    },
    [TrainingAlgorithm.SAC]: {
      learning_rate:0.0003,
      buffer_size:1000000,
      learning_starts:100,
      batch_size:256,
      tau:0.005,
      gamma:0.99,
      train_freq:1,
      gradient_steps:1,
      n_steps:1,
      ent_coef:'auto',
      target_update_interval:1,
      use_sde:false,
      sde_sample_freq:-1,
      use_sde_at_warmup:false,
      verbose:2
    },
    [TrainingAlgorithm.TD3]: {
      learning_rate:0.001,
      buffer_size:1000000,
      learning_starts:100,
      batch_size:256,
      tau:0.005,
      gamma:0.99,
      train_freq:1,
      gradient_steps:1,
      n_steps:1,
      policy_delay:2,
      target_policy_noise:0.2,
      target_noise_clip:0.5,
      verbose:2
    },
    [TrainingAlgorithm.DDPG]: {
      learning_rate:0.001,
      buffer_size:1000000,
      learning_starts:100,
      batch_size:256,
      tau:0.005,
      gamma:0.99,
      train_freq:1,
      gradient_steps:1,
      n_steps:1,
      verbose:2,
    }
  };