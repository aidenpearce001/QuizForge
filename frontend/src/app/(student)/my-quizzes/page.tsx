"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type MyQuiz = {
  quiz_id: string;
  session_id: string;
  session_title: string;
  started_at: string;
  submitted_at: string | null;
  score: number | null;
  total_correct: number | null;
  total_questions: number;
};

function scoreColor(pct: number) {
  if (pct >= 80) return "text-green-400";
  if (pct >= 50) return "text-yellow-400";
  return "text-red-400";
}

function scoreBg(pct: number) {
  if (pct >= 80) return "bg-green-400";
  if (pct >= 50) return "bg-yellow-400";
  return "bg-red-400";
}

export default function MyQuizzesPage() {
  const { user, loading: authLoading } = useAuth();
  const [quizzes, setQuizzes] = useState<MyQuiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user || user.role !== "student") {
      setError("Please log in as a student to view your quizzes.");
      setLoading(false);
      return;
    }
    api
      .getMyQuizzes()
      .then(setQuizzes)
      .catch(() => setError("Failed to load quizzes"))
      .finally(() => setLoading(false));
  }, [user, authLoading]);

  const handleDelete = async (quizId: string) => {
    if (!confirm("Delete this practice quiz? This cannot be undone.")) return;
    setDeleting(quizId);
    try {
      await api.deletePracticeQuiz(quizId);
      setQuizzes((prev) => prev.filter((q) => q.quiz_id !== quizId));
    } catch {
      alert("Failed to delete quiz");
    }
    setDeleting(null);
  };

  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="h-8 w-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">{error}</p>
      </div>
    );
  }

  const isPractice = (q: MyQuiz) => q.session_title.startsWith("Practice");
  const submitted = quizzes.filter((q) => q.submitted_at);
  const inProgress = quizzes.filter((q) => !q.submitted_at);
  const sessionQuizzes = submitted.filter((q) => !isPractice(q));
  const practiceQuizzes = submitted.filter((q) => isPractice(q));

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Quizzes</h1>

        {quizzes.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-lg mb-2">No quizzes yet</p>
            <p className="text-gray-600 text-sm mb-4">Join a session via QR code or generate a practice quiz</p>
            <Link
              href="/practice"
              className="text-sm bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 font-medium transition-colors"
            >
              Start Practice Quiz
            </Link>
          </div>
        )}

        {/* In-progress quizzes */}
        {inProgress.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
              In Progress
            </h2>
            <div className="flex flex-col gap-3">
              {inProgress.map((q) => (
                <div
                  key={q.quiz_id}
                  className="bg-gray-900 border border-yellow-500/20 rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-gray-100 font-medium truncate">{q.session_title}</p>
                      {isPractice(q) && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-400 shrink-0">Practice</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Started {new Date(q.started_at).toLocaleDateString()} &middot; {q.total_questions} questions
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    <Link
                      href={`/quiz/${q.quiz_id}`}
                      className="text-sm bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 font-medium transition-colors"
                    >
                      Continue
                    </Link>
                    {isPractice(q) && (
                      <button
                        onClick={() => handleDelete(q.quiz_id)}
                        disabled={deleting === q.quiz_id}
                        className="text-xs text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded px-3 py-1.5 transition-colors disabled:opacity-40"
                      >
                        {deleting === q.quiz_id ? "..." : "Delete"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Session quizzes */}
        {sessionQuizzes.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
              Session Quizzes
            </h2>
            <div className="flex flex-col gap-3">
              {sessionQuizzes.map((q) => {
                const score = Math.round(q.score ?? 0);
                return (
                  <div
                    key={q.quiz_id}
                    className="bg-gray-900 border border-gray-800 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-100 font-medium truncate">{q.session_title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {new Date(q.submitted_at!).toLocaleDateString()} &middot; {q.total_correct}/{q.total_questions} correct
                        </p>
                      </div>
                      <span className={`text-2xl font-bold ${scoreColor(score)} shrink-0 ml-4`}>
                        {score}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-3">
                      <div
                        className={`h-full rounded-full ${scoreBg(score)}`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/results/${q.quiz_id}`}
                        className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded px-3 py-1.5 transition-colors"
                      >
                        Review Q&A
                      </Link>
                      <Link
                        href={`/leaderboard/${q.session_id}`}
                        className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded px-3 py-1.5 transition-colors"
                      >
                        Leaderboard
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Practice quizzes */}
        {practiceQuizzes.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
                Practice Quizzes
              </h2>
              <Link
                href="/practice"
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                New practice +
              </Link>
            </div>
            <div className="flex flex-col gap-3">
              {practiceQuizzes.map((q) => {
                const score = Math.round(q.score ?? 0);
                return (
                  <div
                    key={q.quiz_id}
                    className="bg-gray-900 border border-gray-800 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-gray-100 font-medium truncate">{q.session_title}</p>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-400 shrink-0">Practice</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {new Date(q.submitted_at!).toLocaleDateString()} &middot; {q.total_correct}/{q.total_questions} correct
                        </p>
                      </div>
                      <span className={`text-2xl font-bold ${scoreColor(score)} shrink-0 ml-4`}>
                        {score}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-3">
                      <div
                        className={`h-full rounded-full ${scoreBg(score)}`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/results/${q.quiz_id}`}
                        className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded px-3 py-1.5 transition-colors"
                      >
                        Review Q&A
                      </Link>
                      <button
                        onClick={() => handleDelete(q.quiz_id)}
                        disabled={deleting === q.quiz_id}
                        className="text-xs text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded px-3 py-1.5 transition-colors disabled:opacity-40"
                      >
                        {deleting === q.quiz_id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
