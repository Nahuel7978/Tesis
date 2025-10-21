import { apiClient } from './api/client';
import { jobWebSocketService } from './websocket/jobs_websocket';
import { configurationStorage } from './storage/ConfigurationStorage';

/**
 * Inicializador de servicios
 * Carga la configuración almacenada y actualiza los servicios al inicio de la aplicación
 */
export class ServiceInitializer {
  private static initialized = false;

  /**
   * Inicializa todos los servicios con la configuración almacenada
   * Debe llamarse una sola vez al inicio de la aplicación
   */
  static async initialize(): Promise<void> {
    if (this.initialized) {
      console.log('[ServiceInitializer] Already initialized');
      return;
    }

    console.log('[ServiceInitializer] Initializing services...');

    try {
      // Cargar configuración almacenada
      const config = await configurationStorage.getConfiguration();
      console.log('[ServiceInitializer] Configuration loaded:', config);

      // Actualizar ApiClient
      apiClient.updateConfig({
        baseUrl: config.httpBaseUrl,
        timeout: config.timeout || 30000,
        retryAttempts: config.retryAttempts || 3,
        retryDelay: config.retryDelay || 1000,
      });

      // Actualizar JobWebSocketService
      // El WebSocket se inicializará cuando se conecte a un job específico
      // Solo necesitamos asegurarnos de que tiene la configuración correcta

      console.log('[ServiceInitializer] Services initialized successfully');
      this.initialized = true;
    } catch (error) {
      console.error('[ServiceInitializer] Error initializing services:', error);
      // Continuar con valores por defecto
      this.initialized = true;
    }
  }

  /**
   * Verifica si los servicios han sido inicializados
   */
  static isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Fuerza una reinicialización (útil para testing o casos especiales)
   */
  static async reinitialize(): Promise<void> {
    this.initialized = false;
    await this.initialize();
  }
}

/**
 * Hook de inicialización que se puede usar en el componente raíz
 * Inicializa los servicios automáticamente
 */
export const initializeServices = async (): Promise<void> => {
  await ServiceInitializer.initialize();
};
