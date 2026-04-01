"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Subject = { id: string; name: string };
type Domain = { id: string; name: string; description: string | null; question_count: number };

export default function PracticePage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set());
  const [questionsCount, setQuestionsCount] = useState(10);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Load subjects
  useEffect(() => {
    api
      .getSubjects()
      .then((data: Subject[]) => {
        setSubjects(data);
        if (data.length > 0) setSelectedSubject(data[0].id);
      })
      .catch(() => setError("Failed to load subjects"))
      .finally(() => setLoading(false));
  }, []);

  // Load domains when subject changes
  useEffect(() => {
    if (!selectedSubject) return;
    setDomains([]);
    setSelectedDomains(new Set());
    api
      .getDomains(selectedSubject)
      .then(setDomains)
      .catch(() => {});
  }, [selectedSubject]);

  const totalAvailable = selectedDomains.size > 0
    ? domains.filter((d) => selectedDomains.has(d.id)).reduce((sum, d) => sum + d.question_count, 0)
    : domains.reduce((sum, d) => sum + d.question_count, 0);

  const toggleDomain = (id: string) => {
    setSelectedDomains((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedDomains.size === domains.length) {
      setSelectedDomains(new Set());
    } else {
      setSelectedDomains(new Set(domains.map((d) => d.id)));
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    try {
      const res = await api.createPracticeQuiz({
        subject_id: selectedSubject,
        domain_ids: selectedDomains.size > 0 ? Array.from(selectedDomains) : undefined,
        questions_count: questionsCount,
      });
      router.push(`/quiz/${res.quiz_id}`);
    } catch (e: any) {
      setError(e.message || "Failed to generate quiz");
      setGenerating(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="h-8 w-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user || user.role !== "student") {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400">Please log in as a student.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-2">Practice Quiz</h1>
        <p className="text-gray-400 text-sm mb-8">
          Generate a personal quiz to test yourself. Results are only visible to you.
        </p>

        {/* Subject selector (if multiple) */}
        {subjects.length > 1 && (
          <div className="mb-6">
            <label className="text-sm text-gray-400 block mb-2">Subject</label>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Domain selection */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm text-gray-400">
              Domains <span className="text-gray-600">(leave empty for all)</span>
            </label>
            {domains.length > 0 && (
              <button
                onClick={selectAll}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {selectedDomains.size === domains.length ? "Deselect all" : "Select all"}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 gap-2">
            {domains.map((d) => {
              const isSelected = selectedDomains.has(d.id);
              return (
                <button
                  key={d.id}
                  onClick={() => toggleDomain(d.id)}
                  className={`text-left px-4 py-3 rounded-lg border text-sm transition-colors ${
                    isSelected
                      ? "border-blue-500/50 bg-blue-500/10 text-blue-300"
                      : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{d.name}</span>
                    <span className="text-xs text-gray-500">{d.question_count} questions</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Question count */}
        <div className="mb-8">
          <label className="text-sm text-gray-400 block mb-2">Number of questions</label>
          <div className="flex items-center gap-3">
            {[5, 10, 20, 30, 50].map((n) => (
              <button
                key={n}
                onClick={() => setQuestionsCount(n)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  questionsCount === n
                    ? "bg-blue-600 text-white"
                    : "bg-gray-900 border border-gray-800 text-gray-400 hover:text-gray-200"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
          {totalAvailable > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {totalAvailable} questions available{selectedDomains.size > 0 ? " in selected domains" : ""}
              {questionsCount > totalAvailable && (
                <span className="text-yellow-500"> (quiz will have {totalAvailable})</span>
              )}
            </p>
          )}
        </div>

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={generating || !selectedSubject || totalAvailable === 0}
          className="w-full py-3 rounded-lg font-medium text-sm transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {generating ? "Generating..." : "Start Practice Quiz"}
        </button>
      </div>
    </div>
  );
}
