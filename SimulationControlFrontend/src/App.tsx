import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import TestPage from './pages/TestPage';
import './App.css'

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/test" element={<TestPage />} />
        <Route path="*" element={<Navigate to="/test" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
