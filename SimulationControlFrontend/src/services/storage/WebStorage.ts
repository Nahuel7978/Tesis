// src/services/storage/web-storage.ts

import { IStorage } from './StorageInterface';

/**
 * Implementación de IStorage usando localStorage del navegador
 * Para uso en versión web (futuro)
 */
export class WebStorage implements IStorage {
  private prefix: string;

  constructor(prefix: string = 'app_') {
    this.prefix = prefix;
  }

  private getFullKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const fullKey = this.getFullKey(key);
      const item = localStorage.getItem(fullKey);
      
      if (item === null) {
        return null;
      }

      return JSON.parse(item) as T;
    } catch (error) {
      console.error(`Error getting key "${key}" from Web storage:`, error);
      return null;
    }
  }

  async set<T>(key: string, value: T): Promise<void> {
    try {
      const fullKey = this.getFullKey(key);
      const serialized = JSON.stringify(value);
      localStorage.setItem(fullKey, serialized);
    } catch (error) {
      console.error(`Error setting key "${key}" in Web storage:`, error);
      throw error;
    }
  }

  async remove(key: string): Promise<void> {
    try {
      const fullKey = this.getFullKey(key);
      localStorage.removeItem(fullKey);
    } catch (error) {
      console.error(`Error removing key "${key}" from Web storage:`, error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      const keys = await this.keys();
      keys.forEach((key) => {
        const fullKey = this.getFullKey(key);
        localStorage.removeItem(fullKey);
      });
    } catch (error) {
      console.error('Error clearing Web storage:', error);
      throw error;
    }
  }

  async keys(): Promise<string[]> {
    try {
      const allKeys: string[] = [];
      
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.prefix)) {
          allKeys.push(key.substring(this.prefix.length));
        }
      }

      return allKeys;
    } catch (error) {
      console.error('Error getting keys from Web storage:', error);
      return [];
    }
  }

}