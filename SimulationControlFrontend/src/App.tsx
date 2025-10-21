import { useEffect, useRef, useState } from 'react';
import './App.css'
import { AppRouter } from './router/AppRouter';
import { initializeServices } from './services/Initializer';
import LoadingSpinner from './components/ui/LoandingSpinner';
import ErrorDisplay from './components/ui/ErrorDisplay';

function App() {
  const [servicesReady, setServicesReady] = useState<boolean>(false);
  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    // Inicializar servicios al montar la aplicación
    const init = async () => {
      try {
        console.log('[App] Initializing services...');
        await initializeServices();
        setServicesReady(true);
        console.log('[App] Services ready');
      } catch (error) {
        console.error('[App] Error initializing services:', error);
        setInitError('Error al inicializar la aplicación');
        // Aún así permitir que la app cargue con valores por defecto
        setServicesReady(true);
      }
    };

    init();
  }, []);
  if (!servicesReady) {
    return <LoadingSpinner message="Inicializando aplicación" />;
  }else if (initError) {
    return <ErrorDisplay message={initError} />;
  }
  return <AppRouter />
}

export default App
