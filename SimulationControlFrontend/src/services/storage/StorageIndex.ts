import { IStorage } from './StorageInterface';
import { TauriStorage } from './TauriStorage';
import { WebStorage } from './WebStorage';

/**
 * Detecta si la aplicación está corriendo en Tauri
 */
//const IS_TAURI = '__TAURI__' in window;
const IS_TAURI = true; // Forzar Tauri para pruebas locales

/**
 * Instancia singleton del storage
 * Selecciona automáticamente la implementación según el entorno
 */
export const storage: IStorage = IS_TAURI 
  ? new TauriStorage('webots-training-store.json')
  : new WebStorage('webots_training_');

/**
 * Constantes para las claves de almacenamiento
 */
export const STORAGE_KEYS = {
  SETTINGS: 'settings',
  USER_PREFERENCES: 'user_preferences',
} as const;

// Re-exportar tipos e interfaces
export type { IStorage };
export { TauriStorage, WebStorage };