// src/components/layout/Sidebar.tsx
import React, { useState } from 'react'; // Importa useState
import { useNavigate, useLocation } from 'react-router-dom';
import { useMediaQuery } from 'react-responsive'; // Importa useMediaQuery

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery({ maxWidth: 768 }); // Define un breakpoint para móvil
  const [isOpen, setIsOpen] = useState(!isMobile); // Controla si el sidebar está abierto/cerrado

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      path: '/dashboard'
    },
    {
      id: 'Nuevo Entrenamiento',
      label: 'Cargar Mundo',
      icon: '🦾',
      path: '/training/new'
    }
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Botón para abrir/cerrar sidebar en móvil */}
      {isMobile && (
        <button
          onClick={toggleSidebar}
          className="fixed top-4 left-4 z-50 p-2 bg-blue-600 text-white rounded-md shadow-lg"
        >
          {isOpen ? '✕' : '☰'} {/* Icono para cerrar o abrir */}
        </button>
      )}

      <div
        className={`
          bg-white border-r border-gray-200 h-screen fixed left-0 top-0 flex flex-col z-40
          transition-all duration-300 ease-in-out
          ${isOpen ? 'translate-x-0 w-[var(--sidebar-width)]' : '-translate-x-full w-[var(--sidebar-width)]'}
          md:translate-x-0 md:w-[var(--sidebar-width)]
          ${isMobile && !isOpen ? 'hidden' : 'block'} /* Oculta completamente en móvil si está cerrado */
        `}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">
            {isOpen || !isMobile ? '🤖 Simulation Control App' : '🤖'}
          </h1>
          <p className="text-sm text-gray-500 mt-1 ml-8">
            {isOpen || !isMobile ? 'Simulación Robótica en la Nube' : ''}
          </p>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-5">
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => {
                    navigate(item.path);
                    if (isMobile) setIsOpen(false); // Cierra el sidebar después de navegar en móvil
                  }}
                  className={`
                    w-full flex items-center ${isOpen || !isMobile ? 'gap-3 px-4' : 'justify-center px-0'} py-3 rounded-lg text-left transition-colors
                    ${isActive(item.path)
                      ? 'bg-blue-50 text-blue-600 font-medium'
                      : 'text-gray-700'
                    }
                  `}
                  title={item.label} // Añade title para el tooltip en colapsado
                >
                  <span className="text-xl">{item.icon}</span>
                  {(isOpen || !isMobile) && <span>{item.label}</span>}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Overlay para cuando el sidebar está abierto en móvil */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={toggleSidebar}
        ></div>
      )}
    </>
  );
};