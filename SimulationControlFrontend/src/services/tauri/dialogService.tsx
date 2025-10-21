import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';

export class DialogService {
  /**
   * Abre un diálogo para guardar un archivo
   * @param blob - Archivo a guardar
   * @param defaultFileName - Nombre por defecto del archivo
   * @param filters - Filtros de extensión
   */
  async saveFile(
    blob: Blob,
    defaultFileName: string,
    filters?: Array<{ name: string; extensions: string[] }>
  ): Promise<boolean> {
    try {
      // Abrir diálogo de guardado
      const filePath = await save({
        defaultPath: defaultFileName,
        filters: filters || [
          { name: 'Archivo ZIP', extensions: ['zip'] },
          { name: 'Todos los archivos', extensions: ['*'] }
        ],
      });

      // Si el usuario cancela, filePath será null
      if (!filePath) {
        console.log('[DialogService] Usuario canceló el guardado');
        return false;
      }

      // Convertir blob a ArrayBuffer
      const arrayBuffer = await blob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      // Escribir archivo en la ruta seleccionada
      await writeFile(filePath, uint8Array);
      
      console.log(`[DialogService] Archivo guardado en: ${filePath}`);
      return true;
    } catch (error) {
      console.error('[DialogService] Error guardando archivo:', error);
      throw error;
    }
  }

  /**
   * Helper para verificar si estamos en Tauri
   */
  isTauriAvailable(): boolean {
    //return typeof window !== 'undefined' && '__TAURI__' in window;
    return true
  }
}

// Singleton
export const dialogService = new DialogService();
export default dialogService;