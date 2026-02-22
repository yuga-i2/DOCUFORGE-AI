import React, { useEffect, useState } from "react";
import axios from "axios";

export default function EvalDashboard() {
  const [history, setHistory] = useState([]);
  const [trend, setTrend] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [historyRes, trendRes] = await Promise.all([
          axios.get("/api/v1/eval/history?limit=20"),
          axios.get("/api/v1/eval/trend?days=30"),
        ]);

        setHistory(historyRes.data.results || []);
        setTrend(trendRes.data);
        setError(null);
      } catch (err) {
        setError(err.message);
        setHistory([]);
        setTrend(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-400">Loading evaluation metrics...</div>
      </div>
    );
  }

  const stats = trend
    ? {
        meanAccuracy:
          (trend.accuracy_scores || []).reduce((a, b) => a + b, 0) /
            (trend.accuracy_scores || []).length || 0,
        meanFaithfulness:
          (trend.faithfulness_scores || []).reduce((a, b) => a + b, 0) /
            (trend.faithfulness_scores || []).length || 0,
        totalEvals: history.length,
        passed: history.filter((h) => h.accuracy_score >= 0.7).length,
      }
    : { meanAccuracy: 0, meanFaithfulness: 0, totalEvals: 0, passed: 0 };

  const StatCard = ({ label, value, color }) => (
    <div className={`rounded-lg border p-4 ${color}`}>
      <div className="text-sm font-medium text-gray-300">{label}</div>
      <div className="text-2xl font-bold text-white mt-2">
        {typeof value === "number" ? value.toFixed(3) : value}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg border border-red-500 bg-red-950 p-4">
          <div className="text-sm text-red-200">Error: {error}</div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Mean Accuracy"
          value={stats.meanAccuracy}
          color="border-green-800 bg-green-950"
        />
        <StatCard
          label="Mean Faithfulness"
          value={stats.meanFaithfulness}
          color="border-blue-800 bg-blue-950"
        />
        <StatCard
          label="Total Evaluations"
          value={stats.totalEvals}
          color="border-purple-800 bg-purple-950"
        />
        <StatCard
          label="Pass Count (≥0.7)"
          value={stats.passed}
          color="border-indigo-800 bg-indigo-950"
        />
      </div>

      {/* Trend Chart */}
      {trend && trend.dates && trend.dates.length > 0 && (
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <h3 className="text-sm font-semibold text-white mb-4">
            30-Day Trend
          </h3>
          <div className="space-y-2 text-xs text-gray-400">
            <div className="flex justify-between">
              <span>Accuracy:</span>
              <span className="text-green-400">
                {trend.accuracy_scores[0]?.toFixed(3) || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Faithfulness:</span>
              <span className="text-blue-400">
                {trend.faithfulness_scores[0]?.toFixed(3) || "—"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* History Table */}
      <div className="rounded-lg border border-gray-700 bg-gray-900 overflow-hidden">
        <table className="w-full text-sm text-gray-300">
          <thead className="bg-gray-800 border-b border-gray-700">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Eval ID</th>
              <th className="px-4 py-2 text-left font-medium">Accuracy</th>
              <th className="px-4 py-2 text-left font-medium">Faithfulness</th>
              <th className="px-4 py-2 text-left font-medium">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {history.length > 0 ? (
              history.slice(0, 10).map((result) => (
                <tr key={result.eval_id} className="hover:bg-gray-800">
                  <td className="px-4 py-2 font-mono text-xs">
                    {result.eval_id.substring(0, 8)}...
                  </td>
                  <td
                    className={`px-4 py-2 font-semibold ${
                      result.accuracy_score >= 0.85
                        ? "text-green-400"
                        : result.accuracy_score >= 0.7
                          ? "text-yellow-400"
                          : "text-red-400"
                    }`}
                  >
                    {result.accuracy_score.toFixed(3)}
                  </td>
                  <td
                    className={`px-4 py-2 font-semibold ${
                      result.faithfulness_score >= 0.85
                        ? "text-green-400"
                        : result.faithfulness_score >= 0.7
                          ? "text-yellow-400"
                          : "text-red-400"
                    }`}
                  >
                    {result.faithfulness_score.toFixed(3)}
                  </td>
                  <td className="px-4 py-2 text-gray-400 text-xs">
                    {new Date(result.ran_at).toLocaleString()}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center text-gray-400">
                  No evaluations yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Run Evaluation Button */}
      <div className="flex gap-2">
        <button className="flex-1 rounded-lg bg-brand-500 px-4 py-2 font-semibold text-white hover:bg-brand-600 transition">
          Run New Evaluation
        </button>
        <button className="flex-1 rounded-lg border border-gray-700 px-4 py-2 font-semibold text-gray-300 hover:bg-gray-800 transition">
          Export Results
        </button>
      </div>
    </div>
  );
}
