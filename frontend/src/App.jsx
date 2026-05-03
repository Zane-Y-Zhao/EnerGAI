import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import AiAssistantPage from './pages/AiAssistantPage'

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ai-assistant" element={<AiAssistantPage />} />
      </Routes>
    </div>
  )
}

export default App