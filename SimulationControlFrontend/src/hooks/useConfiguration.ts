import { useState, useEffect, useCallback } from 'react';
import { configurationStorage, ApiConfiguration } from '@/services/storage/ConfigurationStorage';
import { apiClient } from '@/services/api/client';
import { jobWebSocketService } from '@/services/websocket/jobs_websocket';

interface UseConfigurationReturn {
  configuration: ApiConfiguration | null;
  httpBaseUrl: string;
  wsBaseUrl: string;
  loading: boolean;
  error: string | null;
  saveConfiguration: (config: Partial<ApiConfiguration>) => Promise<void>;
  updateAddressHttp: (address: string) => Promise<void>;
  updateAddressWs: (address: string) => Promise<void>;
  resetToDefaults: () => Promise<void>;
  testConnectionHTTP: () => Promise<boolean>;
}

/**
 * Hook para gestionar la configuración de la API
 * Proporciona funciones para cargar, guardar y actualizar la configuración
 */
export const useConfiguration = (): UseConfigurationReturn => {
  const [configuration, setConfiguration] = useState<ApiConfiguration | null>(null);
  const [baseAddressHttp, setBaseAddressHttp] = useState<string>('');
  const [baseAddressWs, setBaseAddressWs] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Carga la configuración al montar el componente
   */
  useEffect(() => {
    loadConfiguration();
  }, []);

  /**
   * Carga la configuración desde el storage
   */
  const loadConfiguration = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const config = await configurationStorage.getConfiguration();
      
      setConfiguration(config);
      setBaseAddressHttp(config.httpBaseUrl);
      setBaseAddressWs(config.wsBaseUrl);
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido';
      setError(message);
      console.error('[useConfiguration] Error loading configuration:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Guarda la configuración y actualiza los servicios
   */
  const saveConfiguration = useCallback(async (config: Partial<ApiConfiguration>) => {
    setLoading(true);
    setError(null);
    
    try {
      await configurationStorage.saveConfiguration(config);
      
      // Recargar configuración
      const updated = await configurationStorage.getConfiguration();
      setConfiguration(updated);
      
      // Actualizar servicios con nueva configuración
      updateServices(updated);
      
      console.log('[useConfiguration] Configuration saved and services updated');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar configuración';
      setError(message);
      console.error('[useConfiguration] Error saving configuration:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Actualiza la dirección(IP:puerto) http 
   */
  const updateAddressHttp = useCallback(async (address: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await configurationStorage.updateHttpBaseUrl(address);
      
      // Recargar configuración
      const updated = await configurationStorage.getConfiguration();
      
      setConfiguration(updated);
      updateServices(updated);
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al actualizar dirección';
      setError(message);
      console.error('[useConfiguration] Error updating base address:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Actualiza la dirección(IP:puerto) ws
   */
  const updateAddressWs = useCallback(async (address: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await configurationStorage.updateWsBaseUrl(address);
      
      // Recargar configuración
      const updated = await configurationStorage.getConfiguration();
      
      setConfiguration(updated);
      updateServices(updated);
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al actualizar dirección';
      setError(message);
      console.error('[useConfiguration] Error updating base address:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Resetea la configuración a valores por defecto
   */
  const resetToDefaults = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      await configurationStorage.resetToDefaults();
      
      // Recargar configuración
      const config = await configurationStorage.getConfiguration();
      
      setConfiguration(config);
      setBaseAddressHttp(config.httpBaseUrl);
      setBaseAddressWs(config.wsBaseUrl);
      
      // Actualizar servicios
      updateServices(config);
      
      console.log('[useConfiguration] Configuration reset to defaults');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al resetear configuración';
      setError(message);
      console.error('[useConfiguration] Error resetting configuration:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Prueba la conexión con la API
   */
  const testConnectionHTTP = useCallback(async (): Promise<boolean> => {
    if (!configuration) return false;
    
    try {
      // Intentar hacer una petición simple (ajusta el endpoint según tu API)
      const response = await apiClient.getInstance().get('/health');
      return response.status === 200;
    } catch (err) {
      console.error('[useConfiguration] Connection test failed:', err);
      return false;
    }
  }, [configuration]);


  /**
   * Actualiza los servicios (ApiClient y WebSocket) con la nueva configuración
   */
  const updateServices = (config: ApiConfiguration) => {
    // Actualizar ApiClient
    apiClient.updateConfig({
      baseUrl: config.httpBaseUrl,
      timeout: config.timeout || 30000,
      retryAttempts: config.retryAttempts || 3,
      retryDelay: config.retryDelay || 1000,
    });

    // Actualizar WebSocket Service
    // Nota: WebSocket se reconectará automáticamente cuando sea necesario
    jobWebSocketService.disconnect();
    
    console.log('[useConfiguration] Services updated with new configuration');
  };

  return {
    configuration,
    httpBaseUrl: baseAddressHttp,
    wsBaseUrl: baseAddressWs,
    loading,
    error,
    saveConfiguration,
    updateAddressHttp,
    updateAddressWs,
    resetToDefaults,
    testConnectionHTTP,
  };
};