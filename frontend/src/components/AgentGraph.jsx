import React, { useCallback, useMemo } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'

// AgentGraph: Displays agent execution nodes in a pipeline graph with status visualization
function AgentGraph({ agentTrace, isProcessing }) {
  const AGENT_NODES = [
    {
      id: 'supervisor',
      data: { label: '🧭 Supervisor' },
      position: { x: 250, y: 0 },
    },
    {
      id: 'ingestion',
      data: { label: '📥 Ingestion' },
      position: { x: 0, y: 100 },
    },
    {
      id: 'rag',
      data: { label: '📚 RAG' },
      position: { x: 250, y: 100 },
    },
    {
      id: 'research',
      data: { label: '🌐 Research' },
      position: { x: 500, y: 100 },
    },
    {
      id: 'analyst',
      data: { label: '📊 Analyst' },
      position: { x: 125, y: 200 },
    },
    {
      id: 'writer',
      data: { label: '✍️ Writer' },
      position: { x: 375, y: 200 },
    },
    {
      id: 'verifier',
      data: { label: '🛡️ Verifier' },
      position: { x: 250, y: 300 },
    },
  ]

  const AGENT_EDGES = [
    { id: 'super-ingestion', source: 'supervisor', target: 'ingestion' },
    { id: 'super-rag', source: 'supervisor', target: 'rag' },
    { id: 'super-research', source: 'supervisor', target: 'research' },
    { id: 'ingestion-analyst', source: 'ingestion', target: 'analyst' },
    { id: 'rag-analyst', source: 'rag', target: 'analyst' },
    { id: 'research-analyst', source: 'research', target: 'analyst' },
    { id: 'analyst-writer', source: 'analyst', target: 'writer' },
    { id: 'writer-verifier', source: 'writer', target: 'verifier' },
  ]

  // Determine node status based on agent trace
  const nodes = useMemo(() => {
    return AGENT_NODES.map((node) => {
      const agentName = node.id.toLowerCase()
      const isInTrace = agentTrace.some((entry) => entry.toLowerCase().includes(agentName))
      const isLastAgent =
        agentTrace.length > 0 &&
        agentTrace[agentTrace.length - 1].toLowerCase().includes(agentName)

      let style = {
        background: '#1e293b',
        border: '2px solid #475569',
        color: '#e2e8f0',
        borderRadius: '8px',
        padding: '16px',
        fontSize: '12px',
        minWidth: '100px',
        textAlign: 'center',
        fontWeight: '600',
        transition: 'all 0.3s ease',
      }

      if (isInTrace && !isLastAgent) {
        style.border = '2px solid #22c55e'
        style.background = '#1b4332'
      }

      if (isLastAgent && isProcessing) {
        style.border = '2px solid #3b82f6'
        style.background = '#1e3a8a'
        style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.5)'
        style.animation = 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      }

      return {
        ...node,
        style,
      }
    })
  }, [agentTrace, isProcessing])

  return (
    <div className="w-full h-96 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <ReactFlow nodes={nodes} edges={AGENT_EDGES}>
        <Background color="#374151" gap={12} />
        <Controls />
      </ReactFlow>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </div>
  )
}

export default AgentGraph
