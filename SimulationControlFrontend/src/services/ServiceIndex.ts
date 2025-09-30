import jobsService from './api/jobs';
import jobWebSocketService from './websocket/jobs_websocket';

// API Services
export { default as apiClient, apiClient as api } from './api/client';
export { default as jobsService, JobsService } from './api/jobs';

// WebSocket Services
export { jobWebSocketService, JobWebSocketService } from './websocket/jobs_websocket';

// Re-export for convenience
export const services = {
  jobs: jobsService,
  websocket: jobWebSocketService
} as const;