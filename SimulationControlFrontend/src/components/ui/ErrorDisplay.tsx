import { useNavigate } from 'react-router-dom';

interface ErrorDisplayProps {
  message: string;
  showBackButton?: boolean;
}

const ErrorDisplay = ({ message, showBackButton = true }: ErrorDisplayProps) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-4xl">❌</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Error
          </h2>
          <p className="text-gray-600">{message}</p>
        </div>

        {showBackButton && (
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Volver al Dashboard
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;