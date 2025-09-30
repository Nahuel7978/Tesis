// JobRepository.ts

import {IStorage, storage} from '@/services/storage/StorageIndex';
import { Job, JobSummary } from '@/types/TypeIndex';

export class JobRepository {
  private storage: IStorage;

  constructor(storageInstance: IStorage) {
    this.storage = storageInstance;
  }

  /**
   * Almacena un job individualmente en el storage.
   */
  async saveJob(job: Job): Promise<void> {
    await this.storage.set<Job>(`${job.id}`, job);
  }

  /**
   * Obtiene todos los jobs almacenados y devuelve un resumen de cada uno.
   */
  async getJobSummaries(): Promise<JobSummary[]> {
    const keys = await this.storage.keys();
    
    // Usamos Promise.all para obtener todos los jobs concurrentemente.
    const jobPromises = keys.map(key => this.storage.get<Job>(key));
    const allJobs = await Promise.all(jobPromises);

    const summaries: JobSummary[] = [];

    // Filtro los valores nulos (en caso de error) y mapeo a JobSummary.
    for (const job of allJobs) {
      if (job) {
        summaries.push({
          id: job.id,
          state: job.state,
          worldName: job.worldName,
          createdAt: job.createdAt,
        });
      }
    }

    return summaries;
  }

    /**
     * Obtiene un job completo por su ID.
     * 
     * @param id - ID del job a obtener.
     */
    async getJobById(id: string): Promise<Job | null> {
        return await this.storage.get<Job>(id);
    }

    /**
     * Elimina un job por su ID.
     * 
     * @param id - ID del job a eliminar.
    */
    async deleteJobById(id: string): Promise<void> {
        await this.storage.remove(id);
    }

    /**
     * Elimina todos los jobs almacenados.
     * */
    async clearAllJobs(): Promise<void> {
        await this.storage.clear();
    }

}

// Exportar una instancia singleton
export const jobRepository = new JobRepository(storage);