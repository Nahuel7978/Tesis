import { Job } from '@/types/TypeIndex';

interface JobInfoSectionProps {
  job: Job;
}

const JobInfoSection = ({ job }: JobInfoSectionProps) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        Información del Entrenamiento
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Información General */}
        <div className="space-y-4">
          <div className="border-b pb-4">
            <h3 className="text-sm font-semibold text-gray-600 uppercase mb-3">
              Información General
            </h3>
            <div className="space-y-2">
              <InfoRow label="Job ID" value={job.id} />
              <InfoRow label="Nombre del Mundo" value={job.worldName} />
              <InfoRow label="Robot" value={job.hyperparameters.def_robot || 'No especificado'} />
              <InfoRow 
                label="Creado" 
                value={new Date(job.createdAt).toLocaleString('es-AR')} 
              />
              {job.lastUpdated && (
                <InfoRow 
                  label="Última Actualización" 
                  value={new Date(job.lastUpdated).toLocaleString('es-AR')} 
                />
              )}
            </div>
          </div>

          {/* Algoritmo */}
          <div>
            <h3 className="text-sm font-semibold text-gray-600 uppercase mb-3">
              Algoritmo
            </h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-lg font-semibold text-blue-900">
                {job.hyperparameters.model || 'DQN'}
              </p>
            </div>
          </div>
        </div>

        {/* Hiperparámetros */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase mb-3">
            Hiperparámetros
          </h3>
          {job.hyperparameters ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2 max-h-96 overflow-y-auto">
              {Object.entries(job.hyperparameters).map(([key, value]) => (
                <HyperparamRow 
                  key={key} 
                  param={key} 
                  value={formatHyperparamValue(value)} 
                />
              ))}
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-gray-500 text-sm">
                No hay hiperparámetros configurados
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Componente auxiliar para filas de información
const InfoRow = ({ label, value }: { label: string; value: string }) => {
  return (
    <div className="flex justify-between items-start">
      <span className="text-sm text-gray-600 font-medium">{label}:</span>
      <span className="text-sm text-gray-900 text-right ml-4">{value}</span>
    </div>
  );
};

// Componente auxiliar para hiperparámetros
const HyperparamRow = ({ param, value }: { param: string; value: string }) => {
  return (
    <div className="flex justify-between items-start py-1 border-b border-gray-200 last:border-b-0">
      <span className="text-sm text-gray-700 font-mono">{param}</span>
      <span className="text-sm text-gray-900 font-semibold ml-4">{value}</span>
    </div>
  );
};

// Función auxiliar para formatear valores de hiperparámetros
const formatHyperparamValue = (value: any): string => {
  if (value === null || value === undefined) {
    return 'null';
  }
  
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }
  
  if (typeof value === 'number') {
    // Formatear números grandes con separadores
    if (Math.abs(value) >= 1000) {
      return value.toLocaleString('es-AR');
    }
    // Formatear números decimales pequeños
    if (value !== 0 && Math.abs(value) < 0.01) {
      return value.toExponential(2);
    }
    return value.toString();
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  
  return String(value);
};

export default JobInfoSection;