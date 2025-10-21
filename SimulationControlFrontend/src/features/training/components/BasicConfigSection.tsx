import React, { useRef, useEffect } from 'react';
import { Upload, FileArchive, X } from 'lucide-react';
import { PolicyType, TrainingAlgorithm } from '@/types/base';
import FileUploadZone from './FileUploadZip';

interface BasicConfigSectionProps {
  worldFile: File | null;
  worldName: string;
  robotName: string;
  controllerName: string;
  envClass: string;
  algorithm: TrainingAlgorithm;
  policy: PolicyType;
  timesteps: number;
  onWorldFileChange: (file: File | null) => void;
  onWorldNameChange:(value: string) => void;
  onRobotNameChange: (value: string) => void;
  onControllerNameChange:(value: string) => void;
  onEnvClassChange:(value: string) => void;
  onAlgorithmChange: (algorithm: TrainingAlgorithm) => void;
  onPolicyChange: (policy: PolicyType) => void;
  onTimestepsChange: (value: number) => void;
}

const BasicConfigSection: React.FC<BasicConfigSectionProps> = ({
  worldFile,
  worldName,
  robotName,
  controllerName,
  envClass,
  algorithm,
  policy,
  timesteps,
  onWorldFileChange,
  onWorldNameChange,
  onRobotNameChange,
  onControllerNameChange,
  onEnvClassChange,
  onAlgorithmChange,
  onPolicyChange,
  onTimestepsChange,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleRemoveFile = () => {
    onWorldFileChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        <u>Configuración Básica</u>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {/* World File Upload */}
        <div className="md:col-span-2 lg:col-span-2">
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Mundo de Webots
          </label>
          
          {!worldFile ? (
            <div>
              <FileUploadZone
                file={worldFile}
                onFileChange={onWorldFileChange}
                accept=".zip"
                maxSizeMB={100}
                label=""
                description="Archivo del mundo de Webots comprimido"
              />
            </div>
          ) : (
            <div className="border border-gray-300 rounded-lg p-4 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-3">
                <FileArchive className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {worldFile.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(worldFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          )}
        </div>

        {/* World Name */}
        <div className="md:col-span-2 lg:col-span-2" >
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Nombre del Entrenamiento
          </label>
          <input
            type="text"
            value={worldName}
            onChange={(e) => onWorldNameChange(e.target.value)}
            placeholder="Ej: Navegacion Autonoma"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            Nombre del entrenamiento que se está creando
          </p>
        </div>

        {/* Robot Name */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Nombre del Robot
          </label>
          <input
            type="text"
            value={robotName}
            onChange={(e) => onRobotNameChange(e.target.value)}
            placeholder="Ej: MyRobot"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            Nombre del DEF del robot en el mundo de Webots
          </p>
        </div>
        

        {/*Controller Name */ }
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Nombre del Controlador
          </label>
          <input
            type="text"
            value={controllerName}
            onChange={(e) => onControllerNameChange(e.target.value)}
            placeholder="Ej: MyRobotController"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            Nombre del controlador del robot en el mundo de Webots
          </p>
        </div>

        {/* Enviroment class */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Clase del entorno
          </label>
          <input
            type="text"
            value={envClass}
            onChange={(e) => onEnvClassChange(e.target.value)}
            placeholder="Ej: RobotEnv"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            Clase del enviroment del controlador del robot
          </p>
        </div>
        

        {/* Algorithm */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Algoritmo
          </label>
          <select
            value={algorithm}
            onChange={(e) => onAlgorithmChange(e.target.value as TrainingAlgorithm)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow bg-white"
          >
            <option value={TrainingAlgorithm.DQN}>DQN (Deep Q-Network)</option>
            <option value={TrainingAlgorithm.PPO}>PPO (Proximal Policy Optimization)</option>
            <option value={TrainingAlgorithm.A2C}>A2C (Advantage Actor-Critic)</option>
            <option value={TrainingAlgorithm.SAC}>SAC (Soft Actor-Critic)</option>
            <option value={TrainingAlgorithm.TD3}>TD3 (Twin Delayed DDPG)</option>
            <option value={TrainingAlgorithm.DDPG}>DDPG (Deep Deterministic Policy Gradient)</option>
          </select>
        </div>

        {/* Policy Type */}
        <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">
              Tipo de Política
            </label>
            <select
              value={policy}
              onChange={(e) => onPolicyChange(e.target.value as PolicyType)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow bg-white"
            >
              <option value={PolicyType.MlpPolicy}>MLP Policy</option>
              <option value={PolicyType.CnnPolicy}>CNN Policy</option>
              <option value={PolicyType.MultiInputPolicy}>Multi-Input Policy</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
            <strong>⚠️ Advertencia:</strong> La elección de la policy es una decisión de arquitectura de red neuronal que debe ser coherente con el tipo de datos de observación del entorno.
            </p>
        </div>

        {/* Timesteps */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Episodios Totales
          </label>
          <input
            type="number"
            value={timesteps}
            onChange={(e) => onTimestepsChange(parseInt(e.target.value) || 0)}
            min="1"
            step="1"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            Número total de pasos de tiempo para el entrenamiento
          </p>
        </div>
      </div>
    </div>
  );
};

export default BasicConfigSection;