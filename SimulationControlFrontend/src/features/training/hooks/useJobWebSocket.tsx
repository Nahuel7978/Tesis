import { useEffect, useState, useCallback } from 'react';
import { TrainingMetrics, WebSocketState, JobState } from '@/types/TypeIndex';
import { jobWebSocketService } from '@/services/websocket/jobs_websocket';

interface UseJobWebSocketReturn {
  wsState: WebSocketState;
  connect: (jobId: string) => void;
  disconnect: () => void;
}

/**
 * Hook personalizado para manejar la conexión WebSocket de un job
 * @param onMetrics - Callback cuando llegan nuevas métricas
 * @param onStateChange - Callback cuando cambia el estado del job
 */
export const useJobWebSocket = (
  onMetrics: (metrics: TrainingMetrics) => void,
  onStateChange?: (state: JobState) => void
): UseJobWebSocketReturn => {
  const [wsState, setWsState] = useState<WebSocketState>(
    WebSocketState.DISCONNECTED
  );

  // Conectar al WebSocket
  const connect = useCallback((jobId: string) => {
    // Suscribirse a cambios de estado del WebSocket
    const unsubscribeStatus = jobWebSocketService.onStatusChange((state) => {
      setWsState(state);
    });

    // Suscribirse a mensajes
    const unsubscribeMessages = jobWebSocketService.onMessage((message) => {
      if ('total_timesteps' in message) {
        // Es una métrica
        onMetrics(message as TrainingMetrics);
      } else if ('type' in message && message.type === 'status') {
        // Es un cambio de estado del job
        if (onStateChange && 'state' in message) {
          onStateChange(message.state as JobState);
        }
      }
    });

    // Conectar
    jobWebSocketService.connect(jobId);

    // Guardar funciones de desuscripción
    return () => {
      unsubscribeStatus();
      unsubscribeMessages();
    };
  }, [onMetrics, onStateChange]);

  // Desconectar del WebSocket
  const disconnect = useCallback(() => {
    jobWebSocketService.disconnect();
    setWsState(WebSocketState.DISCONNECTED);
  }, []);

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    wsState,
    connect,
    disconnect,
  };
};

export default useJobWebSocket;