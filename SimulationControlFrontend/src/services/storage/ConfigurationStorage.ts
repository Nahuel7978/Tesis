import { storage } from './TauriStorage';

/**
 * Configuración de la API que se persiste localmente
 */
export interface ApiConfiguration {
  httpBaseUrl: string;
  wsBaseUrl: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  wsReconnectAttempts?: number;
  wsReconnectDelay?: number;
  wsHeartbeatInterval?: number;
}

/**
 * Configuración por defecto
 */
const DEFAULT_API_CONFIG: ApiConfiguration = {
  httpBaseUrl: 'http://localhost:8000/SimulationControlApi/v1',
  wsBaseUrl: 'ws://localhost:8000/SimulationControlApi/ws/v1',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  wsReconnectAttempts: 5,
  wsReconnectDelay: 3000,
  wsHeartbeatInterval: 30000,
};

const CONFIG_STORAGE_KEY = 'api_configuration';

/**
 * Servicio para gestionar la configuración de la API
 * Proporciona persistencia y validación de configuración
 */
export class ConfigurationStorage {
  /**
   * Obtiene la configuración almacenada o devuelve la configuración por defecto
   */
  async getConfiguration(): Promise<ApiConfiguration> {
    try {
      const stored = await storage.get<ApiConfiguration>(CONFIG_STORAGE_KEY);
      
      if (stored) {
        console.log('[ConfigStorage] Loaded configuration:', stored);
        // Merge con defaults para asegurar todos los campos
        return { ...DEFAULT_API_CONFIG, ...stored };
      }
      
      console.log('[ConfigStorage] No configuration found, using defaults');
      return DEFAULT_API_CONFIG;
    } catch (error) {
      console.error('[ConfigStorage] Error loading configuration:', error);
      return DEFAULT_API_CONFIG;
    }
  }

  /**
   * Guarda la configuración
   */
  async saveConfiguration(config: Partial<ApiConfiguration>): Promise<void> {
    try {
      const current = await this.getConfiguration();
      const updated = { ...current, ...config };
      
      // Validar URLs antes de guardar
      this.validateConfiguration(updated);
      
      await storage.set(CONFIG_STORAGE_KEY, updated);
      console.log('[ConfigStorage] Configuration saved:', updated);
    } catch (error) {
      console.error('[ConfigStorage] Error saving configuration:', error);
      throw error;
    }
  }

  /**
   * Actualiza solo la URL base HTTP
   */
  async updateHttpBaseUrl(url: string): Promise<void> {
    const normalized = this.normalizeHttpUrl(url);
    await this.saveConfiguration({ httpBaseUrl: normalized });
  }

  /**
   * Actualiza solo la URL base WebSocket
   */
  async updateWsBaseUrl(url: string): Promise<void> {
    const normalized = this.normalizeWsUrl(url);
    await this.saveConfiguration({ wsBaseUrl: normalized });
  }

  /**
   * Actualiza ambas URLs basándose en una dirección IP base
   * Ejemplo: "192.168.1.100:8000" -> http://192.168.1.100:8000/SimulationControlApi/v1
   */
  async updateFromBaseAddress(address: string): Promise<void> {
    const cleanAddress = address.trim();
    
    // Remover protocolo si existe
    let baseAddr = cleanAddress.replace(/^(http:\/\/|https:\/\/|ws:\/\/|wss:\/\/)/, '');
    
    // Asegurar que tenga puerto, si no, agregar 8000
    if (!baseAddr.includes(':')) {
      baseAddr = `${baseAddr}:8000`;
    }
    
    const httpUrl = `http://${baseAddr}/SimulationControlApi/v1`;
    const wsUrl = `ws://${baseAddr}/SimulationControlApi/ws/v1`;
    
    await this.saveConfiguration({
      httpBaseUrl: httpUrl,
      wsBaseUrl: wsUrl,
    });
  }

  /**
   * Resetea la configuración a valores por defecto
   */
  async resetToDefaults(): Promise<void> {
    await storage.set(CONFIG_STORAGE_KEY, DEFAULT_API_CONFIG);
    console.log('[ConfigStorage] Configuration reset to defaults');
  }

  /**
   * Valida que la configuración sea correcta
   */
  private validateConfiguration(config: ApiConfiguration): void {
    if (!config.httpBaseUrl || !this.isValidUrl(config.httpBaseUrl)) {
      throw new Error('Invalid HTTP base URL');
    }
    
    if (!config.wsBaseUrl || !this.isValidWsUrl(config.wsBaseUrl)) {
      throw new Error('Invalid WebSocket base URL');
    }
    
    if (config.timeout && config.timeout < 1000) {
      throw new Error('Timeout must be at least 1000ms');
    }
  }

  /**
   * Valida si es una URL HTTP válida
   */
  private isValidUrl(url: string): boolean {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
      return false;
    }
  }

  /**
   * Valida si es una URL WebSocket válida
   */
  private isValidWsUrl(url: string): boolean {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'ws:' || parsed.protocol === 'wss:';
    } catch {
      return false;
    }
  }

  /**
   * Normaliza una URL HTTP
   */
  private normalizeHttpUrl(url: string): string {
    let normalized = url.trim();
    
    if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
      normalized = `http://${normalized}`;
    }
    
    return normalized;
  }

  /**
   * Normaliza una URL WebSocket
   */
  private normalizeWsUrl(url: string): string {
    let normalized = url.trim();
    
    if (!normalized.startsWith('ws://') && !normalized.startsWith('wss://')) {
      normalized = `ws://${normalized}`;
    }
    
    return normalized;
  }

  /**
   * Extrae la dirección base (IP:puerto) de las URLs configuradas
   */
  async getBaseAddress(): Promise<string> {
    const config = await this.getConfiguration();
    try {
      const parsed = new URL(config.httpBaseUrl);
      return parsed.host; // Devuelve "ip:puerto"
    } catch {
      return 'localhost:8000';
    }
  }
}

// Singleton
export const configurationStorage = new ConfigurationStorage();