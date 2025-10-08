import { invoke } from '@tauri-apps/api/core';
import { IStorage } from './StorageInterface';

/**
 * Implementación de IStorage usando Tauri Store Plugin
 * Utiliza el sistema de archivos nativo para persistencia
 */
export class TauriStorage implements IStorage {
  private storeName: string;
  private storeRid: number | null = null;

  constructor(storeName: string = 'simulation_control_store.json') {
    this.storeName = storeName;
  }

  /**
  * Inicializa el store y obtiene el RID (Resource Identifier).
  * Debe llamarse antes de usar el storage.
  */
  private async ensureStore(): Promise<number> {
    if (this.storeRid !== null) {
      return this.storeRid;
    }

    try {
      // Cargar o crear el store
      this.storeRid = await invoke<number>('plugin:store|load', {
        path: this.storeName,
      });
      return this.storeRid;
    } catch (error) {
      console.error('Error loading Tauri store:', error);
      throw error;
    }
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const rid = await this.ensureStore();
      // El plugin devuelve un array [valor, encontrado]
      const result = await invoke<[T | null, boolean]>('plugin:store|get', {
        rid,
        key,
      });
      
      console.log(`[TauriStorage] Raw result for key "${key}":`, result);
      
      // Si es un array, extraer el primer elemento
      if (Array.isArray(result)) {
        const [value, found] = result;
        if (!found || value === null) {
          console.log(`[TauriStorage] Key "${key}" not found`);
          return null;
        }
        console.log(`[TauriStorage] Retrieved value for key "${key}":`, value);
        return value;
      }
      
      // Fallback: si no es un array, devolver el resultado directamente
      console.log(`[TauriStorage] Direct value for key "${key}":`, result);
      return result as T | null;
    } catch (error) {
      console.error(`Error getting key "${key}" from Tauri storage:`, error);
      return null;
    }
  }


  async set<T>(key: string, value: T): Promise<void> {
    try {
      const rid = await this.ensureStore();
      await invoke('plugin:store|set', {
        rid,
        key,
        value,
      });
      // Guardar cambios en disco
      await invoke('plugin:store|save', {
        rid,
      });
    } catch (error) {
      console.error(`Error setting key "${key}" in Tauri storage:`, error);
      throw error;
    }
  }

  async remove(key: string): Promise<void> {
    try {
      const rid = await this.ensureStore();
      await invoke('plugin:store|delete', {
        rid,
        key,
      });
      await invoke('plugin:store|save', {
        rid,
      });
    } catch (error) {
      console.error(`Error removing key "${key}" from Tauri storage:`, error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      const rid = await this.ensureStore();
      await invoke('plugin:store|clear', {
        rid,
      });
      await invoke('plugin:store|save', {
        rid,
      });
    } catch (error) {
      console.error('Error clearing Tauri storage:', error);
      throw error;
    }
  }

  async keys(): Promise<string[]> {
    try {
      const rid = await this.ensureStore();
      const keys = await invoke<string[]>('plugin:store|keys', {
        rid,
      });
      return keys || [];
    } catch (error) {
      console.error('Error getting keys from Tauri storage:', error);
      return [];
    }
  }
  /**
   * Cierra el store y libera recursos.
   * Útil cuando ya no se necesita el storage.
   */
  async close(): Promise<void> {
    if (this.storeRid !== null) {
      try {
        // Guardar antes de cerrar
        await invoke('plugin:store|save', {
          rid: this.storeRid,
        });
      } catch (error) {
        console.error('Error closing Tauri store:', error);
      } finally {
        this.storeRid = null;
      }
    }
  }
}

// Exportar una instancia singleton
export const storage = new TauriStorage();