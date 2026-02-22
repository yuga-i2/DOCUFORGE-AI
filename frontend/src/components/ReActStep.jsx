import React, { useState, useEffect } from 'react';

const AGENT_COLORS = {
  supervisor_agent: {
    bg: 'bg-purple-50',
    border: 'border-purple-300',
    badge: 'bg-purple-100 text-purple-700',
    icon: 'text-purple-600',
  },
  ingestion_agent: {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    badge: 'bg-blue-100 text-blue-700',
    icon: 'text-blue-600',
  },
  rag_agent: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-300',
    badge: 'bg-indigo-100 text-indigo-700',
    icon: 'text-indigo-600',
  },
  research_agent: {
    bg: 'bg-cyan-50',
    border: 'border-cyan-300',
    badge: 'bg-cyan-100 text-cyan-700',
    icon: 'text-cyan-600',
  },
  analyst_agent: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    badge: 'bg-amber-100 text-amber-700',
    icon: 'text-amber-600',
  },
  writer_agent: {
    bg: 'bg-green-50',
    border: 'border-green-300',
    badge: 'bg-green-100 text-green-700',
    icon: 'text-green-600',
  },
  verifier_agent: {
    bg: 'bg-teal-50',
    border: 'border-teal-300',
    badge: 'bg-teal-100 text-teal-700',
    icon: 'text-teal-600',
  },
};

const DEFAULT_COLORS = {
  bg: 'bg-gray-50',
  border: 'border-gray-300',
  badge: 'bg-gray-100 text-gray-700',
  icon: 'text-gray-600',
};

const ReActStep = ({ 
  stepNumber, 
  agentName, 
  thought, 
  action, 
  observation, 
  animationDelay = 0 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, animationDelay);
    return () => clearTimeout(timer);
  }, [animationDelay]);

  const colors = AGENT_COLORS[agentName] || DEFAULT_COLORS;

  // Format agent name for display (remove _agent suffix, capitalize)
  const displayName = agentName
    .replace('_agent', '')
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return (
    <div
      className={`transform transition-all duration-500 ${
        isVisible
          ? 'opacity-100 translate-y-0'
          : 'opacity-0 translate-y-4'
      }`}
    >
      <div className={`border-l-4 ${colors.border} ${colors.bg} p-4 rounded-r-lg mb-4`}>
        {/* Header: Step number and agent badge */}
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-white font-semibold text-sm text-gray-700">
            {stepNumber}
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors.badge}`}>
            {displayName}
          </span>
        </div>

        {/* Thought section */}
        {thought && (
          <div className="mb-3">
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              💭 Thought
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed">{thought}</p>
          </div>
        )}

        {/* Action section */}
        {action && (
          <div className="mb-3">
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              ⚡ Action
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed font-mono bg-white/50 p-2 rounded">
              {action}
            </p>
          </div>
        )}

        {/* Observation section */}
        {observation && (
          <div>
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              👁️ Observation
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed">
              {observation.substring(0, 200)}
              {observation.length > 200 ? '...' : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReActStep;
