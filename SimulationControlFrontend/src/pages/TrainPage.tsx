import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Job, JobState, TrainingMetrics } from '@/types/TypeIndex';
import { jobRepository } from '@/services/storage/JobRepository';
import { jobsService } from '@/services/api/jobs';
import { useJobWebSocket } from '@/features/training/hooks/useJobWebSocket';
import JobStateDisplay from '@/features/training/components/JobStateDisplay';
import MetricsCharts from '@/features/training/components/MetricsCharts';
import JobActions from '@/features/training/components/JobActions';
import JobInfoSection from '@/features/training/components/JobInfoSection';
import LoadingSpinner from '@/components/ui/LoandingSpinner';
import ErrorDisplay from '@/components/ui/ErrorDisplay';

const TrainPage = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  // Estado principal
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Métricas
  const [metricsHistory, setMetricsHistory] = useState<TrainingMetrics[]>([]);
  const [isStopping, setIsStopping] = useState(false);

  // WebSocket - manejado por el hook personalizado
  const { wsState, connect: connectWebSocket, disconnect: disconnectWebSocket } = useJobWebSocket(
    // Callback para nuevas métricas
    useCallback((newMetric: TrainingMetrics) => {
      setMetricsHistory((prev) => [...prev, newMetric]);
    }, []),
    // Callback para cambio de estado del job
    useCallback((newState: JobState) => {
      handleJobStateChange(newState);
    }, [])
  );

  // ==================== EFECTOS ====================

  // Cargar job al montar
  useEffect(() => {
    if (!jobId) {
      setError('No se especificó un ID de job válido');
      setLoading(false);
      return;
    }

    loadJobData(jobId);

    // Cleanup
    return () => {
      disconnectWebSocket();
    };
  }, [jobId]);

  // Manejar cambios de estado del job
  useEffect(() => {
    if (!job || !jobId) return;

    switch (job.state) {
      case JobState.RUNNING:
        setupRunningJob(jobId);
        break;
      case JobState.READY:
      case JobState.ERROR:
      case JobState.TERMINATED:
        loadMetricsOnly(jobId);
        break;
      default:
        // WAIT, CANCELLED - no hay métricas
        break;
    }
  }, [job?.state, jobId]);

  // ==================== FUNCIONES DE CARGA ====================

  /**
   * Carga inicial del job desde storage y API
   */
  const loadJobData = async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      // 1. Buscar en storage local
      const localJob = await jobRepository.getJobById(id);
      
      if (!localJob) {
        setError(`No se encontró información para el job ${id}`);
        setLoading(false);
        return;
      }

      setJob(localJob);

      // 2. Actualizar estado desde API
      try {
        const apiStatus = await jobsService.getJobStatus(id);
        
        // Actualizar job con el estado más reciente
        const updatedJob: Job = {
          ...localJob,
          state: apiStatus.state as JobState,
          lastUpdated: new Date().toISOString(),
        };

        setJob(updatedJob);
        await jobRepository.saveJob(updatedJob);
      } catch (apiError) {
        console.warn('[TrainPage] Error al obtener estado desde API:', apiError);
        // Continuar con datos locales
      }

      setLoading(false);
    } catch (err) {
      console.error('[TrainPage] Error cargando job:', err);
      setError('Error al cargar la información del job');
      setLoading(false);
    }
  };

  /**
   * Configura job en ejecución: carga historial + conecta WebSocket
   */
  const setupRunningJob = async (id: string) => {
    try {
      // Cargar historial de métricas
      const history = await jobsService.getMetricsHistory(id);
      setMetricsHistory(history);

      // Conectar WebSocket
      connectWebSocket(id);
    } catch (err) {
      console.error('[TrainPage] Error configurando job en ejecución:', err);
    }
  };

  /**
   * Solo carga métricas (para READY, ERROR, TERMINATED)
   */
  const loadMetricsOnly = async (id: string) => {
    try {
      const history = await jobsService.getMetricsHistory(id);
      setMetricsHistory(history);
    } catch (err) {
      console.error('[TrainPage] Error cargando métricas:', err);
    }
  };

  /**
   * Maneja cambios de estado recibidos por WebSocket
   */
  const handleJobStateChange = async (newState: JobState) => {
    if (!job) return;

    const updatedJob: Job = {
      ...job,
      state: newState,
      lastUpdated: new Date().toISOString(),
    };

    setJob(updatedJob);
    await jobRepository.saveJob(updatedJob);

    // Si cambió a READY o ERROR, desconectar WebSocket
    if (newState === JobState.READY || newState === JobState.ERROR) {
      disconnectWebSocket();
    }
  };

  // ==================== ACCIONES DEL USUARIO ====================

  /**
   * Detener entrenamiento
   */
  const handleStopTraining = async () => {
    if (!jobId || !job) return;

    const confirmed = window.confirm(
      '¿Estás seguro de que deseas detener este entrenamiento? Esta acción no se puede deshacer.'
    );

    if (!confirmed) return;

    try {
      setIsStopping(true);
      await jobsService.stopJob(jobId);

      // Actualizar estado local
      const updatedJob: Job = {
        ...job,
        state: JobState.CANCELLED,
        lastUpdated: new Date().toISOString(),
      };

      setJob(updatedJob);
      await jobRepository.saveJob(updatedJob);

      // Desconectar WebSocket
      disconnectWebSocket();
    } catch (err) {
      console.error('[TrainPage] Error deteniendo job:', err);
      alert('Error al detener el entrenamiento. Intenta nuevamente.');
    } finally {
      setIsStopping(false);
    }
  };

  /**
   * Descargar modelo entrenado
   */
  const handleDownloadModel = async () => {
    if (!jobId) return;

    try {
      const blob = await jobsService.downloadModel(jobId);
      jobsService.downloadBlob(blob, `${jobId}_model.zip`);
    } catch (err: any) {
      console.error('[TrainPage] Error descargando modelo:', err);
      
      const errorMessage = err?.response?.data?.message || err?.message || '';
      
      if (errorMessage.toLowerCase().includes('checkpoint')) {
        alert(
          'El modelo completo no está disponible. Se descargará un checkpoint del último estado guardado.'
        );
      } else {
        alert('Aún no hay un modelo entrenado disponible para descargar.');
      }
    }
  };

  /**
   * Descargar Tensorboard
   */
  const handleDownloadTensorboard = async () => {
    if (!jobId) return;

    try {
      const blob = await jobsService.downloadTensorboard(jobId);
      jobsService.downloadBlob(blob, `${jobId}_tensorboard.zip`);
    } catch (err) {
      console.error('[TrainPage] Error descargando tensorboard:', err);
      alert('Error al descargar Tensorboard. Por favor, intenta más tarde.');
    }
  };

  /**
   * Descargar checkpoint (para jobs con ERROR)
   */
  const handleDownloadCheckpoint = async () => {
    if (!jobId) return;

    try {
      const blob = await jobsService.downloadModel(jobId);
      jobsService.downloadBlob(blob, `${jobId}_checkpoint.zip`);
    } catch (err) {
      console.error('[TrainPage] Error descargando checkpoint:', err);
      alert('Error al descargar el checkpoint. Al haber habido un error es posible que no exista un checkpoint disponible.');
    }
  };

  /**
   * Eliminar job del storage local
   */
  const handleDeleteJob = async () => {
    if (!jobId || !job) return;

    const confirmed = window.confirm(
      '¿Deseas eliminar este job de tu historial local? Esta acción no se puede deshacer.'
    );

    if (!confirmed) return;

    try {
      await jobRepository.deleteJobById(jobId);
      navigate('/dashboard');
    } catch (err) {
      console.error('[TrainPage] Error eliminando job:', err);
      alert('Error al eliminar el job. Intenta nuevamente.');
    }
  };

  // ==================== RENDERIZADO ====================

  if (loading) {
    return <LoadingSpinner message="Cargando información del entrenamiento..." />;
  }

  if (error || !job) {
    return <ErrorDisplay message={error || 'Job no encontrado'} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-6 md:px-8">
      <div className="max-w-6xl mx-auto space-y-6"> 
       {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 md:gap-0"> {/* Flex-col en móvil, flex-row en md+ */}
          <div className="text-center md:text-left">
            <h1 className="text-3xl font-bold text-gray-900">{job.worldName}</h1>
            <p className="text-gray-600 mt-1">
              Iniciado: {new Date(job.createdAt).toLocaleString('es-AR')}
            </p>
          </div>
          <JobStateDisplay state={job.state} wsState={wsState} />
        </div>

        {/* Contenido basado en estado */}
        <div className="space-y-6">
          {/* Gráficos de métricas */}
          {(job.state === JobState.RUNNING || 
            job.state === JobState.READY || 
            job.state === JobState.ERROR ||
            job.state === JobState.TERMINATED) && 
            metricsHistory.length > 0 && (
            <MetricsCharts metrics={metricsHistory} />
          )}

          {/* Acciones */}
          <JobActions
            job={job}
            isStopping={isStopping}
            onStopTraining={handleStopTraining}
            onDownloadModel={handleDownloadModel}
            onDownloadTensorboard={handleDownloadTensorboard}
            onDownloadCheckpoint={handleDownloadCheckpoint}
            onDeleteJob={handleDeleteJob}
          />

          {/* Información del entrenamiento */}
          <JobInfoSection job={job} />
        </div>
      </div>
    </div>
  );
};

export default TrainPage;