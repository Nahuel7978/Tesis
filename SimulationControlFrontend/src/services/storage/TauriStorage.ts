import { invoke } from '@tauri-apps/api/core';
import { IStorage } from './StorageInterface';

/**
 * Implementación de IStorage usando Tauri Store Plugin
 * Utiliza el sistema de archivos nativo para persistencia
 */
export class TauriStorage implements IStorage {
  private storeName: string;

  constructor(storeName: string = 'app-store.json') {
    this.storeName = storeName;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await invoke<T | null>('plugin:store|get', {
        path: this.storeName,
        key,
      });
      return value;
    } catch (error) {
      console.error(`Error getting key "${key}" from Tauri storage:`, error);
      return null;
    }
  }

  async set<T>(key: string, value: T): Promise<void> {
    try {
      await invoke('plugin:store|set', {
        path: this.storeName,
        key,
        value,
      });
      // Guardar cambios en disco
      await invoke('plugin:store|save', {
        path: this.storeName,
      });
    } catch (error) {
      console.error(`Error setting key "${key}" in Tauri storage:`, error);
      throw error;
    }
  }

  async remove(key: string): Promise<void> {
    try {
      await invoke('plugin:store|delete', {
        path: this.storeName,
        key,
      });
      await invoke('plugin:store|save', {
        path: this.storeName,
      });
    } catch (error) {
      console.error(`Error removing key "${key}" from Tauri storage:`, error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      await invoke('plugin:store|clear', {
        path: this.storeName,
      });
      await invoke('plugin:store|save', {
        path: this.storeName,
      });
    } catch (error) {
      console.error('Error clearing Tauri storage:', error);
      throw error;
    }
  }

  async keys(): Promise<string[]> {
    try {
      const keys = await invoke<string[]>('plugin:store|keys', {
        path: this.storeName,
      });
      return keys || [];
    } catch (error) {
      console.error('Error getting keys from Tauri storage:', error);
      return [];
    }
  }

}