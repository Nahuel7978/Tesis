import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiConfig, ApiErrorResponse } from '@/types/TypeIndex';

// Configuración por defecto.
const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: import.meta.env.API_BASE_URL || 'http://localhost:8000/SimulationControlApi/v1',
  timeout: 30000, // 30 segundos
  retryAttempts: 3,
  retryDelay: 1000 // 1 segundo
};

class ApiClient {
  private client: AxiosInstance;
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) { //config puede contener solo algunas de las propiedades de ApiConfig
    this.config = { ...DEFAULT_CONFIG, ...config };//Copio todos los valores de DEFAULT_CONFIG y los sobreescribo con los valores de config
    
    this.client = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      }
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    /**
     Metodo encargado de ejecutar código de forma automática antes de que se envíe una
     solicitud o antes de que se procese una respuesta.
    **/
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Futuro: Auth token handling
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API Response] ${response.status} ${response.config.url}`);
        return response;
      },
      async (error: AxiosError<ApiErrorResponse>) => {
        console.error('[API Response Error]', error.response?.data || error.message);
        
        // Retry logic para errores de red
        const config = error.config;
        if (config && this.shouldRetry(error)) {
          const retryCount = (config as any).__retryCount || 0;
          
          if (retryCount < this.config.retryAttempts) {
            (config as any).__retryCount = retryCount + 1;
            
            console.log(`[API Retry] Attempt ${retryCount + 1}/${this.config.retryAttempts}`);
            await this.delay(this.config.retryDelay);
            
            return this.client(config);
          }
        }
        
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry solo en errores de red o 5xx
    return !error.response || (error.response.status >= 500 && error.response.status < 600);
  }

  private normalizeError(error: AxiosError<ApiErrorResponse>): ApiErrorResponse {
    if (error.response?.data) {
      return error.response.data;
    }
    
    return{
      message: error.message || 'Unknown error occurred',
      error: error.code || 'UNKNOWN_ERROR',
      details: error.toJSON()
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public methods
  public getInstance(): AxiosInstance {
    return this.client;
  }

  public updateConfig(config: Partial<ApiConfig>) {
    this.config = { ...this.config, ...config };
    this.client.defaults.baseURL = this.config.baseUrl;
    this.client.defaults.timeout = this.config.timeout;
  }

  public getConfig(): ApiConfig {
    return { ...this.config };
  }
}

// Singleton instance
export const apiClient = new ApiClient();
export default apiClient.getInstance();