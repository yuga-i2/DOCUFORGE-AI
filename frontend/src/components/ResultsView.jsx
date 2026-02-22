import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Download, RefreshCw, FileText, Zap, Lightbulb, BarChart3 } from 'lucide-react'
import ReActStep from './ReActStep'
import MetricBar from './MetricBar'

// ResultsView: Comprehensive results display with 4 tabs (Report, ReAct, Prompts, Metrics)
function ResultsView({ sessionId, taskResult, onReset }) {
  const [activeTab, setActiveTab] = useState('report') // 'report' | 'react' | 'prompts' | 'metrics'
  const [prompts, setPrompts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showDiff, setShowDiff] = useState(false)

  // Fetch prompts on mount
  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        const response = await axios.get('/api/v1/prompts')
        setPrompts(response.data.prompts)
      } catch (err) {
        console.error('Failed to fetch prompts:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchPrompts()
  }, [])

  if (!taskResult) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <p className="text-gray-400 mb-4">No results available</p>
          <button
            onClick={onReset}
            className="bg-brand-500 text-white px-6 py-2 rounded-lg hover:bg-brand-500/90 transition"
          >
            Back to Upload
          </button>
        </div>
      </div>
    )
  }

  // Parse verified report
  const parseReport = (reportText) => {
    try {
      if (typeof reportText === 'string') {
        return JSON.parse(reportText)
      }
      return reportText
    } catch {
      return null
    }
  }

  const report = parseReport(taskResult.verified_report)
  const agentTrace = taskResult.agent_trace || []

  // Parse ReAct steps from agent trace
  const parseReActSteps = () => {
    const steps = []
    let currentAgent = null
    let currentThought = null
    let currentAction = null
    let currentObservation = null

    agentTrace.forEach((line) => {
      // Extract agent name
      if (line.includes('_agent:')) {
        if (currentAgent) {
          steps.push({
            agent: currentAgent,
            thought: currentThought || '',
            action: currentAction || '',
            observation: currentObservation || '',
          })
        }
        const agentMatch = line.match(/(\w+_agent):/)
        currentAgent = agentMatch ? agentMatch[1] : 'unknown'
        currentThought = null
        currentAction = null
        currentObservation = null
      } else if (line.includes('Thought:')) {
        currentThought = line.replace(/.*Thought:\s*/i, '').trim()
      } else if (line.includes('Action:')) {
        currentAction = line.replace(/.*Action:\s*/i, '').trim()
      } else if (line.includes('Observation:')) {
        currentObservation = line.replace(/.*Observation:\s*/i, '').trim()
      }
    })

    // Add last step
    if (currentAgent) {
      steps.push({
        agent: currentAgent,
        thought: currentThought || '',
        action: currentAction || '',
        observation: currentObservation || '',
      })
    }

    return steps
  }

  const reactSteps = parseReActSteps()

  const handleDownload = () => {
    const content = report ? JSON.stringify(report, null, 2) : taskResult.verified_report
    const element = document.createElement('a')
    element.setAttribute(
      'href',
      `data:text/plain;charset=utf-8,${encodeURIComponent(content)}`
    )
    element.setAttribute('download', `report_${sessionId}.txt`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  // Tab icons and labels
  const tabs = [
    { id: 'report', label: 'Report', icon: FileText },
    { id: 'react', label: 'ReAct Pattern', icon: Zap },
    { id: 'prompts', label: 'Prompt Versions', icon: Lightbulb },
    { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-100">Analysis Results</h1>
          <div className="flex gap-3">
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              <Download size={18} />
              Download
            </button>
            <button
              onClick={onReset}
              className="flex items-center gap-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition"
            >
              <RefreshCw size={18} />
              New Analysis
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8 border-b border-gray-700">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-3 font-medium transition border-b-2 ${
                activeTab === id
                  ? 'text-brand-400 border-brand-400'
                  : 'text-gray-400 border-transparent hover:text-gray-300'
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-gray-800/50 rounded-lg p-8">
          {/* Report Tab */}
          {activeTab === 'report' && (
            <div className="space-y-6">
              {report ? (
                <>
                  {/* Confidence Badge */}
                  {report.overall_confidence !== undefined && (
                    <div className="flex items-center gap-4 p-4 bg-blue-900/30 rounded-lg border border-blue-700">
                      <div className="flex-1">
                        <p className="text-sm text-blue-200">Overall Confidence</p>
                        <p className="text-2xl font-bold text-blue-400">
                          {Math.round(report.overall_confidence * 100)}%
                        </p>
                      </div>
                      <div className="flex gap-6 text-sm">
                        {report.has_web_context !== undefined && (
                          <div className="text-center">
                            <p className="text-gray-400">Web Context</p>
                            <p className="font-semibold text-gray-200">
                              {report.has_web_context ? '✓' : '✗'}
                            </p>
                          </div>
                        )}
                        {report.has_analysis !== undefined && (
                          <div className="text-center">
                            <p className="text-gray-400">Analysis</p>
                            <p className="font-semibold text-gray-200">
                              {report.has_analysis ? '✓' : '✗'}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Report Sections */}
                  {report.sections && report.sections.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.map((section, idx) => (
                        <div
                          key={idx}
                          className="border-l-4 border-green-500 bg-green-900/20 p-4 rounded-r-lg"
                        >
                          <h3 className="font-semibold text-green-300 mb-2">
                            {section.title || `Section ${idx + 1}`}
                          </h3>
                          <p className="text-gray-300 text-sm leading-relaxed">
                            {section.content}
                          </p>
                          {section.citations && section.citations.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-green-500/30">
                              <p className="text-xs text-green-400 font-semibold mb-2">
                                Citations
                              </p>
                              <ul className="text-xs text-gray-400 space-y-1">
                                {section.citations.map((cite, i) => (
                                  <li key={i}>• {cite}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Fallback for raw report text */}
                  {!report.sections && (
                    <div className="bg-gray-700/30 p-4 rounded-lg font-mono text-sm text-gray-300 max-h-96 overflow-y-auto">
                      <pre>{JSON.stringify(report, null, 2)}</pre>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400 mb-4">Could not parse report</p>
                  <div className="bg-gray-700/30 p-4 rounded-lg font-mono text-sm text-gray-300 max-h-96 overflow-y-auto text-left">
                    <pre>{taskResult.verified_report}</pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ReAct Pattern Tab */}
          {activeTab === 'react' && (
            <div className="space-y-4">
              {reactSteps.length > 0 ? (
                reactSteps.map((step, idx) => (
                  <ReActStep
                    key={idx}
                    stepNumber={idx + 1}
                    agentName={step.agent}
                    thought={step.thought}
                    action={step.action}
                    observation={step.observation}
                    animationDelay={idx * 100}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400">No ReAct pattern data available</p>
                  {agentTrace.length > 0 && (
                    <div className="mt-6 bg-gray-700/30 p-4 rounded-lg max-h-96 overflow-y-auto">
                      {agentTrace.map((entry, idx) => (
                        <div key={idx} className="text-xs text-gray-400 mb-2 text-left font-mono">
                          {entry}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Prompts Tab */}
          {activeTab === 'prompts' && (
            <div className="space-y-4">
              {loading ? (
                <div className="text-center py-12">
                  <p className="text-gray-400">Loading prompts...</p>
                </div>
              ) : prompts ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {['v1', 'v2', 'v3'].map((version) => {
                    const prompt = prompts[version]
                    const isActive = prompt?.active
                    return (
                      <div
                        key={version}
                        className={`border rounded-lg p-4 ${
                          isActive
                            ? 'border-green-500 bg-green-900/20'
                            : 'border-gray-600 bg-gray-700/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-semibold text-gray-200">{version.toUpperCase()}</h3>
                          {isActive && (
                            <span className="px-2 py-1 bg-green-600 text-green-100 text-xs rounded">
                              Active
                            </span>
                          )}
                        </div>
                        <div
                          className="text-sm text-gray-400 bg-gray-900/50 p-3 rounded max-h-64 overflow-y-auto font-mono text-xs leading-relaxed"
                        >
                          {prompt?.content || `(${version} not found)`}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400">Failed to load prompts</p>
                </div>
              )}
            </div>
          )}

          {/* Metrics Tab */}
          {activeTab === 'metrics' && (
            <div className="space-y-8">
              {/* Score Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Faithfulness */}
                <div className="bg-gray-700/50 p-6 rounded-lg border border-gray-600">
                  <h3 className="font-semibold text-gray-200 mb-4">Faithfulness Score</h3>
                  <div className="text-3xl font-bold text-blue-400 mb-4">
                    {Math.round((taskResult.faithfulness_score || 0) * 100)}%
                  </div>
                  <MetricBar
                    label="Relevance to Source"
                    score={taskResult.faithfulness_score || 0}
                    showPercentage={false}
                  />
                </div>

                {/* Hallucination */}
                <div className="bg-gray-700/50 p-6 rounded-lg border border-gray-600">
                  <h3 className="font-semibold text-gray-200 mb-4">Hallucination Score</h3>
                  <div className="text-3xl font-bold text-red-400 mb-4">
                    {Math.round((taskResult.hallucination_score || 0) * 100)}%
                  </div>
                  <MetricBar
                    label="Error Rate"
                    score={1 - (taskResult.hallucination_score || 0)}
                    showPercentage={false}
                  />
                </div>
              </div>

              {/* Agent Information */}
              <div className="bg-gray-700/50 p-6 rounded-lg border border-gray-600">
                <h3 className="font-semibold text-gray-200 mb-4">Pipeline Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Agents Executed</p>
                    <p className="text-2xl font-bold text-gray-200">
                      {agentTrace.length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Session ID</p>
                    <p className="text-xs font-mono text-gray-400 truncate">
                      {taskResult.session_id}
                    </p>
                  </div>
                </div>
              </div>

              {/* Agent Timeline */}
              {agentTrace.length > 0 && (
                <div className="bg-gray-700/50 p-6 rounded-lg border border-gray-600">
                  <h3 className="font-semibold text-gray-200 mb-4">Execution Timeline</h3>
                  <div className="space-y-2">
                    {agentTrace.slice(0, 10).map((entry, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <div className="w-2 h-2 mt-2 rounded-full bg-blue-500 flex-shrink-0" />
                        <p className="text-xs text-gray-400 font-mono">
                          {entry.substring(0, 80)}
                          {entry.length > 80 ? '...' : ''}
                        </p>
                      </div>
                    ))}
                    {agentTrace.length > 10 && (
                      <p className="text-xs text-gray-500 ml-5">
                        ... and {agentTrace.length - 10} more steps
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResultsView
