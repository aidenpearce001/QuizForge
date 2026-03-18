"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";

type StudentResult = {
  student_id: string;
  full_name: string;
  score: number;
  total_correct: number;
  total_questions: number;
  time_taken_seconds: number | null;
  domain_scores: Record<string, { correct: number; total: number }>;
};

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [results, setResults] = useState<StudentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortAsc, setSortAsc] = useState(false);
  const [error, setError] = useState("");

  const [hardestQuestion, setHardestQuestion] = useState<{ question_text: string; correct_rate: number } | null>(null);

  useEffect(() => {
    api
      .getResults(id)
      .then((data: any) => {
        // API returns {results: [...], hardest_question: {...}}
        if (Array.isArray(data)) {
          setResults(data);
        } else {
          setResults(data.results || []);
          setHardestQuestion(data.hardest_question || null);
        }
      })
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-400">Loading results...</p>;
  if (error) return <p className="text-red-400">Error: {error}</p>;

  const sorted = [...results].sort((a, b) =>
    sortAsc ? a.score - b.score : b.score - a.score
  );

  const avgScore = results.length > 0
    ? results.reduce((sum, r) => sum + r.score, 0) / results.length
    : 0;

  const avgTime = results.length > 0
    ? results.reduce((sum, r) => sum + (r.time_taken_seconds || 0), 0) / results.length
    : 0;

  const scoreColor = (pct: number) => {
    if (pct >= 80) return "text-green-400";
    if (pct >= 50) return "text-yellow-400";
    return "text-red-400";
  };

  const formatTime = (seconds: number | null) => {
    if (!seconds) return "--";
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}m ${s}s`;
  };

  const getWeakestDomain = (ds: Record<string, { correct: number; total: number }>) => {
    let worst = "";
    let worstPct = 1;
    for (const [name, { correct, total }] of Object.entries(ds)) {
      if (total > 0) {
        const pct = correct / total;
        if (pct < worstPct) {
          worstPct = pct;
          worst = name;
        }
      }
    }
    return worst || "--";
  };

  return (
    <div>
      <Link href="/dashboard" className="text-xs text-gray-500 hover:text-gray-300 mb-4 block">← Back to sessions</Link>
      <h1 className="text-2xl font-semibold mb-6">Session Results</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Avg Score</p>
          <p className={`text-xl font-semibold ${scoreColor(avgScore)}`}>
            {results.length > 0 ? `${Math.round(avgScore)}%` : "--"}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Completed</p>
          <p className="text-xl font-semibold text-gray-100">{results.length}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Avg Time</p>
          <p className="text-xl font-semibold text-gray-100">{formatTime(avgTime)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase">Hardest Question</p>
          <p className="text-sm font-medium text-gray-100 truncate">
            {hardestQuestion ? `${Math.round(hardestQuestion.correct_rate * 100)}% correct` : "--"}
          </p>
          {hardestQuestion && (
            <p className="text-xs text-gray-500 truncate mt-1">{hardestQuestion.question_text}</p>
          )}
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
              <th className="text-left p-3">Correct</th>
              <th className="text-left p-3">Time</th>
              <th className="text-left p-3">Weakest Domain</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => (
              <tr key={s.student_id} className="border-b border-gray-800 last:border-0">
                <td className="p-3 text-gray-200">{s.full_name}</td>
                <td className={`p-3 font-medium ${scoreColor(s.score)}`}>
                  {Math.round(s.score)}%
                </td>
                <td className="p-3 text-gray-400">{s.total_correct}/{s.total_questions}</td>
                <td className="p-3 text-gray-400">{formatTime(s.time_taken_seconds)}</td>
                <td className="p-3 text-gray-400">{getWeakestDomain(s.domain_scores)}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={5} className="p-3 text-gray-500 text-center">
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
