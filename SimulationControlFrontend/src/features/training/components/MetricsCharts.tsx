import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrainingMetrics } from '@/types/TypeIndex';

interface MetricsChartsProps {
  metrics: TrainingMetrics[];
}

const MetricsCharts = ({ metrics }: MetricsChartsProps) => {
  // Procesar datos para los gráficos
  const chartData = useMemo(() => {
    return metrics.map((m) => ({
      timestep: m.total_timesteps,
      episodeLength: m.ep_len_mean,
      episodeReward: m.ep_rew_mean,
      explorationRate: m.exploration_rate,
      fps: m.fps
    }));
  }, [metrics]);

  // Obtener últimos valores
  const lastMetric = metrics[metrics.length - 1];

  if (metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">No hay métricas disponibles aún...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métricas Principales en Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"> {/* Muestra 2 en sm, 3 en lg */}
        <MetricCard
          title="Episode Length Mean"
          value={lastMetric?.ep_len_mean.toFixed(0) || '-'}
          subtitle="pasos"
          color="blue"
        />
        <MetricCard
          title="Episode Reward Mean"
          value={lastMetric?.ep_rew_mean?.toFixed(2) || '-'}
          subtitle="reward"
          color="green"
        />

      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-1 xl:grid-cols-2 gap-6"> {/* 1 columna en lg, 2 en xl */}
        {/* Episode Length */}
        <ChartCard title="Episode Length Mean">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="timestep" 
                stroke="#666"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #ccc',
                  borderRadius: '8px' 
                }}
              />
              <Line 
                type="monotone" 
                dataKey="episodeLength" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Episode Reward */}
        <ChartCard title="Episode Reward Mean">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="timestep" 
                stroke="#666"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #ccc',
                  borderRadius: '8px' 
                }}
              />
              <Line 
                type="monotone" 
                dataKey="episodeReward" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Info adicional */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Total Timesteps:</strong> {lastMetric?.total_timesteps.toLocaleString()} | 
          <strong> FPS:</strong> {lastMetric?.fps.toFixed(1)} | 
        </p>
      </div>
    </div>
  );
};

// Componente auxiliar para Cards de métricas
const MetricCard = ({ 
  title, 
  value, 
  subtitle, 
  color 
}: { 
  title: string; 
  value: string; 
  subtitle: string; 
  color: 'blue' | 'green' | 'orange'; 
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800',
  };

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6`}>
      <h3 className="text-sm font-medium mb-2">{title}</h3>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-sm mt-1 opacity-75">{subtitle}</p>
    </div>
  );
};

// Componente auxiliar para Cards de gráficos
const ChartCard = ({ 
  title, 
  children 
}: { 
  title: string; 
  children: React.ReactNode; 
}) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  );
};

export default MetricsCharts;