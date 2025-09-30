/**
 * Interface genérica para operaciones de almacenamiento
 * Permite abstraer la implementación específica (Tauri, Web, etc.)
 */
export interface IStorage {
    /**
     * Obtiene un valor del storage
     * @param key - Clave del valor a obtener
     * @returns El valor almacenado o null si no existe
     */
    get<T>(key: string): Promise<T | null>;
  
    /**
     * Almacena un valor en el storage
     * @param key - Clave bajo la cual almacenar el valor
     * @param value - Valor a almacenar
     */
    set<T>(key: string, value: T): Promise<void>;
  
    /**
     * Elimina un valor del storage
     * @param key - Clave del valor a eliminar
     */
    remove(key: string): Promise<void>;
  
    /**
     * Limpia completamente el storage
     */
    clear(): Promise<void>;
  
    /**
     * Obtiene todas las claves almacenadas
     * @returns Array con todas las claves
     */
    keys(): Promise<string[]>;
  
  }