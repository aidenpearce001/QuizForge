"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

type ResultSummary = {
  avg_score: number;
  completed_count: number;
  total_students: number;
  avg_time_seconds: number;
  hardest_question?: string;
};

type StudentResult = {
  student_name: string;
  score: number;
  total: number;
  time_seconds: number;
  weakest_domain?: string;
};

type ResultsData = {
  session_title: string;
  summary: ResultSummary;
  students: StudentResult[];
};

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ResultsData | null>(null);
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    api.getResults(id).then(setData);
  }, [id]);

  if (!data) {
    return <p className="text-gray-400">Loading results...</p>;
  }

  const { summary, students } = data;
  const sorted = [...students].sort((a, b) =>
    sortAsc ? a.score - b.score : b.score - a.score
  );

  const scoreColor = (score: number, total: number) => {
    const pct = total > 0 ? score / total : 0;
    if (pct >= 0.8) return "text-green-400";
    if (pct >= 0.5) return "text-yellow-400";
    return "text-red-400";
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}m ${s}s`;
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">{data.session_title} - Results</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Avg Score</p>
          <p className="text-xl font-semibold text-gray-100">
            {summary.avg_score != null ? `${Math.round(summary.avg_score)}%` : "--"}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Completed</p>
          <p className="text-xl font-semibold text-gray-100">
            {summary.completed_count}/{summary.total_students}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Avg Time</p>
          <p className="text-xl font-semibold text-gray-100">
            {summary.avg_time_seconds ? formatTime(summary.avg_time_seconds) : "--"}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Hardest Question</p>
          <p className="text-sm font-medium text-gray-100 truncate">
            {summary.hardest_question || "--"}
          </p>
        </div>
      </div>

      {/* Student table */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
              <th className="text-left p-3">Student</th>
              <th
                className="text-left p-3 cursor-pointer hover:text-gray-300"
                onClick={() => setSortAsc(!sortAsc)}
              >
                Score {sortAsc ? "\u25B2" : "\u25BC"}
              </th>
              <th className="text-left p-3">Time</th>
              <th className="text-left p-3">Weakest Domain</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s, i) => (
              <tr key={i} className="border-b border-gray-800 last:border-0">
                <td className="p-3 text-gray-200">{s.student_name}</td>
                <td className={`p-3 font-medium ${scoreColor(s.score, s.total)}`}>
                  {s.score}/{s.total}
                </td>
                <td className="p-3 text-gray-400">{formatTime(s.time_seconds)}</td>
                <td className="p-3 text-gray-400">{s.weakest_domain || "--"}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={4} className="p-3 text-gray-500 text-center">
                  No results yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
