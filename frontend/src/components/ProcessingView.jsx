import React, { useState, useEffect } from 'react'
import axios from 'axios'
import AgentGraph from './AgentGraph'

// ProcessingView: Polls task status and displays real-time agent execution progress
function ProcessingView({ taskId, onComplete }) {
  const [status, setStatus] = useState('queued')
  const [agentTrace, setAgentTrace] = useState([])
  const [error, setError] = useState(null)
  const [isProcessing, setIsProcessing] = useState(true)

  const AGENT_STAGES = [
    { name: 'Ingestion', color: 'blue' },
    { name: 'RAG', color: 'purple' },
    { name: 'Analysis', color: 'yellow' },
    { name: 'Writing', color: 'green' },
    { name: 'Verification', color: 'teal' },
  ]

  // Determine current stage based on agent trace
  const getCurrentStage = () => {
    if (agentTrace.length === 0) return 'Queued'
    const lastEntry = agentTrace[agentTrace.length - 1]
    if (lastEntry.includes('ingestion')) return 'Ingestion'
    if (lastEntry.includes('rag')) return 'RAG'
    if (lastEntry.includes('analyst')) return 'Analysis'
    if (lastEntry.includes('writer')) return 'Writing'
    if (lastEntry.includes('verifier')) return 'Verification'
    return 'Processing'
  }

  // Poll for task status
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await axios.get(`/api/v1/status/${taskId}`)
        setStatus(response.data.status)

        if (response.data.result) {
          const result = response.data.result
          setAgentTrace(result.agent_trace || [])

          if (response.data.status === 'success') {
            clearInterval(intervalRef.current)
            setIsProcessing(false)
            setTimeout(() => {
              const sessionId = result.session_id || taskId
              onComplete(sessionId, result)
            }, 500)
          }
        }

        if (response.data.status === 'failure') {
          clearInterval(intervalRef.current)
          setError(response.data.result?.error || 'Task failed')
          setIsProcessing(false)
        }
      } catch (err) {
        setError(`Polling error: ${err.message}`)
        setIsProcessing(false)
      }
    }

    const intervalRef = { current: setInterval(pollStatus, 2000) }
    return () => clearInterval(intervalRef.current)
  }, [taskId, onComplete])

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Title with Animated Dots */}
        <h1 className="text-3xl font-bold text-gray-100">
          Analysing your document
          <span className="inline-block w-6">
            <span className="animate-bounce">.</span>
            <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>
              .
            </span>
            <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>
              .
            </span>
          </span>
        </h1>

        {/* Agent Graph */}
        <div>
          <h2 className="text-lg font-semibold text-gray-300 mb-4">Agent Pipeline</h2>
          <AgentGraph agentTrace={agentTrace} isProcessing={isProcessing} />
        </div>

        {/* Progress Stage Indicator */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <p className="text-gray-400 text-sm mb-2">Current Stage</p>
          <p className="text-2xl font-bold text-brand-500">{getCurrentStage()}</p>
        </div>

        {/* Log Panel */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="bg-gray-700 px-6 py-3 border-b border-gray-600">
            <h3 className="font-semibold text-gray-200">Execution Log</h3>
          </div>
          <div className="h-48 overflow-y-auto p-4 space-y-2">
            {agentTrace.length === 0 ? (
              <p className="text-gray-400 text-sm">Waiting for agent execution...</p>
            ) : (
              agentTrace.map((entry, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded text-xs font-mono animate-fadeIn ${
                    entry.includes('ingestion')
                      ? 'bg-blue-900/30 text-blue-200'
                      : entry.includes('rag')
                      ? 'bg-purple-900/30 text-purple-200'
                      : entry.includes('analyst')
                      ? 'bg-yellow-900/30 text-yellow-200'
                      : entry.includes('writer')
                      ? 'bg-green-900/30 text-green-200'
                      : entry.includes('verifier')
                      ? 'bg-teal-900/30 text-teal-200'
                      : entry.includes('error')
                      ? 'bg-red-900/30 text-red-200'
                      : 'bg-gray-700/30 text-gray-300'
                  }`}
                >
                  {entry}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded-lg">
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}

export default ProcessingView
