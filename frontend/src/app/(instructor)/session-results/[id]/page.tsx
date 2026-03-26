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

type QuestionStat = {
  question_id: string;
  question_text: string;
  correct_rate: number;
  total_attempts: number;
  correct_count: number;
  correct_students: string[];
  incorrect_students: string[];
};

type ReviewQuestion = {
  question_id: string;
  question_text: string;
  question_type: string;
  domain_name: string;
  choices: { text: string; is_correct: boolean }[];
  explanation: string | null;
  correct_rate: number | null;
  total_attempts: number;
  correct_count: number;
  correct_students: string[];
  incorrect_students: string[];
};

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [results, setResults] = useState<StudentResult[]>([]);
  const [questionStats, setQuestionStats] = useState<QuestionStat[]>([]);
  const [reviewQuestions, setReviewQuestions] = useState<ReviewQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortAsc, setSortAsc] = useState(false);
  const [error, setError] = useState("");
  const [hardestQuestion, setHardestQuestion] = useState<QuestionStat | null>(null);
  const [showStatsModal, setShowStatsModal] = useState<QuestionStat | null>(null);
  const [tab, setTab] = useState<"students" | "questions" | "review">("students");
  const [reviewLoading, setReviewLoading] = useState(false);

  useEffect(() => {
    api
      .getResults(id)
      .then((data: any) => {
        if (Array.isArray(data)) {
          setResults(data);
        } else {
          setResults(data.results || []);
          setHardestQuestion(data.hardest_question || null);
          setQuestionStats(data.question_stats || []);
        }
      })
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const loadReview = () => {
    if (reviewQuestions.length > 0) { setTab("review"); return; }
    setReviewLoading(true);
    api.getSessionQuestionsReview(id)
      .then((data: any) => {
        setReviewQuestions(data.questions || []);
        setTab("review");
      })
      .catch(() => {})
      .finally(() => setReviewLoading(false));
  };

  if (loading) return <p className="text-gray-400 p-6">Loading results...</p>;
  if (error) return <p className="text-red-400 p-6">Error: {error}</p>;

  const sorted = [...results].sort((a, b) =>
    sortAsc ? a.score - b.score : b.score - a.score
  );

  const avgScore = results.length > 0
    ? results.reduce((sum, r) => sum + r.score, 0) / results.length : 0;
  const avgTime = results.length > 0
    ? results.reduce((sum, r) => sum + (r.time_taken_seconds || 0), 0) / results.length : 0;

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
        if (pct < worstPct) { worstPct = pct; worst = name; }
      }
    }
    return worst || "--";
  };

  const rateBg = (rate: number) => {
    if (rate >= 80) return "bg-green-500";
    if (rate >= 50) return "bg-yellow-500";
    return "bg-red-500";
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
        <button
          onClick={() => hardestQuestion && setShowStatsModal(hardestQuestion)}
          className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-left hover:border-red-500/30 transition-colors"
        >
          <p className="text-xs text-gray-500 uppercase">Hardest Question</p>
          <p className={`text-sm font-medium truncate ${hardestQuestion ? scoreColor(hardestQuestion.correct_rate) : "text-gray-500"}`}>
            {hardestQuestion ? `${Math.round(hardestQuestion.correct_rate)}% correct` : "--"}
          </p>
          {hardestQuestion && (
            <p className="text-xs text-gray-500 truncate mt-1">{hardestQuestion.question_text}</p>
          )}
          {hardestQuestion && <p className="text-xs text-blue-400 mt-1">Click to see details →</p>}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab("students")}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            tab === "students" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"
          }`}
        >
          Students
        </button>
        <button
          onClick={() => setTab("questions")}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            tab === "questions" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"
          }`}
        >
          Question Stats
        </button>
        <button
          onClick={loadReview}
          disabled={reviewLoading}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            tab === "review" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"
          }`}
        >
          {reviewLoading ? "Loading..." : "Questions & Answers"}
        </button>
      </div>

      {/* Tab: Students */}
      {tab === "students" && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3">Student</th>
                <th className="text-left p-3 cursor-pointer hover:text-gray-300" onClick={() => setSortAsc(!sortAsc)}>
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
                  <td className={`p-3 font-medium ${scoreColor(s.score)}`}>{Math.round(s.score)}%</td>
                  <td className="p-3 text-gray-400">{s.total_correct}/{s.total_questions}</td>
                  <td className="p-3 text-gray-400">{formatTime(s.time_taken_seconds)}</td>
                  <td className="p-3 text-gray-400">{getWeakestDomain(s.domain_scores)}</td>
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr><td colSpan={5} className="p-3 text-gray-500 text-center">No results yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Question Stats */}
      {tab === "questions" && (
        <div className="flex flex-col gap-3">
          {questionStats.map((q, i) => (
            <button
              key={q.question_id}
              onClick={() => setShowStatsModal(q)}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-left hover:border-gray-600 transition-colors"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs text-gray-500 font-mono">#{i + 1}</span>
                <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${rateBg(q.correct_rate)}`} style={{ width: `${q.correct_rate}%` }} />
                </div>
                <span className={`text-sm font-bold ${scoreColor(q.correct_rate)}`}>{Math.round(q.correct_rate)}%</span>
              </div>
              <p className="text-sm text-gray-300 line-clamp-2">{q.question_text}</p>
              <p className="text-xs text-gray-500 mt-1">{q.correct_count}/{q.total_attempts} correct</p>
            </button>
          ))}
          {questionStats.length === 0 && (
            <p className="text-gray-500 text-center py-4">No question data available.</p>
          )}
        </div>
      )}

      {/* Tab: Questions & Answers (full review) */}
      {tab === "review" && (
        <div className="flex flex-col gap-6">
          {reviewQuestions.map((q, i) => (
            <div key={q.question_id} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
              <div className="flex items-start gap-3 mb-3">
                <span className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  q.correct_rate !== null && q.correct_rate >= 70 ? "bg-green-500/20 text-green-400" :
                  q.correct_rate !== null && q.correct_rate >= 40 ? "bg-yellow-500/20 text-yellow-400" :
                  "bg-red-500/20 text-red-400"
                }`}>
                  {i + 1}
                </span>
                <div className="flex-1">
                  <p className="text-gray-200 leading-relaxed">{q.question_text}</p>
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-400">{q.domain_name}</span>
                    {q.correct_rate !== null && (
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        q.correct_rate >= 70 ? "bg-green-900/30 text-green-400" :
                        q.correct_rate >= 40 ? "bg-yellow-900/30 text-yellow-400" :
                        "bg-red-900/30 text-red-400"
                      }`}>
                        {Math.round(q.correct_rate)}% correct ({q.correct_count}/{q.total_attempts})
                      </span>
                    )}
                  </div>
                </div>
              </div>
              {/* Choices */}
              <div className="space-y-2 ml-11 mb-3">
                {q.choices.map((c, ci) => (
                  <div
                    key={ci}
                    className={`px-4 py-2 rounded-lg border text-sm ${
                      c.is_correct
                        ? "border-green-500/50 bg-green-500/10 text-green-300"
                        : "border-gray-800 bg-gray-950 text-gray-400"
                    }`}
                  >
                    <span className="font-medium text-gray-500 mr-2">{String.fromCharCode(65 + ci)}.</span>
                    {c.text}
                    {c.is_correct && <span className="ml-2 text-green-400 text-xs">Correct</span>}
                  </div>
                ))}
              </div>
              {/* Explanation */}
              {q.explanation && (
                <div className="ml-11 text-sm text-gray-400 bg-gray-800/50 rounded-lg p-3">
                  {q.explanation}
                </div>
              )}
            </div>
          ))}
          {reviewQuestions.length === 0 && (
            <p className="text-gray-500 text-center py-4">No questions to review.</p>
          )}
        </div>
      )}

      {/* Modal: Question Stats Detail */}
      {showStatsModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setShowStatsModal(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100">Question Analysis</h3>
              <button onClick={() => setShowStatsModal(null)} className="text-gray-500 hover:text-gray-300 text-xl">&times;</button>
            </div>
            <p className="text-gray-300 text-sm mb-4 leading-relaxed">{showStatsModal.question_text}</p>

            {/* Stats bar */}
            <div className="mb-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Correct rate</span>
                <span className={scoreColor(showStatsModal.correct_rate)}>{Math.round(showStatsModal.correct_rate)}%</span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${rateBg(showStatsModal.correct_rate)}`} style={{ width: `${showStatsModal.correct_rate}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">{showStatsModal.correct_count} of {showStatsModal.total_attempts} students answered correctly</p>
            </div>

            {/* Correct students */}
            <div className="mb-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Answered Correctly ({showStatsModal.correct_students.length})</p>
              {showStatsModal.correct_students.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {showStatsModal.correct_students.map((name, i) => (
                    <span key={i} className="text-xs bg-green-900/30 text-green-400 px-2 py-1 rounded">{name}</span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-600">No one</p>
              )}
            </div>

            {/* Incorrect students */}
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Answered Incorrectly ({showStatsModal.incorrect_students.length})</p>
              {showStatsModal.incorrect_students.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {showStatsModal.incorrect_students.map((name, i) => (
                    <span key={i} className="text-xs bg-red-900/30 text-red-400 px-2 py-1 rounded">{name}</span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-600">No one</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
