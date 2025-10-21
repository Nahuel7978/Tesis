import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Upload, FileArchive, X, CheckCircle, AlertCircle } from 'lucide-react';

interface FileUploadZoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  description?: string;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  file,
  onFileChange,
  accept = '.zip',
  maxSizeMB = 100,
  label = 'Mundo de Webots',
  description = 'Archivo del mundo de Webots comprimido'
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleFileSelect = useCallback((selectedFile: File | null) => {
    console.log('handleFileSelect called with:', selectedFile);
    if (!selectedFile) {
      onFileChange(null);
      setValidationError(null);
      return;
    }

    if (validateFile(selectedFile)) {
      onFileChange(selectedFile);
    } else {
      console.log('File validation failed');
      onFileChange(null);
    }
  },[onFileChange]);

  useEffect(() => {
    const dropZone = dropZoneRef.current;
    if (!dropZone) return;
  
    let dragCounter = 0;
  
    const handleDragEnter = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter++;
      setIsDragging(true);
    };
  
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy';
      }
    };
  
    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter--;
      if (dragCounter === 0) {
        setIsDragging(false);
      }
    };
  
    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      
      dragCounter = 0;
      setIsDragging(false);

      if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        if(droppedFile!=undefined)
          handleFileSelect(droppedFile); // ← Ahora usa la función actualizada
      }
    };
  
    dropZone.addEventListener('dragenter', handleDragEnter, true);
    dropZone.addEventListener('dragover', handleDragOver, true);
    dropZone.addEventListener('dragleave', handleDragLeave, true);
    dropZone.addEventListener('drop', handleDrop, true);
  
    return () => {
      dropZone.removeEventListener('dragenter', handleDragEnter, true);
      dropZone.removeEventListener('dragover', handleDragOver, true);
      dropZone.removeEventListener('dragleave', handleDragLeave, true);
      dropZone.removeEventListener('drop', handleDrop, true);
    };
  }, [handleFileSelect]); 

  const validateFile = useCallback((file: File): boolean => {
    setValidationError(null);

    if (!file.name.toLowerCase().endsWith('.zip')) {
      setValidationError('El archivo debe tener extensión .zip');
      return false;
    }

    const sizeMB = file.size / 1024 / 1024;
    if (sizeMB > maxSizeMB) {
      setValidationError(`El archivo excede el tamaño máximo de ${maxSizeMB}MB`);
      return false;
    }

    return true;
  },[maxSizeMB]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    handleFileSelect(selectedFile);
  };

  const handleRemoveFile = () => {
    onFileChange(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}

      {!file ? (
        <>
          <div
            ref={dropZoneRef}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
              ${isDragging 
                ? 'border-blue-500 bg-blue-50 scale-[1.02]' 
                : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
              }
              ${validationError ? 'border-red-300 bg-red-50' : ''}
            `}
          >
            <div 
              className="flex flex-col items-center gap-3 select-none"
              style={{ pointerEvents: 'none', userSelect: 'none' }}
            >
              <div className={`
                w-16 h-16 rounded-full flex items-center justify-center transition-colors
                ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
              `}>
                <Upload className={`
                  w-8 h-8 transition-colors
                  ${isDragging ? 'text-blue-600' : 'text-gray-400'}
                `} />
              </div>

              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">
                  {isDragging ? 'Suelta el archivo aquí' : 'Arrastra un archivo .zip o haz clic para seleccionar'}
                </p>
                <p className="text-xs text-gray-500">
                  {description} • Máximo {maxSizeMB}MB
                </p>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept={accept}
              onChange={handleInputChange}
              className="hidden"
              style={{ display: 'none' }}
            />
          </div>

          {validationError && (
            <div className="mt-2 flex items-center gap-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <p className="text-sm">{validationError}</p>
            </div>
          )}
        </>
      ) : (
        <div className="border border-gray-300 rounded-lg overflow-hidden bg-gradient-to-r from-green-50 to-blue-50 animate-in fade-in duration-300">
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1 min-w-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <FileArchive className="w-6 h-6 text-blue-600" />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                </div>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>

            <button
              onClick={handleRemoveFile}
              className="p-2 hover:bg-red-100 rounded-lg transition-colors group flex-shrink-0"
              title="Remover archivo"
            >
              <X className="w-5 h-5 text-gray-600 group-hover:text-red-600 transition-colors" />
            </button>
          </div>

          <div className="h-1 bg-gradient-to-r from-green-400 to-blue-500"></div>
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;