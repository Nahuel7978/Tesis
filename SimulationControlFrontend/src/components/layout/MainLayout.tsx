// src/components/layout/MainLayout.tsx
import React from 'react';
import { Sidebar } from './Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      {/* El margen izquierdo del main se adapta al ancho del sidebar en desktop, y es 0 en móvil */}
      <main className="flex-1 md:ml-[var(--sidebar-width)] mt-16 md:mt-0"> {/* Ajuste el mt para el botón del sidebar en móvil */}
        {children}
      </main>
    </div>
  );
};