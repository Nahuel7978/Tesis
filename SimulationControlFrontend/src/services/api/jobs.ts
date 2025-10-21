import axios from './client';
import {
  CreateJobApiResponse,
  JobStatusApiResponse,
  TrainingMetrics,
  TrainingHyperparameters,
  ApiErrorResponse
} from '@/types/TypeIndex';
import { dialogService } from '@/services/tauri/dialogService';

export class JobsService {
  /**
   * Crea un nuevo job de entrenamiento
   * @param worldFile - Archivo .zip del mundo de Webots
   * @param hyperparameters - Configuración del entrenamiento
   * @returns Job ID creado
   */
  async createJob(
    worldFile: File,
    hyperparameters: TrainingHyperparameters
  ): Promise<CreateJobApiResponse> {
    try {
      const formData = new FormData();
      formData.append('world_zip', worldFile);
      formData.append('hparams', JSON.stringify(hyperparameters));

      const response = await axios.post<CreateJobApiResponse>(
        '/jobs',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error('[JobsService] Error creating job:', error);
      throw error;
    }
  }
  
  /**
   * Detiene un job en ejecución
   * @param jobId - ID del job a detener
   */
  async stopJob(jobId: string): Promise<void> {
     try {
        await axios.delete(`/jobs/${jobId}`);
        console.log(`[JobsService] Job ${jobId} stopped successfully`);
     } catch (error) {
        console.error(`[JobsService] Error stopping job ${jobId}:`, error);
        throw error;
     }
  }

  /**
   * Obtiene el estado actual de un job
   * @param jobId - ID del job (ej: "job_5")
   * @returns Estado del job con timestamps
   */
  async getJobStatus(jobId: string): Promise<JobStatusApiResponse> {
    try {
      const response = await axios.get<JobStatusApiResponse>(
        `/state/${jobId}`
      );

      return response.data;
    } catch (error) {
      console.error(`[JobsService] Error getting status for ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * Obtiene el historial completo de métricas de un job
   * @param jobId - ID del job
   * @returns Array de métricas históricas
   */
  async getMetricsHistory(jobId: string): Promise<TrainingMetrics[]> {
    try {
      const response = await axios.get<TrainingMetrics[] | ApiErrorResponse>(
        `/jobs/${jobId}/metrics`
      );

      // Manejar respuesta de error (message: "No logs found.")
      if (!Array.isArray(response.data)) {
        if ('message' in response.data) {
          console.warn(`[JobsService] ${response.data.message}`);
          return [];
        }
      }

      return response.data as TrainingMetrics[];
    } catch (error) {
      console.error(`[JobsService] Error getting metrics for ${jobId}:`, error);
      throw error;
    }
  }

/**
   * Descarga los logs de Tensorboard
   * @param jobId - ID del job
   * @returns Blob del archivo de tensorboard
   */
  async downloadTensorboard(jobId: string): Promise<Blob> {
    try {
      const response = await axios.get(`/jobs/${jobId}/download/tensorboard`, {
        responseType: 'blob'
      });

      return response.data;
    } catch (error) {
      console.error(`[JobsService] Error downloading tensorboard for ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * Descarga el modelo entrenado
   * @param jobId - ID del job
   * @returns Blob del archivo del modelo
   */
  async downloadModel(jobId: string): Promise<Blob> {
    try {
      const response = await axios.get(`/jobs/${jobId}/download/model`, {
        responseType: 'blob'
      });

      return response.data;
    } catch (error) {
      console.error(`[JobsService] Error downloading model for ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * Helper para descargar un blob como archivo
   * @param blob - Blob a descargar
   * @param filename - Nombre del archivo
   */
  async downloadBlob(blob: Blob, filename: string): Promise<void> {
    // Si estamos en Tauri, usar diálogo de guardado
    if (dialogService.isTauriAvailable()) {
      try {
        const saved = await dialogService.saveFile(blob, filename);
        if (saved) {
          console.log(`[JobsService] Archivo guardado exitosamente: ${filename}`);
        }
      } catch (error) {
        console.error('[JobsService] Error al guardar archivo:', error);
        throw error;
      }
    } else {
      // Fallback para navegador web (descarga directa)
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }
  }
}

// Singleton instance
export const jobsService = new JobsService();
export default jobsService;