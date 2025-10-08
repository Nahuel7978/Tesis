// src/features/jobs/hooks/useJobPolling.tsx
import { useState, useEffect, useCallback, useRef } from 'react';
import { jobsService } from '@/services/api/jobs';
import { jobRepository } from '@/services/storage/JobRepository';
import { JobState, Job } from '@/types/TypeIndex';

interface UseJobPollingReturn {
  isPolling: boolean;
  lastUpdate: Date | null;
  error: string | null;
}

export const useJobPolling = (jobs: Job[]): UseJobPollingReturn => {
  const [isPolling, setIsPolling] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const updateJobState = useCallback(async (jobId: string) => {
    try {
      setIsPolling(true);
      const statusResponse = await jobsService.getJobStatus(jobId);
      
      // Obtener el job completo del storage
      const job = await jobRepository.getJobById(jobId);
      
      if (job) {
        // Actualizar el estado del job
        const updatedJob: Job = {
          ...job,
          state: statusResponse.state
        };
        
        await jobRepository.saveJob(updatedJob);
        setLastUpdate(new Date());
        setError(null);
      }
    } catch (err) {
      console.error(`Error polling job ${jobId}:`, err);
      setError(`Error actualizando estado de ${jobId}`);
    } finally {
      setIsPolling(false);
    }
  }, []);

  const scheduleNextPoll = useCallback((jobId: string, state: JobState) => {
    // Limpiar timeout anterior si existe
    const existingTimeout = timeoutsRef.current.get(jobId);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Determinar intervalo según el estado
    // WAIT: 3 minutos (180000ms)
    // Otros estados: 10 minutos (600000ms)
    const interval = state === JobState.WAIT ? 18000 : 600000;

    // No hacer polling para estados terminales
    if (state === JobState.TERMINATED) {
      return;
    }

    const timeout = setTimeout(async () => {
      await updateJobState(jobId);
      
      // Re-agendar siguiente poll
      const updatedJob = await jobRepository.getJobById(jobId);
      if (updatedJob) {
        scheduleNextPoll(jobId, updatedJob.state);
      }
    }, interval);

    timeoutsRef.current.set(jobId, timeout);
  }, [updateJobState]);

  useEffect(() => {
    // Inicializar polling para cada job
    jobs.forEach(job => {
      scheduleNextPoll(job.id, job.state);
    });

    // Cleanup: limpiar todos los timeouts al desmontar
    return () => {
      timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      timeoutsRef.current.clear();
    };
  }, [jobs, scheduleNextPoll]);

  return {
    isPolling,
    lastUpdate,
    error
  };
};