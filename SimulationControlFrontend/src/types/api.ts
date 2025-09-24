import { JobState } from './base';
import { TrainingMetrics } from './job';
//import {TrainingHyperparameters} from './training'

// API Configuration
export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

// Common API endpoints
export enum ApiEndpoints {
  CREATE_JOB = '/SimulationControlApi/v1/jobs',
  JOB_STATUS = '/SimulationControlApi/v1/state/{jobId}',
  STOP_JOB = '/SimulationControlApi/v1/jobs/{jobId}',
  METRICS_HISTORY = '/SimulationControlApi/v1/jobs/{jobId}/metrics',
  DOWNLOAD_MODEL = '/SimulationControlApi/v1/jobs/{jobId}/download/model',
  DOWNLOAD_TENSORBOARD = '/SimulationControlApi/v1/jobs/{jobId}/download/tensorboard',
  WEBSOCKET = '/SimulationControlApi/ws/v1/jobs/{jobId}/metrics/stream'
}

// Request types
export interface CreateJobApiRequest {
  world_zip: File;
  hparams: string; // JSON stringified TrainingHyperparameters
}

export interface JobStatusApiRequest {
  jobId: string;
}

export interface StopJobApiRequest {
  jobId: string;
}

export interface MetricsHistoryApiRequest {
  jobId: string;
}

export interface DownloadApiRequest {
  jobId: string;
}

// Response types
export interface CreateJobApiResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusApiResponse {
  state: JobState;
  init_timestamp: string;
  end_timestamp?: string;
  errors: string[];
}

export interface MetricsHistoryApiResponse {
  success: boolean;
  data?: TrainingMetrics[];
  message?: string;
}

// Error responses
export interface ApiErrorResponse {
  message: string;
  error?: string;
  details?: any;
}

// WebSocket connection config
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
}

// WebSocket connection state
export enum WebSocketState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR'
}

export interface WebSocketStore {
  state: WebSocketState;
  jobId: string | null;
  error: string | null;
  lastMessage: any | null;
  
  connect: (jobId: string) => void;
  disconnect: () => void;
  onMessage: (callback: (message: any) => void) => () => void; // Returns unsubscribe function
  onStatusChange: (callback: (status: WebSocketState) => void) => () => void;
}