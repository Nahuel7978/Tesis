import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import TestPage from './pages/TestPage';
import TrainingConfigPage from './pages/TrainingConfigPage';
import './App.css'

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/training/new" element={<TrainingConfigPage />} />
        <Route path="/test" element={<TestPage />} />
        {/*<Route path="*" element={<Navigate to="/test" replace />} />*/}
        <Route path="*" element={<Navigate to="/training/new" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
