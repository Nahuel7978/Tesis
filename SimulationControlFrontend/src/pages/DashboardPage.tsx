// src/features/jobs/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { jobRepository } from '@/services/storage/JobRepository';
import { Job } from '@/types/TypeIndex';
import { JobStatsCards } from '../features/jobs/components/JobStatsCards';
import { JobCard } from '../features/jobs/components/JobCard';
import { useJobPolling } from '../features/jobs/hooks/useJobPolling';

export const Dashboard: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { lastUpdate } = useJobPolling(jobs);

  // Cargar jobs desde el storage
  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const summaries = await jobRepository.getJobSummaries();
      
      // Obtener los jobs completos
      const fullJobs = await Promise.all(
        summaries.map(summary => jobRepository.getJobById(summary.id))
      );
      
      // Filtrar nulls y ordenar por fecha de creación (más reciente primero)
      const validJobs = fullJobs
        .filter((job): job is Job => job !== null)
        .sort((a, b) => 
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
      
      setJobs(validJobs);
    } catch (err) {
      console.error('Error loading jobs:', err);
      setError('Error al cargar los entrenamientos');
    } finally {
      setLoading(false);
    }
  };

  // Cargar jobs al montar el componente
  useEffect(() => {
    loadJobs();
  }, []);

  // Recargar jobs cuando se actualice alguno (desde el polling)
  useEffect(() => {
    if (lastUpdate) {
      loadJobs();
    }
  }, [lastUpdate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-600">Cargando entrenamientos...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-red-800 font-semibold mb-2">Error</h3>
            <p className="text-red-600">{error}</p>
            <button 
              onClick={loadJobs}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Monitoreo de entrenamientos activos y completados</p>
        </div>

        {/* Stats Cards */}
        <JobStatsCards jobs={jobs} />

        {/* Jobs List */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Jobs de Entrenamiento
          </h2>

          {jobs.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-5xl mb-4">📦</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No hay entrenamientos
              </h3>
              <p className="text-gray-600 mb-6">
                Comienza creando un nuevo entrenamiento desde "Cargar Mundo"
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map(job => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </div>

        {/* Footer info */}
        {lastUpdate && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Última actualización: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};