import React from 'react';
import { Info } from 'lucide-react';

interface HyperparameterInputProps {
  label: string;
  value: number;
  type: 'number' | 'integer';
  min?: number | undefined;
  max?: number | undefined;
  step?: number | undefined;
  description?: string | undefined;
  onChange: (value: number) => void;
}

const HyperparameterInput: React.FC<HyperparameterInputProps> = ({
  label,
  value,
  type,
  min,
  max,
  step,
  description,
  onChange,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = type === 'integer' 
      ? parseInt(e.target.value) || 0
      : parseFloat(e.target.value) || 0;
    onChange(newValue);
  };

  const handleIncrement = () => {
    const increment = step || (type === 'integer' ? 1 : 0.01);
    const newValue = value + increment;
    if (max === undefined || newValue <= max) {
      onChange(parseFloat(newValue.toFixed(6)));
    }
  };

  const handleDecrement = () => {
    const decrement = step || (type === 'integer' ? 1 : 0.01);
    const newValue = value - decrement;
    if (min === undefined || newValue >= min) {
      onChange(parseFloat(newValue.toFixed(6)));
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <label className="block text-sm font-bold text-gray-700">
          {label}
        </label>
        {description && (
          <div className="group relative">
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 bg-gray-900 text-white text-xs rounded-lg p-3 z-10">
              {description}
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        )}
      </div>
      
      <div className="relative flex items-center">
        <input
          type="number"
          value={value}
          onChange={handleChange}
          min={min}
          max={max}
          step={step || (type === 'integer' ? 1 : 0.01)}
          className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
        />
        
        {/* Increment/Decrement buttons */}
        <div className="absolute right-1 top-1/2 -translate-y-1/2 flex flex-col">
          <button
            type="button"
            onClick={handleIncrement}
            className="px-2 py-0.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <button
            type="button"
            onClick={handleDecrement}
            className="px-2 py-0.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default HyperparameterInput;