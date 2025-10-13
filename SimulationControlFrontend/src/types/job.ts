import { JobState, WebSocketMessageType } from './base';
import { TrainingHyperparameters } from './training';

// Core Job interface - stored locally and synced with backend
export interface Job {
  id: string; // e.g., "job_5"
  state: JobState;
  worldName: string;
  hyperparameters: TrainingHyperparameters;
  createdAt: string; // ISO timestamp
  lastUpdated: string; // ISO timestamp
  // Optional fields populated from API
  initTimestamp?: string | undefined;
  endTimestamp?: string | undefined;
  errors?: string[];
}

export interface JobSummary {
  id: string;
  state: JobState;
  worldName: string;
  createdAt: string;
}

// Job status response from API
export interface JobStatusResponse {
  state: JobState;
  init_timestamp: string;
  end_timestamp?: string;
  errors: string[];
}

// Training metrics received from API/WebSocket
export interface TrainingMetrics {
  ep_len_mean: number;
  ep_rew_mean?: number;
  exploration_rate: number;
  episodes: number;
  fps: number;
  time_elapsed: number;
  total_timesteps: number;
  timestamp: string;
}

// Job creation request
export interface CreateJobRequest {
  world_zip: File;
  hparams: TrainingHyperparameters;
}

// Job creation response
export interface CreateJobResponse {
  job_id: string;
  status: string;
  message: string;
}

// Metrics history response
export interface MetricsHistoryResponse {
  success: boolean;
  data?: TrainingMetrics[];
  message?: string;
}

// WebSocket message types
export interface WebSocketStatusMessage {
  type: typeof WebSocketMessageType.STATUS;
  state: JobState;
  message: string;
}

export interface WebSocketMetricsMessage extends TrainingMetrics {
  // Metrics data is flat in the message
}

export type WebSocketMessage = WebSocketStatusMessage | WebSocketMetricsMessage;

// Job actions
export interface JobActions {
  start: (config: { worldFile: File; hyperparameters: TrainingHyperparameters }) => Promise<string>;
  stop: (jobId: string) => Promise<void>;
  getStatus: (jobId: string) => Promise<JobStatusResponse>;
  getMetricsHistory: (jobId: string) => Promise<TrainingMetrics[]>;
  downloadModel: (jobId: string) => Promise<Blob>;
  downloadTensorboard: (jobId: string) => Promise<Blob>;
  downloadCheckpoint: (jobId: string) => Promise<Blob>;
}

// Job store state
export interface JobStore {
  jobs: Record<string, Job>;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  addJob: (job: Job) => void;
  updateJob: (jobId: string, updates: Partial<Job>) => void;
  removeJob: (jobId: string) => void;
  getJob: (jobId: string) => Job | undefined;
  getAllJobs: () => Job[];
  getJobsByState: (state: JobState) => Job[];
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}