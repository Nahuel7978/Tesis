import { useState, useEffect } from 'react';
import { AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { jobsService, jobWebSocketService } from '@/services/ServiceIndex';
import { jobRepository } from '@/services/storage/JobRepository';
import { 
  TrainingAlgorithm, 
  PolicyType, 
  TrainingMetrics, 
  WebSocketState,
  Job,
  JobSummary,
  JobState,
} from '@/types/TypeIndex';


export default function TestPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string>('');
  const [wsState, setWsState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [metrics, setMetrics] = useState<TrainingMetrics[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [storedJobs, setStoredJobs] = useState<JobSummary[]>([]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
    console.log(message);
  };

  // Cargar jobs almacenados
  const loadStoredJobs = async () => {
    try {
      addLog('📦 Loading stored jobs...');
      const summaries = await jobRepository.getJobSummaries();
      setStoredJobs(summaries);
      addLog(`📦 Loaded ${summaries.length} stored jobs`);
    } catch (error: any) {
      addLog(`❌ Error loading jobs: ${error.message || error}`);
    }
  };

  // Test 1: Crear Job
  const testCreateJob = async () => {
    if (!selectedFile) {
      addLog('❌ Error: Por favor, selecciona un archivo primero.');
      return;
    }
    try {
      addLog('🚀 Testing: Create Job');
      
      const dummyFile = selectedFile;

      const hparams = {
        def_robot: 'principal_robot',
        controller: 'robotController',
        env_class: 'RobotController',
        model: TrainingAlgorithm.DQN,
        policy: PolicyType.MlpPolicy,
        timesteps: 1000,
        model_params: {
          verbose: 2,
          learning_rate: 0.0003,
          batch_size: 64,
          gamma: 0.99,
          target_kl: 0.01
        }
      };

      const response = await jobsService.createJob(dummyFile, hparams);
      setCurrentJobId(response.job_id);
      addLog(`✅ Job created: ${response.job_id}`);
      addLog(`   Status: ${response.status}`);
      addLog(`   Message: ${response.message}`);

      // Guardar job en el repositorio
      const newJob: Job = {
        id: response.job_id,
        state: JobState.WAIT,
        worldName: "New World_"+response.job_id,
        hyperparameters: hparams,
        createdAt: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
      };

      
      await jobRepository.saveJob(newJob);
      addLog(`💾 Job saved to repository`);
      
      // Recargar lista de jobs
      await loadStoredJobs();
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  // Test 2: Obtener estado del Job
  const testGetStatus = async () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    try {
      addLog(`🔍 Testing: Get Job Status (${currentJobId})`);
      const status = await jobsService.getJobStatus(currentJobId);
      addLog(`✅ State: ${status.state}`);
      addLog(`   Init: ${status.init_timestamp}`);
      addLog(`   End: ${status.end_timestamp || 'N/A'}`);
      addLog(`   Errors: ${status.errors.length > 0 ? status.errors.join(', ') : 'None'}`);

      // Actualizar job en el repositorio
      const existingJob = await jobRepository.getJobById(currentJobId);
      if (existingJob) {
        const updatedJob: Job = {
          ...existingJob,
          state: status.state,
          lastUpdated: new Date().toISOString(),
          initTimestamp: status.init_timestamp,
          endTimestamp: status.end_timestamp,
          errors: status.errors,
        };
        await jobRepository.saveJob(updatedJob);
        addLog(`💾 Job status updated in repository`);
        await loadStoredJobs();
      }
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  // Test 3: Obtener métricas
  const testGetMetrics = async () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    try {
      addLog(`📊 Testing: Get Metrics History (${currentJobId})`);
      const metricsData = await jobsService.getMetricsHistory(currentJobId);
      addLog(`✅ Retrieved ${metricsData.length} metrics entries`);
      if (metricsData.length > 0) {
        const latest = metricsData[metricsData.length - 1];
        if (latest) {
          addLog(`   Latest: Episode ${latest.episodes}, Reward ${latest.ep_rew_mean.toFixed(2)}`);
        }
      }
      setMetrics(metricsData);
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  // Test 4: Conectar WebSocket
  const testConnectWebSocket = () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    addLog(`🔌 Testing: Connect WebSocket (${currentJobId})`);
    jobWebSocketService.connect(currentJobId);
  };

  // Test 5: Desconectar WebSocket
  const testDisconnectWebSocket = () => {
    addLog('🔌 Testing: Disconnect WebSocket');
    jobWebSocketService.disconnect();
  };

  // Test 6: Detener Job
  const testStopJob = async () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    try {
      addLog(`⏹️ Testing: Stop Job (${currentJobId})`);
      await jobsService.stopJob(currentJobId);
      addLog(`✅ Job stopped successfully`);
      
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  // Test 7: Descargar modelo
  const testDownloadModel = async () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    try {
      addLog(`💾 Testing: Download Model (${currentJobId})`);
      const blob = await jobsService.downloadModel(currentJobId);
      addLog(`✅ Model downloaded: ${(blob.size / 1024).toFixed(2)} KB`);
      jobsService.downloadBlob(blob, `model_${currentJobId}.zip`);
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  const testDownloadTensorboard = async () => {
    if (!currentJobId) {
      addLog('⚠️ No job ID. Create a job first.');
      return;
    }

    try {
      addLog(`💾 Testing: Download Tensorboard (${currentJobId})`);
      const blob = await jobsService.downloadTensorboard(currentJobId);
      addLog(`✅ Tensorboard downloaded: ${(blob.size / 1024).toFixed(2)} KB`);
      jobsService.downloadBlob(blob, `tensorBoard${currentJobId}.zip`);
    } catch (error: any) {
      addLog(`❌ Error: ${error.message || error}`);
    }
  };

  // Eliminar job del repositorio
  const deleteJobFromRepo = async (jobId: string) => {
    try {
      await jobRepository.deleteJobById(jobId);
      addLog(`🗑️ Job ${jobId} deleted from repository`);
      await loadStoredJobs();
    } catch (error: any) {
      addLog(`❌ Error deleting job: ${error.message || error}`);
    }
  };

  // Limpiar todos los jobs
  const clearAllJobs = async () => {
    try {
      await jobRepository.clearAllJobs();
      addLog(`🗑️ All jobs cleared from repository`);
      setStoredJobs([]);
    } catch (error: any) {
      addLog(`❌ Error clearing jobs: ${error.message || error}`);
    }
  };

  // Seleccionar job de la tabla
  const selectJobFromTable = (jobId: string) => {
    setCurrentJobId(jobId);
    addLog(`📋 Selected job: ${jobId}`);
  };

  // Setup WebSocket listeners
  useEffect(() => {
    const unsubscribeMessage = jobWebSocketService.onMessage((message) => {
      if ('type' in message && message.type === 'status') {
        addLog(`📡 WS Status: ${message.state} - ${message.message}`);
      } else if ('timestamp' in message) {
        const m = message as TrainingMetrics;
        addLog(`📡 WS Metrics: Episode ${m.episodes}, Timesteps ${m.total_timesteps}, Reward ${m.ep_rew_mean.toFixed(2)}`);
        setMetrics(prev => [...prev, m]);
      }
    });

    const unsubscribeStatus = jobWebSocketService.onStatusChange((state) => {
      setWsState(state);
      addLog(`🔌 WS State: ${state}`);
    });

    return () => {
      unsubscribeMessage();
      unsubscribeStatus();
    };
  }, []);

  // Cargar jobs al montar el componente
  useEffect(() => {
    loadStoredJobs();
  }, []);

  // Obtener color según el estado del job
  const getStateColor = (state: JobState) => {
    switch (state) {
      case JobState.WAIT: return 'text-yellow-400';
      case JobState.RUNNING: return 'text-blue-400';
      case JobState.READY: return 'text-green-400';
      case JobState.ERROR: return 'text-red-400';
      case JobState.TERMINATED: return 'text-gray-400';
      default: return 'text-white';
    }
  };

  return (
    
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">API Services Test Page</h1>

        {/* Stored Jobs Table */} 
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Stored Jobs ({storedJobs.length})</h2>
            <div className="flex gap-2">
              <button
                onClick={loadStoredJobs}
                className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition"
              >
                🔄 Refresh
              </button>
              <button
                onClick={clearAllJobs}
                className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm transition"
                disabled={storedJobs.length === 0}
              >
                🗑️ Clear All
              </button>
            </div>
          </div>
          
          {storedJobs.length === 0 ? (
            <div className="bg-gray-700 rounded p-4 text-center text-gray-400">
              No stored jobs. Create one to get started!
            </div>
          ) : (
            <div className="bg-black rounded overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="text-left p-3">Job ID</th>
                    <th className="text-left p-3">State</th>
                    <th className="text-left p-3">World Name</th>
                    <th className="text-left p-3">Created At</th>
                    <th className="text-left p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {storedJobs.map((job) => (
                    <tr 
                      key={job.id} 
                      className={`border-b border-gray-800 hover:bg-gray-700 transition ${
                        currentJobId === job.id ? 'bg-gray-700' : ''
                      }`}
                    >
                      <td className="p-3 font-mono text-xs">{job.id}</td>
                      <td className={`p-3 font-semibold ${getStateColor(job.state)}`}>
                        {job.state}
                      </td>
                      <td className="p-3">{job.worldName}</td>
                      <td className="p-3 text-gray-400 text-xs">
                        {new Date(job.createdAt).toLocaleString()}
                      </td>
                      <td className="p-3">
                        <button
                          onClick={() => selectJobFromTable(job.id)}
                          className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs mr-2 transition"
                        >
                          Select
                        </button>
                        <button
                          onClick={() => deleteJobFromRepo(job.id)}
                          className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs transition"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Control Panel */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Controls</h2>
          <div className="mb-4">
            <h3 className="mb-2">Paso 1: Seleccionar Archivo (Mundo/Modelo)</h3>
            <input 
              type="file" 
              accept=".zip, .tar.gz"
              onChange={(e) => {
                setSelectedFile(e.target.files?.[0] || null);
              }}
              className="bg-gray-700 text-white p-2 rounded w-full"
            />
            <p className="text-sm text-gray-400 mt-1">
              Archivo seleccionado: {selectedFile ? selectedFile.name : 'Ninguno'}
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <button
              onClick={testCreateJob}
              disabled={!selectedFile}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              1. Create Job
            </button>
            <button
              onClick={testGetStatus}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId}
            >
              2. Get Status
            </button>
            <button
              onClick={testGetMetrics}
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId}
            >
              3. Get Metrics
            </button>
            <button
              onClick={testConnectWebSocket}
              className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId || wsState === WebSocketState.CONNECTED}
            >
              4. Connect WS
            </button>
            <button
              onClick={testDisconnectWebSocket}
              className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={wsState === WebSocketState.DISCONNECTED}
            >
              5. Disconnect WS
            </button>
            <button
              onClick={testStopJob}
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId}
            >
              6. Stop Job
            </button>
            <button
              onClick={testDownloadModel}
              className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId}
            >
              7. Download Model
            </button>
            <button
              onClick={testDownloadTensorboard}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentJobId}
            >
              8. Download TB
            </button>
            <button
              onClick={() => setLogs([])}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded transition"
            >
              Clear Logs
            </button>
          </div>

          {/* Status Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-700 p-3 rounded">
              <span className="text-gray-400">Current Job ID:</span>
              <div className="font-mono text-green-400">{currentJobId || 'None'}</div>
            </div>
            <div className="bg-gray-700 p-3 rounded">
              <span className="text-gray-400">WebSocket State:</span>
              <div className={`font-semibold ${
                wsState === WebSocketState.CONNECTED ? 'text-green-400' : 
                wsState === WebSocketState.ERROR ? 'text-red-400' : 
                'text-yellow-400'
              }`}>
                {wsState}
              </div>
            </div>
          </div>
        </div>

        {/* Logs Panel */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Logs</h2>
          <div className="bg-black rounded p-4 h-64 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-500">No logs yet. Click a test button to start.</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="mb-1 text-green-400">{log}</div>
              ))
            )}
          </div>
        </div>

        {/* Metrics Display */}
        {metrics.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              Metrics ({metrics.length} entries)
            </h2>
            <div className="bg-black rounded p-4 h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="text-left p-2">Episode</th>
                    <th className="text-left p-2">Timesteps</th>
                    <th className="text-left p-2">Reward</th>
                    <th className="text-left p-2">Length</th>
                    <th className="text-left p-2">FPS</th>
                    <th className="text-left p-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m, i) => (
                    <tr key={i} className="border-b border-gray-800 hover:bg-gray-700">
                      <td className="p-2">{m.episodes}</td>
                      <td className="p-2">{m.total_timesteps}</td>
                      <td className="p-2 text-green-400">{m.ep_rew_mean.toFixed(2)}</td>
                      <td className="p-2">{m.ep_len_mean.toFixed(2)}</td>
                      <td className="p-2">{m.fps}</td>
                      <td className="p-2 text-gray-400 text-xs">
                        {new Date(m.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}