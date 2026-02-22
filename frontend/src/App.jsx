import React, { useState, useEffect } from 'react'
import axios from 'axios'
import UploadView from './components/UploadView'
import ProcessingView from './components/ProcessingView'
import ResultsView from './components/ResultsView'
import EvalDashboard from './components/EvalDashboard'

// Main application component managing overall state and view transitions
function App() {
  const [activeTab, setActiveTab] = useState('analysis') // 'analysis' | 'evaluations'
  const [activeView, setActiveView] = useState('upload') // 'upload' | 'processing' | 'results'
  const [currentTaskId, setCurrentTaskId] = useState(null)
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [taskResult, setTaskResult] = useState(null)
  const [apiHealthy, setApiHealthy] = useState(false)

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await axios.get('/health', { timeout: 5000 })
        setApiHealthy(true)
      } catch (error) {
        setApiHealthy(false)
      }
    }

    checkHealth()
    const healthInterval = setInterval(checkHealth, 30000) // Check every 30s

    return () => clearInterval(healthInterval)
  }, [])

  const handleSubmit = (taskId, sessionId) => {
    setCurrentTaskId(taskId)
    setCurrentSessionId(sessionId)
    setActiveView('processing')
  }

  const handleComplete = (sessionId, result) => {
    setCurrentSessionId(sessionId)
    setTaskResult(result)
    setActiveView('results')
  }

  const handleReset = () => {
    setActiveView('upload')
    setCurrentTaskId(null)
    setCurrentSessionId(null)
    setTaskResult(null)
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Navigation Bar */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="text-2xl font-bold text-brand-500">🧠</div>
          <h1 className="text-xl font-semibold text-gray-100">DocuForge AI</h1>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4">
          <button
            onClick={() => {
              setActiveTab('analysis')
              setActiveView('upload')
            }}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'analysis'
                ? 'text-brand-500 border-b-2 border-brand-500'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Analysis
          </button>
          <button
            onClick={() => setActiveTab('evaluations')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'evaluations'
                ? 'text-brand-500 border-b-2 border-brand-500'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Evaluations
          </button>
        </div>

        {/* Health Indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              apiHealthy ? 'bg-green-500' : 'bg-red-500'
            }`}
          ></div>
          <span className="text-xs text-gray-400">
            {apiHealthy ? 'API Ready' : 'API Offline'}
          </span>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {activeTab === 'analysis' && (
          <>
            {activeView === 'upload' && (
              <UploadView onSubmit={handleSubmit} />
            )}
            {activeView === 'processing' && (
              <ProcessingView taskId={currentTaskId} onComplete={handleComplete} />
            )}
            {activeView === 'results' && (
              <ResultsView sessionId={currentSessionId} taskResult={taskResult} onReset={handleReset} />
            )}
          </>
        )}
        {activeTab === 'evaluations' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Evaluation Dashboard</h2>
            <EvalDashboard />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
