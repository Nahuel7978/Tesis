import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Resolver alias para que coincidan con tsconfig.json
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/types': path.resolve(__dirname, './src/types'),
    },
  },

  // Configuración para desarrollo
  server: {
    port: 5173,
    host: true, // Permite acceso desde otras IPs (útil para testing)
  },

  // Configuración de build
  build: {
    outDir: 'dist',
    sourcemap: true, // Source maps para debugging en producción
    rollupOptions: {
      output: {
        manualChunks: {
          // Separar dependencias grandes en chunks
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          charts: ['recharts'],
          utils: ['axios', 'clsx', 'zustand'],
        },
      },
    },
  },

  // Optimización de dependencias
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
})