import React, { useState, useEffect } from 'react';

const MetricBar = ({ label, score, showPercentage = true }) => {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    // Animate from 0 to actual score
    const timer = setTimeout(() => {
      setDisplayScore(score);
    }, 100);
    return () => clearTimeout(timer);
  }, [score]);

  // Determine color based on score
  const getColor = () => {
    if (score >= 0.85) return 'bg-green-500';
    if (score >= 0.70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTextColor = () => {
    if (score >= 0.85) return 'text-green-700';
    if (score >= 0.70) return 'text-yellow-700';
    return 'text-red-700';
  };

  const percentage = Math.round(score * 100);

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-semibold text-gray-700">{label}</label>
        {showPercentage && (
          <span className={`text-sm font-bold ${getTextColor()}`}>
            {percentage}%
          </span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-full ${getColor()} transition-all duration-1000 ease-out`}
          style={{ width: `${displayScore * 100}%` }}
        />
      </div>
    </div>
  );
};

export default MetricBar;
