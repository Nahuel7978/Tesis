// src/router/AppRouter.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '../pages/DashboardPage';
import  TrainingConfigPage from '../pages/TrainingConfigPage';
import TestPage from '@/pages/TestPage';
// Importa aquí tu TrainPage cuando la tengas
// import { TrainPage } from '@/features/training/pages/TrainPage';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          {/* Redirigir la raíz al dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* Cargar Mundo */}
          <Route path="/training/new" element={<TrainingConfigPage />} />
          
          <Route path="/test" element={<TestPage/>} />

          {/* Detalle de Training (cuando lo implementes) */}
          {/* <Route path="/train/:jobId" element={<TrainPage />} /> */}
          
          {/* 404 - Ruta no encontrada */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
};