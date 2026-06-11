"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import AntiCopyPaste from "@/components/AntiCopyPaste";
import { BilingualText } from "@/components/BilingualText";

type QuizMeta = {
  id: string;
  total_questions: number;
  time_limit_minutes: number | null;
  started_at: string;
  submitted: boolean;
  is_practice: boolean;
};

type Question = {
  question_number: number;
  question_text: string;
  question_type: string;
  domain_name: string;
  choices: { index: number; text: string }[];
  selected_choices: number[] | null;
};

export default function QuizPage() {
  const params = useParams();
  const router = useRouter();
  const quizId = params.id as string;

  const [meta, setMeta] = useState<QuizMeta | null>(null);
  const [currentQ, setCurrentQ] = useState(1);
  const [question, setQuestion] = useState<Question | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [answered, setAnswered] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Exam guard state
  const [guardReady, setGuardReady] = useState(false);
  const [isBlackedOut, setIsBlackedOut] = useState(false);
  const isBlackedOutRef = useRef(false);
  const violationsRef = useRef(0);
  const [violationCount, setViolationCount] = useState(0);

  // Fetch quiz meta
  useEffect(() => {
    api.getQuizMeta(quizId)
      .then((data) => {
        if (data.submitted_at) {
          router.push(`/results/${quizId}`);
          return;
        }
        setMeta({ ...data, submitted: !!data.submitted_at });
        // Practice quizzes skip the guard
        if (data.is_practice) setGuardReady(true);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [quizId, router]);

  const handleSubmitQuiz = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await api.submitQuiz(quizId);
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      router.push(`/results/${quizId}`);
    } catch { setSubmitting(false); }
  }, [submitting, quizId, router]);

  // Timer
  useEffect(() => {
    if (!meta?.time_limit_minutes || !meta?.started_at) return;
    const deadline = new Date(meta.started_at).getTime() + meta.time_limit_minutes * 60 * 1000;
    const tick = () => {
      const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining <= 0) {
        if (timerRef.current) clearInterval(timerRef.current);
        handleSubmitQuiz();
      }
    };
    tick();
    timerRef.current = setInterval(tick, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [meta, handleSubmitQuiz]);

  // Exam guard — tab/focus/fullscreen detection
  useEffect(() => {
    if (!guardReady || meta?.is_practice) return;

    // Small delay to avoid false positives from the fullscreen transition
    const setup = setTimeout(() => {
      const flag = (type: "fullscreen" | "tab" | "window") => {
        if (isBlackedOutRef.current) return;
        isBlackedOutRef.current = true;
        violationsRef.current += 1;
        setViolationCount(violationsRef.current);
        setIsBlackedOut(true);
        api.reportViolation(quizId, type).catch(() => {});
      };

      const onVisibility = () => { if (document.hidden) flag("tab"); else unblack(); };
      const onBlur = () => flag("window");
      const onFocus = () => unblack();
      const onFullscreenChange = () => { if (!document.fullscreenElement) flag("fullscreen"); };
      const onKeyDown = (e: KeyboardEvent) => {
        if (
          e.key === "F12" ||
          ((e.ctrlKey || e.metaKey) && e.shiftKey && ["i", "j", "c"].includes(e.key.toLowerCase())) ||
          ((e.ctrlKey || e.metaKey) && ["u", "s", "p"].includes(e.key.toLowerCase()))
        ) {
          e.preventDefault();
        }
      };

      document.addEventListener("visibilitychange", onVisibility);
      window.addEventListener("blur", onBlur);
      window.addEventListener("focus", onFocus);
      document.addEventListener("fullscreenchange", onFullscreenChange);
      document.addEventListener("keydown", onKeyDown);

      return () => {
        document.removeEventListener("visibilitychange", onVisibility);
        window.removeEventListener("blur", onBlur);
        window.removeEventListener("focus", onFocus);
        document.removeEventListener("fullscreenchange", onFullscreenChange);
        document.removeEventListener("keydown", onKeyDown);
      };
    }, 600);

    return () => clearTimeout(setup);
  }, [guardReady, meta?.is_practice]);

  function unblack() {
    isBlackedOutRef.current = false;
    setIsBlackedOut(false);
  }

  async function enterFullscreenAndStart() {
    try {
      await document.documentElement.requestFullscreen();
    } catch {
      // Fullscreen denied; proceed anyway — tab detection still works
    }
    setGuardReady(true);
  }

  async function returnToExam() {
    if (!document.fullscreenElement) {
      try { await document.documentElement.requestFullscreen(); } catch { /* ignore */ }
    }
    unblack();
  }

  // Fetch question
  const fetchQuestion = useCallback(async (n: number) => {
    try {
      const q = await api.getQuestion(quizId, n);
      setQuestion(q);
      setSelected(q.selected_choices ?? []);
      if (q.selected_choices && q.selected_choices.length > 0) {
        setAnswered((prev) => new Set(prev).add(n));
      }
    } catch { /* ignore */ }
  }, [quizId]);

  useEffect(() => {
    if (meta && guardReady) fetchQuestion(currentQ);
  }, [currentQ, meta, guardReady, fetchQuestion]);

  async function handleSelectChoice(index: number) {
    if (!question) return;
    const newSelected = selected.includes(index)
      ? selected.filter((i) => i !== index)
      : [...selected, index];
    setSelected(newSelected);
    setSaving(true);
    try {
      await api.saveAnswer(quizId, currentQ, { selected_choices: newSelected });
      setAnswered((prev) => new Set(prev).add(currentQ));
    } catch { /* ignore */ }
    finally { setSaving(false); }
  }

  function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading quiz...</p>
      </div>
    );
  }

  if (!meta) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-red-400 text-lg">Quiz not found</p>
      </div>
    );
  }

  // Fullscreen entry prompt (only for real sessions)
  if (!guardReady) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <div className="text-5xl mb-5">🔒</div>
          <h2 className="text-2xl font-semibold mb-3 text-white">Exam Security Mode</h2>
          <p className="text-gray-400 text-sm mb-2">
            This exam will run in fullscreen. Switching tabs or leaving the window will be detected.
          </p>
          <p className="text-gray-500 text-xs mb-8">
            Copy, paste, and right-click are disabled during the exam.
          </p>
          <button
            onClick={enterFullscreenAndStart}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-3 font-medium transition-colors"
          >
            Enter Fullscreen &amp; Begin Exam
          </button>
        </div>
      </div>
    );
  }

  // Blackout overlay
  if (isBlackedOut) {
    return (
      <div className="fixed inset-0 bg-black z-50 flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <div className="text-5xl mb-5">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-3">You left the exam</h2>
          <p className="text-gray-400 text-sm mb-1">
            Leaving the exam window is recorded and reported to your instructor.
          </p>
          <p className="text-red-400 text-sm font-medium mb-8">
            Violation #{violationCount}
          </p>
          <button
            onClick={returnToExam}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-3 font-medium transition-colors"
          >
            Return to Exam
          </button>
        </div>
      </div>
    );
  }

  return (
    <AntiCopyPaste>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        {/* Top Bar */}
        <div className="sticky top-0 z-10 bg-gray-900 border-b border-gray-800 px-4 py-3">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">
                Question {currentQ} of {meta.total_questions}
              </span>
              {violationCount > 0 && (
                <span className="text-xs bg-red-600/20 text-red-400 border border-red-600/40 rounded px-2 py-0.5">
                  {violationCount} violation{violationCount > 1 ? "s" : ""}
                </span>
              )}
            </div>

            {/* Progress dots */}
            <div className="hidden sm:flex items-center gap-1.5 flex-wrap justify-center max-w-xs">
              {Array.from({ length: meta.total_questions }, (_, i) => {
                const n = i + 1;
                const isAnswered = answered.has(n);
                const isCurrent = n === currentQ;
                return (
                  <button
                    key={n}
                    onClick={() => setCurrentQ(n)}
                    className={`w-3 h-3 rounded-full transition-colors ${
                      isCurrent ? "bg-yellow-400" : isAnswered ? "bg-blue-500" : "bg-gray-600"
                    }`}
                    title={`Question ${n}`}
                  />
                );
              })}
            </div>

            {timeLeft !== null && (
              <span className={`text-sm font-mono font-medium ${
                timeLeft < 60 ? "text-red-400" : timeLeft < 300 ? "text-yellow-400" : "text-gray-300"
              }`}>
                {formatTime(timeLeft)}
              </span>
            )}
          </div>
        </div>

        {/* Question Content */}
        <div className="max-w-3xl mx-auto px-4 py-8">
          {question ? (
            <>
              <span className="inline-block bg-blue-600/20 text-blue-400 text-xs font-medium px-3 py-1 rounded-full mb-4">
                {question.domain_name}
              </span>

              <h2 className="text-xl font-semibold mb-6 leading-relaxed">
                <BilingualText text={question.question_text} sep={"\n\n"} variant="question" />
              </h2>

              <div className="flex items-center gap-2 mb-4 bg-blue-600/10 border border-blue-500/30 rounded-lg px-4 py-2">
                <span className="text-blue-400 text-sm font-medium">
                  {question.question_type === "multiple" ? "Select all correct answers" : "Select your answer"}
                </span>
                {selected.length > 0 && (
                  <span className="text-blue-400/60 text-xs">({selected.length} selected)</span>
                )}
              </div>

              <div className="space-y-3 mb-8">
                {question.choices.map((choice) => {
                  const isSelected = selected.includes(choice.index);
                  return (
                    <button
                      key={choice.index}
                      onClick={() => handleSelectChoice(choice.index)}
                      disabled={saving}
                      className={`w-full text-left px-5 py-4 rounded-lg border transition-colors flex items-start gap-3 ${
                        isSelected
                          ? "border-blue-500 bg-blue-600/15 text-gray-100"
                          : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-700 hover:bg-gray-800/50"
                      }`}
                    >
                      <span className={`shrink-0 w-5 h-5 mt-0.5 flex items-center justify-center border rounded ${
                        isSelected ? "border-blue-500 bg-blue-500 text-white" : "border-gray-600"
                      }`}>
                        {isSelected && (
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </span>
                      <span className="flex-1">
                        <span className="font-medium text-gray-500 mr-2">
                          {String.fromCharCode(65 + choice.index)}.
                        </span>
                        <BilingualText text={choice.text} sep={"\n"} variant="choice" />
                      </span>
                    </button>
                  );
                })}
              </div>

              {selected.length === 0 && (
                <p className="text-sm text-yellow-400/70 mb-4">Please select an answer to continue</p>
              )}

              <div className="flex items-center justify-between">
                <button
                  onClick={() => setCurrentQ((q) => Math.max(1, q - 1))}
                  disabled={currentQ === 1}
                  className="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>

                {currentQ === meta.total_questions ? (
                  <button
                    onClick={handleSubmitQuiz}
                    disabled={submitting || selected.length === 0}
                    className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium transition-colors"
                  >
                    {submitting ? "Submitting..." : "Submit Quiz"}
                  </button>
                ) : (
                  <button
                    onClick={() => setCurrentQ((q) => Math.min(meta.total_questions, q + 1))}
                    disabled={selected.length === 0}
                    className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium transition-colors"
                  >
                    Next
                  </button>
                )}
              </div>
            </>
          ) : (
            <p className="text-gray-400">Loading question...</p>
          )}
        </div>
      </div>
    </AntiCopyPaste>
  );
}
