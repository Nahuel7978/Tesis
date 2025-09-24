export enum JobState {
    WAIT = 'WAIT',
    RUNNING = 'RUNNING', // WebSocket variant
    READY = 'READY',
    ERROR = 'ERROR',
    TERMINATED = 'TERMINATED'
  } 
  
  export enum WebSocketMessageType {
    STATUS = 'status',
    METRICS = 'metrics'
  }
  
  // Supported algorithms from stable-baselines3
  export enum TrainingAlgorithm {
    DQN = 'DQN',
    PPO = 'PPO',
    A2C = 'A2C',
    SAC = 'SAC',
    TD3 = 'TD3',
    DDPG = 'DDPG'
  }
  
  // Supported policies
  export enum PolicyType {
    MlpPolicy = 'MlpPolicy',
    CnnPolicy = 'CnnPolicy',
    MultiInputPolicy = 'MultiInputPolicy'
  }
  
  // Common API response structure
  export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    message?: string;
    error?: string;
  }
  
  // Error handling
  export interface ApiError {
    message: string;
    code?: string;
    details?: any;
  }