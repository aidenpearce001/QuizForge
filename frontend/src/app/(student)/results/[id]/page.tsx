"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

type DomainScore = {
  domain_name: string;
  correct: number;
  total: number;
};

type ReviewQuestion = {
  number: number;
  text: string;
  domain_name: string;
  choices: { index: number; text: string; is_correct: boolean }[];
  selected_choices: number[];
  explanation: string;
};

type Results = {
  score_percent: number;
  correct_count: number;
  total_questions: number;
  time_taken_seconds: number;
  domain_scores: DomainScore[];
  questions: ReviewQuestion[];
};

export default function ResultsPage() {
  const params = useParams();
  const quizId = params.id as string;

  const [results, setResults] = useState<Results | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchResults() {
      try {
        // Try submitting first (will return results or fail if already submitted)
        const data = await api.submitQuiz(quizId);
        setResults(data);
      } catch {
        try {
          // Already submitted - fetch meta which may have results
          const meta = await api.getQuizMeta(quizId);
          if (meta.results) {
            setResults(meta.results);
          } else {
            setError("Could not load results");
          }
        } catch {
          setError("Could not load results");
        }
      } finally {
        setLoading(false);
      }
    }
    fetchResults();
  }, [quizId]);

  function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  function scoreColor(pct: number) {
    if (pct >= 70) return "text-green-400";
    if (pct >= 50) return "text-yellow-400";
    return "text-red-400";
  }

  function scoreBgColor(pct: number) {
    if (pct >= 70) return "bg-green-400";
    if (pct >= 50) return "bg-yellow-400";
    return "bg-red-400";
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading results...</p>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-red-400 text-lg">{error || "Results not available"}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Score Header */}
        <div className="text-center mb-10">
          <h1 className="text-lg text-gray-400 mb-2">Quiz Complete</h1>
          <p className={`text-7xl font-bold ${scoreColor(results.score_percent)}`}>
            {Math.round(results.score_percent)}%
          </p>
          <p className="text-gray-400 mt-3">
            {results.correct_count} of {results.total_questions} correct
            {results.time_taken_seconds > 0 && (
              <span> &middot; {formatTime(results.time_taken_seconds)}</span>
            )}
          </p>
        </div>

        {/* Domain Breakdown */}
        {results.domain_scores && results.domain_scores.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-10">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Score by Domain</h2>
            <div className="space-y-3">
              {results.domain_scores.map((ds) => {
                const pct = ds.total > 0 ? Math.round((ds.correct / ds.total) * 100) : 0;
                return (
                  <div key={ds.domain_name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{ds.domain_name}</span>
                      <span className="text-gray-400">{ds.correct}/{ds.total}</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${scoreBgColor(pct)}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Question Review */}
        {results.questions && results.questions.length > 0 && (
          <div>
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Question Review</h2>
            <div className="space-y-6">
              {results.questions.map((q) => {
                const isCorrect = q.choices
                  .filter((c) => c.is_correct)
                  .every((c) => q.selected_choices.includes(c.index)) &&
                  q.selected_choices.every((s) => q.choices.find((c) => c.index === s)?.is_correct);

                return (
                  <div key={q.number} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
                    <div className="flex items-start gap-3 mb-3">
                      <span
                        className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          isCorrect ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {q.number}
                      </span>
                      <p className="text-gray-200 leading-relaxed">{q.text}</p>
                    </div>

                    <div className="space-y-2 ml-9 mb-3">
                      {q.choices.map((c) => {
                        const wasSelected = q.selected_choices.includes(c.index);
                        const isRight = c.is_correct;
                        let borderClass = "border-gray-800";
                        let bgClass = "bg-gray-950";

                        if (isRight) {
                          borderClass = "border-green-500/50";
                          bgClass = "bg-green-500/10";
                        } else if (wasSelected && !isRight) {
                          borderClass = "border-red-500/50";
                          bgClass = "bg-red-500/10";
                        }

                        return (
                          <div
                            key={c.index}
                            className={`px-4 py-2.5 rounded-lg border text-sm ${borderClass} ${bgClass}`}
                          >
                            <span className="font-medium text-gray-500 mr-2">
                              {String.fromCharCode(65 + c.index)}.
                            </span>
                            <span className={isRight ? "text-green-300" : wasSelected ? "text-red-300" : "text-gray-400"}>
                              {c.text}
                            </span>
                            {wasSelected && (
                              <span className="ml-2 text-xs text-gray-500">(your answer)</span>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {q.explanation && (
                      <p className="ml-9 text-sm text-gray-400 bg-gray-800/50 rounded-lg p-3">
                        {q.explanation}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Back link */}
        <div className="text-center mt-10">
          <a href="/study" className="text-blue-400 hover:text-blue-300 text-sm">
            Go to Study Cards
          </a>
        </div>
      </div>
    </div>
  );
}
