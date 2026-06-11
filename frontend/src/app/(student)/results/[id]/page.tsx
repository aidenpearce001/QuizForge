"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { BilingualText } from "@/components/BilingualText";

function enOnly(s: string, sep: string) {
  const idx = s.indexOf(sep);
  return idx === -1 ? s : s.slice(0, idx);
}

const SCORE_COLORS = {
  high: { text: "text-green-400", bg: "bg-green-400" },
  mid:  { text: "text-yellow-400", bg: "bg-yellow-400" },
  low:  { text: "text-red-400",   bg: "bg-red-400"   },
} as const;

function scoreLevel(pct: number) {
  return pct >= 70 ? SCORE_COLORS.high : pct >= 50 ? SCORE_COLORS.mid : SCORE_COLORS.low;
}

type QuestionResult = {
  question_number: number;
  question_text: string;
  domain_name: string;
  choices: { text: string; is_correct: boolean }[];
  selected_choices: number[];
  is_correct: boolean;
  explanation: string | null;
};

type SubmitData = {
  score: number;
  total_correct: number;
  total_questions: number;
  results: QuestionResult[];
  session_id?: string;
};

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const quizId = params.id as string;

  const [data, setData] = useState<SubmitData | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  const isPractice = sessionTitle.startsWith("Practice");

  useEffect(() => {
    async function fetchResults() {
      try {
        // Try submitting (works if not yet submitted)
        const res = await api.submitQuiz(quizId);
        setData(res);
      } catch {
        // Already submitted — fetch results from GET endpoint
        try {
          const res = await api.getQuizResults(quizId);
          setData(res);
        } catch {
          setError("Could not load results. Please try again.");
        }
      }
      // Fetch session_id from quiz meta for leaderboard link
      try {
        const meta = await api.getQuizMeta(quizId);
        setSessionId(meta.session_id);
        setSessionTitle(meta.session_title || "");
      } catch {
        // Non-critical — leaderboard link just won't show
      }
      setLoading(false);
    }
    fetchResults();
  }, [quizId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading results...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center flex-col gap-4">
        <p className="text-gray-400 text-lg">{error || "Results not available"}</p>
        <a href="/study" className="text-blue-400 hover:text-blue-300 text-sm">
          Go to Study Cards →
        </a>
      </div>
    );
  }

  // Build domain breakdown from results
  const domainMap: Record<string, { correct: number; total: number }> = {};
  for (const q of data.results) {
    if (!domainMap[q.domain_name]) {
      domainMap[q.domain_name] = { correct: 0, total: 0 };
    }
    domainMap[q.domain_name].total++;
    if (q.is_correct) domainMap[q.domain_name].correct++;
  }
  const domainScores = Object.entries(domainMap).map(([name, s]) => ({ name, ...s }));

  function downloadResults() {
    if (!data) return;
    const date = new Date().toISOString().split("T")[0];
    let text = "QuizForge \u2014 Quiz Results\n";
    text += "========================\n";
    text += `Score: ${Math.round(data.score)}% (${data.total_correct}/${data.total_questions} correct)\n`;
    text += `Date: ${date}\n\n`;

    // Domain breakdown
    if (domainScores.length > 0) {
      text += "Domain Breakdown:\n";
      for (const ds of domainScores) {
        const pct = ds.total > 0 ? Math.round((ds.correct / ds.total) * 100) : 0;
        text += `- ${ds.name}: ${ds.correct}/${ds.total} (${pct}%)\n`;
      }
      text += "\n";
    }

    // Question review
    text += "Question Review:\n---\n";
    for (const q of data.results) {
      const status = q.is_correct ? "CORRECT" : "WRONG";
      text += `Q${q.question_number}. [${status}] ${enOnly(q.question_text, "\n\n")}\n`;
      for (let i = 0; i < q.choices.length; i++) {
        const wasSelected = q.selected_choices.includes(i);
        if (wasSelected) {
          const letter = String.fromCharCode(65 + i);
          const mark = q.choices[i].is_correct ? "\u2713" : "\u2717";
          text += `   Your answer: ${letter}. ${enOnly(q.choices[i].text, "\n")} ${mark}\n`;
        }
      }
      if (!q.is_correct) {
        for (let i = 0; i < q.choices.length; i++) {
          if (q.choices[i].is_correct) {
            const letter = String.fromCharCode(65 + i);
            text += `   Correct: ${letter}. ${enOnly(q.choices[i].text, "\n")}\n`;
          }
        }
        if (q.explanation) {
          text += `   Explanation: ${q.explanation}\n`;
        }
      }
      text += "\n";
    }
    text += "---\n";

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "quiz-results.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="text-center mb-10">
          <h1 className="text-lg text-gray-400 mb-2">Quiz Complete</h1>
          <p className={`text-7xl font-bold ${scoreLevel(data.score).text}`}>
            {Math.round(data.score)}%
          </p>
          <p className="text-gray-400 mt-3">
            {data.total_correct} of {data.total_questions} correct
          </p>
        </div>

        {/* Domain Breakdown */}
        {domainScores.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-10">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Score by Domain</h2>
            <div className="space-y-3">
              {domainScores.map((ds) => {
                const pct = ds.total > 0 ? Math.round((ds.correct / ds.total) * 100) : 0;
                return (
                  <div key={ds.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{ds.name}</span>
                      <span className="text-gray-400">{ds.correct}/{ds.total}</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${scoreLevel(pct).bg}`}
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
        <div>
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Question Review</h2>
          <div className="space-y-6">
            {data.results.map((q) => (
              <div key={q.question_number} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
                <div className="flex items-start gap-3 mb-3">
                  <span
                    className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      q.is_correct ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {q.question_number}
                  </span>
                  <div>
                    <p className="text-gray-200 leading-relaxed font-medium">
                      <BilingualText text={q.question_text} sep={"\n\n"} variant="question" />
                    </p>
                    <span className="text-xs text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded mt-1 inline-block">{q.domain_name}</span>
                  </div>
                </div>

                <div className="space-y-2 ml-9 mb-3">
                  {q.choices.map((c, idx) => {
                    const wasSelected = q.selected_choices.includes(idx);
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
                        key={idx}
                        className={`px-4 py-2.5 rounded-lg border ${borderClass} ${bgClass}`}
                      >
                        <div className="flex gap-2 items-start">
                          <span className="font-medium text-gray-500 shrink-0 text-sm pt-0.5">
                            {String.fromCharCode(65 + idx)}.
                          </span>
                          <div className={`flex-1 min-w-0 text-sm ${isRight ? "text-green-300" : wasSelected ? "text-red-300" : "text-gray-400"}`}>
                            <BilingualText text={c.text} sep={"\n"} variant="choice" />
                          </div>
                          <div className="shrink-0 flex flex-col items-end gap-0.5">
                            {isRight && (
                              <span className="text-xs text-green-400 font-medium">✓ Correct</span>
                            )}
                            {wasSelected && (
                              <span className="text-xs text-gray-500">your answer</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {q.explanation && (
                  <div className="ml-9 text-sm bg-gray-800/50 rounded-lg p-3">
                    <p className="text-xs text-blue-400 font-medium uppercase tracking-wider mb-1">Explanation</p>
                    <p className="text-gray-300">{q.explanation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-center gap-6 mt-10">
          <button
            onClick={downloadResults}
            className="text-gray-400 hover:text-gray-200 text-sm border border-gray-700 rounded-lg px-4 py-2 hover:border-gray-500 transition-colors"
          >
            Download Results
          </button>
          {sessionId && !isPractice && (
            <a
              href={`/leaderboard/${sessionId}`}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              View Leaderboard &rarr;
            </a>
          )}
          {isPractice && (
            <button
              onClick={async () => {
                if (!confirm("Delete this practice quiz? This cannot be undone.")) return;
                setDeleting(true);
                try {
                  await api.deletePracticeQuiz(quizId);
                  router.push("/my-quizzes");
                } catch {
                  alert("Failed to delete quiz");
                  setDeleting(false);
                }
              }}
              disabled={deleting}
              className="text-red-400/70 hover:text-red-400 text-sm border border-red-500/20 rounded-lg px-4 py-2 hover:border-red-500/40 transition-colors disabled:opacity-40"
            >
              {deleting ? "Deleting..." : "Delete Practice Quiz"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
