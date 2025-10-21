import {
    WebSocketConfig,
    WebSocketState,
    WebSocketStatusMessage,
    TrainingMetrics,
    WebSocketMessageType
  } from '@/types/TypeIndex';
import { configurationStorage } from '../storage/ConfigurationStorage';
  
  type MessageCallback = (message: TrainingMetrics | WebSocketStatusMessage) => void;
  type StatusCallback = (state: WebSocketState) => void;
  
  const DEFAULT_WS_CONFIG: WebSocketConfig = {
    url:'ws://localhost:8000/SimulationControlApi/ws/v1',
    reconnectAttempts: 5,
    reconnectDelay: 3000,
    heartbeatInterval: 30000
  };
  
  export class JobWebSocketService {
    private ws: WebSocket | null = null;
    private config: WebSocketConfig;
    private currentJobId: string | null = null;
    private state: WebSocketState = WebSocketState.DISCONNECTED;
    
    // Subscribers
    private messageCallbacks: Set<MessageCallback> = new Set();
    private statusCallbacks: Set<StatusCallback> = new Set();
    
    // Reconnection
    private reconnectAttempt: number = 0;
    private reconnectTimeout: number | null = null;
    private heartbeatInterval: number | null = null;
  
    constructor(config: Partial<WebSocketConfig> = {}) {
      this.config = { ...DEFAULT_WS_CONFIG, ...config };
      try{
        // Cargar configuración almacenada
        configurationStorage.getConfiguration().then(storedConfig => {
          this.config.url = storedConfig.wsBaseUrl;
        }) 
      }catch(error){
        console.log("Error loading stored configuration for WebSocketService, using default URL");
        this.config = { ...DEFAULT_WS_CONFIG, ...config };
      }
    }
  
    /**
     * Conecta al WebSocket de un job específico
     */
    connect(jobId: string): void {
      if (this.ws?.readyState === WebSocket.OPEN && this.currentJobId === jobId) {
        console.log(`[WebSocket] Already connected to ${jobId}`);
        return;
      }
  
      this.disconnect();
      this.currentJobId = jobId;
      this.reconnectAttempt = 0;
      this.createConnection();
    }
  
    /**
     * Desconecta el WebSocket actual
     */
    disconnect(): void {
      this.clearReconnectTimeout();
      this.clearHeartbeat();
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.currentJobId = null;
      this.updateState(WebSocketState.DISCONNECTED);
    }
  
    /**
     * Suscribe un callback para recibir mensajes
     * @returns Función para desuscribirse
     */
    onMessage(callback: MessageCallback): () => void {
      this.messageCallbacks.add(callback);
      return () => this.messageCallbacks.delete(callback);
    }
  
    /**
     * Suscribe un callback para cambios de estado
     * @returns Función para desuscribirse
     */
    onStatusChange(callback: StatusCallback): () => void {
      this.statusCallbacks.add(callback);
      return () => this.statusCallbacks.delete(callback);
    }
  
    /**
     * Obtiene el estado actual
     */
    getState(): WebSocketState {
      return this.state;
    }
  
    /**
     * Obtiene el job ID actual
     */
    getCurrentJobId(): string | null {
      return this.currentJobId;
    }
  
    // Private methods
  
    private createConnection(): void {
      if (!this.currentJobId) {
        console.error('[WebSocket] No job ID specified');
        return;
      }
  
      const url = `${this.config.url}/jobs/${this.currentJobId}/metrics/stream`;
      console.log(`[WebSocket] Connecting to ${url}`);
      
      this.updateState(WebSocketState.CONNECTING);
  
      try {
        this.ws = new WebSocket(url, this.config.protocols);
        this.setupEventHandlers();
      } catch (error) {
        console.error('[WebSocket] Connection error:', error);
        this.updateState(WebSocketState.ERROR);
        this.scheduleReconnect();
      }
    }
  
    private setupEventHandlers(): void {
      if (!this.ws) return;
  
      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.updateState(WebSocketState.CONNECTED);
        this.reconnectAttempt = 0;
        this.startHeartbeat();
      };
  
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };
  
      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        this.updateState(WebSocketState.ERROR);
      };
  
      this.ws.onclose = (event) => {
        console.log('[WebSocket] Closed:', event.code, event.reason);
        this.clearHeartbeat();
        this.updateState(WebSocketState.DISCONNECTED);
        
        // Reconectar si no fue cierre intencional
        if (event.code !== 1000 && this.currentJobId) {
          this.scheduleReconnect();
        }
      };
    }
  
    private handleMessage(data: any): void {
      // Detectar tipo de mensaje
      if (data.type === WebSocketMessageType.STATUS) {
        console.log('[WebSocket] Status update:', data);
        const statusMessage: WebSocketStatusMessage = data;
        this.notifyMessageCallbacks(statusMessage);
      } else if (data.timestamp && data.total_timesteps !== undefined) {
        // Es una métrica (tiene campos específicos)
        console.log('[WebSocket] Metrics update:', data.total_timesteps);
        const metrics: TrainingMetrics = data;
        this.notifyMessageCallbacks(metrics);
      } else {
        console.warn('[WebSocket] Unknown message type:', data);
      }
    }
  
    private notifyMessageCallbacks(message: TrainingMetrics | WebSocketStatusMessage): void {
      this.messageCallbacks.forEach(callback => {
        try {
          callback(message);
        } catch (error) {
          console.error('[WebSocket] Error in message callback:', error);
        }
      });
    }
  
    private updateState(newState: WebSocketState): void {
      if (this.state === newState) return;
      
      this.state = newState;
      console.log(`[WebSocket] State changed to: ${newState}`);
      
      this.statusCallbacks.forEach(callback => {
        try {
          callback(newState);
        } catch (error) {
          console.error('[WebSocket] Error in status callback:', error);
        }
      });
    }
  
    private scheduleReconnect(): void {
      if (this.reconnectAttempt >= this.config.reconnectAttempts) {
        console.error('[WebSocket] Max reconnection attempts reached');
        this.updateState(WebSocketState.ERROR);
        return;
      }
  
      this.reconnectAttempt++;
      const delay = this.config.reconnectDelay * this.reconnectAttempt;
      
      console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt}/${this.config.reconnectAttempts})`);
      
      this.reconnectTimeout = window.setTimeout(() => {
        this.createConnection();
      }, delay);
    }
  
    private clearReconnectTimeout(): void {
      if (this.reconnectTimeout !== null) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    }
  
    private startHeartbeat(): void {
      this.heartbeatInterval = window.setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, this.config.heartbeatInterval);
    }
  
    private clearHeartbeat(): void {
      if (this.heartbeatInterval !== null) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
    }
  }
  
  // Singleton instance
  export const jobWebSocketService = new JobWebSocketService();
  export default jobWebSocketService;