import React, { useState, useEffect } from 'react';
import { useConfiguration } from '@/hooks/useConfiguration';

/**
 * Página de configuración de la aplicación
 * Permite al usuario configurar la dirección IP de la API
 */
const ConfigurationPage: React.FC = () => {
  const {
    configuration,
    httpBaseUrl,
    wsBaseUrl,
    loading,
    error,
    updateAddressHttp,
    updateAddressWs,
    resetToDefaults,
    testConnectionHTTP,
  } = useConfiguration();

  // Estado local para el formulario
  const [ipAddressHTTP, setIpAddressHttp] = useState<string>('');
  const [ipAddressWS, setIpAddressWs] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Sincronizar con la configuración cargada
  useEffect(() => {
    if (httpBaseUrl) {
        setIpAddressHttp(httpBaseUrl);
    }
  }, [httpBaseUrl]);

  useEffect(() => {
    if (wsBaseUrl) {
        setIpAddressWs(wsBaseUrl);
    }
  }, [wsBaseUrl]);

  // Limpiar mensajes después de un tiempo
  useEffect(() => {
    if (saveSuccess) {
      const timer = setTimeout(() => setSaveSuccess(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess]);

  useEffect(() => {
    if (testResult !== null) {
      const timer = setTimeout(() => setTestResult(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [testResult]);

  /**
   * Valida el formato de dirección IP:puerto
   */
  const validateAddress = (address: string): boolean => {
    const trimmed = address.trim();
    
    // Permitir localhost
    if (trimmed.startsWith('http://localhost') || trimmed.startsWith('ws://localhost')) 
      return true;
    
    // Validar formato IP:puerto o dominio:puerto
    const pattern = /^(http:\/\/|ws:\/\/)?[\w\.\-]+(:\d+)?(\/[\w\.\-\/]+)?$/i; 
    return pattern.test(trimmed);
  };

  /**
   * Maneja el guardado de la configuración
   */
  const handleSave = async () => {
    setFormError(null);
    setSaveSuccess(false);
    
    if (!ipAddressHTTP.trim()) {
      setFormError('La dirección HTTP no puede estar vacía');
      return;
    }else if (!ipAddressWS.trim()) {
        setFormError('La dirección Websocket no puede estar vacía');
        return;
      }
    if (!validateAddress(ipAddressHTTP)) {
      setFormError('Formato de dirección HTTP inválido. Use formato: IP:puerto o dominio:puerto');
      return;
    }else if (!validateAddress(ipAddressWS)){
        setFormError('Formato de dirección WebSocket inválido. Use formato: IP:puerto o dominio:puerto');
    }

    setIsSaving(true);

    try {
      await updateAddressHttp(ipAddressHTTP);
      await updateAddressWs(ipAddressWS);

      setSaveSuccess(true);
      setFormError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      setFormError(message);
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Maneja el reset a valores por defecto
   */
  const handleReset = async () => {
    if (!window.confirm('¿Está seguro de restaurar la configuración por defecto?')) {
      return;
    }

    setIsSaving(true);
    setFormError(null);

    try {
      await resetToDefaults();
      setSaveSuccess(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al resetear';
      setFormError(message);
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Prueba la conexión con la API
   */
  const handleTestConnectionHTTP = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await testConnectionHTTP();
      setTestResult(result);
    } catch (err) {
      setTestResult(false);
    } finally {
      setIsTesting(false);
    }
  };

  if (loading && !configuration) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Cargando configuración...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-semibold text-gray-900">Configuración</h1>
        <p className="text-sm text-gray-600 mt-1">
          Ajustes generales de la aplicación
        </p>
      </div>

      {/* Error global */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Sección: Conexión API */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Conexión API</h2>
          <p className="text-sm text-gray-600 mt-1">
            Configure la dirección del servidor de la API
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Campo de dirección IP */}
          <div>
            <label
              htmlFor="HTTP"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Dirección HTTP.
            </label>
            <div className="flex gap-3">
              <input
                id="HTTP"
                type="text"
                value={ipAddressHTTP}
                onChange={(e) => setIpAddressHttp(e.target.value)}
                placeholder="http://192.168.1.100:8000"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSaving}
              />
              <button
                onClick={handleTestConnectionHTTP}
                disabled={isTesting || isSaving}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isTesting ? 'Probando...' : 'Probar'}
              </button>

              
            </div>
            <label
              htmlFor="WS"
              className="block text-sm font-medium text-gray-700 mb-2 mt-4"
            >
              Dirección WebSocket.
            </label>
            <div className="flex gap-3">
              <input
                id="WS"
                type="text"
                value={ipAddressWS}
                onChange={(e) => setIpAddressWs(e.target.value)}
                placeholder="ws::/192.168.1.100:8000"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSaving}
              />
             </div>
            <p className="text-xs text-gray-500 mt-2">
              Formato: dirección:puerto (ej: 192.168.1.100:8000 o localhost:8000)
            </p>
            
            {/* Resultado del test */}
            {testResult !== null && (
              <div className={`mt-3 p-3 rounded-lg ${testResult ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <p className={`text-sm ${testResult ? 'text-green-800' : 'text-red-800'}`}>
                  {testResult ? '✓ Conexión exitosa' : '✗ No se pudo conectar con el servidor'}
                </p>
              </div>
            )}

            {/* Error del formulario */}
            {formError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{formError}</p>
              </div>
            )}

            {/* Mensaje de éxito */}
            {saveSuccess && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">✓ Configuración guardada correctamente</p>
              </div>
            )}
          </div>

          {/* Botones de acción */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isSaving ? 'Guardando...' : 'Guardar configuración'}
            </button>
            <button
              onClick={handleReset}
              disabled={isSaving}
              className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Restaurar valores por defecto
            </button>
          </div>
        </div>
      </div>

      {/* Sección: Información adicional */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">🔎 Información</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• La configuración se guarda automáticamente en el dispositivo</li>
          <li>• Los cambios se aplicarán inmediatamente a todas las conexiones</li>
          <li>• Use "Probar" para verificar la conexión antes de guardar</li>
        </ul>
      </div>
    </div>
  );
};

export default ConfigurationPage;