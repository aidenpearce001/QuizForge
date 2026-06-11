"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Subject = { id: string; name: string };
type Domain = { id: string; name: string; question_count?: number; exam_question_count?: number };

export default function NewSessionPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");
  const [questionsPerStudent, setQuestionsPerStudent] = useState(10);
  const [timeLimit, setTimeLimit] = useState<number | "">("");
  const [sessionType, setSessionType] = useState<"normal" | "exam">("normal");
  const [mixWithDomain, setMixWithDomain] = useState(false);
  const [examRatio, setExamRatio] = useState(70);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSubjects().then(setSubjects);
  }, []);

  useEffect(() => {
    if (selectedSubject) {
      api.getDomains(selectedSubject).then((d: Domain[]) => {
        setDomains(d);
        setSelectedDomains(new Set(d.map((dm) => dm.id)));
      });
    } else {
      setDomains([]);
      setSelectedDomains(new Set());
    }
  }, [selectedSubject]);

  const toggleDomain = (id: string) => {
    setSelectedDomains((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedDomainList = domains.filter((d) => selectedDomains.has(d.id));
  const availableQuestions = selectedDomainList.reduce((sum, d) => sum + (d.question_count || 0), 0);
  const examQuestions = selectedDomainList.reduce((sum, d) => sum + (d.exam_question_count || 0), 0);
  const bankQuestions = availableQuestions - examQuestions;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await api.createSession({
        title,
        subject_id: selectedSubject,
        domain_ids: Array.from(selectedDomains),
        questions_per_quiz: questionsPerStudent,
        time_limit_minutes: timeLimit || null,
        session_type: sessionType,
        exam_ratio: sessionType === "exam" && mixWithDomain ? examRatio : null,
      });
      router.push(`/sessions/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create session");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-semibold mb-6">New Session</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">Session Type</label>
          <div className="flex rounded-lg border border-gray-700 overflow-hidden">
            <button
              type="button"
              onClick={() => setSessionType("normal")}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                sessionType === "normal"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-gray-200"
              }`}
            >
              Normal Session
            </button>
            <button
              type="button"
              onClick={() => setSessionType("exam")}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                sessionType === "exam"
                  ? "bg-amber-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-gray-200"
              }`}
            >
              Exam Day
            </button>
          </div>
          {sessionType === "exam" && (
            <div className="mt-2 flex flex-col gap-3">
              {/* Source breakdown */}
              <div className="flex gap-3 text-xs">
                <div className="flex-1 bg-amber-900/30 border border-amber-700/50 rounded px-3 py-2">
                  <div className="text-amber-400 font-medium">Midterm exam questions</div>
                  <div className="text-amber-300 text-base font-bold">{examQuestions}</div>
                  <div className="text-gray-500 mt-0.5">from exam document</div>
                </div>
                <div className="flex-1 bg-blue-900/20 border border-blue-700/40 rounded px-3 py-2">
                  <div className="text-blue-400 font-medium">Domain bank questions</div>
                  <div className="text-blue-300 text-base font-bold">{bankQuestions}</div>
                  <div className="text-gray-500 mt-0.5">practice &amp; study pool</div>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mixWithDomain}
                  onChange={(e) => setMixWithDomain(e.target.checked)}
                  className="w-4 h-4 accent-amber-500"
                />
                <span className="text-sm text-gray-300">Mix with domain bank questions</span>
              </label>

              {mixWithDomain ? (
                <div className="flex flex-col gap-2 bg-gray-800/50 rounded p-3 border border-gray-700">
                  <div className="flex justify-between text-xs">
                    <span className="text-amber-400 font-medium">Midterm exam: {examRatio}%</span>
                    <span className="text-blue-400 font-medium">Domain bank: {100 - examRatio}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={90}
                    step={5}
                    value={examRatio}
                    onChange={(e) => setExamRatio(Number(e.target.value))}
                    className="w-full accent-amber-500"
                  />
                  <p className="text-xs text-gray-500">
                    Each student's quiz pulls {examRatio}% from the midterm exam document and {100 - examRatio}% from the domain bank.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-amber-400">
                  Questions drawn only from the midterm exam document — no domain bank questions included.
                </p>
              )}
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Subject</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            required
          >
            <option value="">Select a subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {domains.length > 0 && (
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Domains ({availableQuestions} questions available{sessionType === "exam" && examQuestions > 0 ? ` · ${examQuestions} midterm exam` : ""})
            </label>
            <div className="flex flex-wrap gap-2">
              {domains.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => toggleDomain(d.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${
                    selectedDomains.has(d.id)
                      ? "bg-blue-600/20 border-blue-500 text-blue-400"
                      : "bg-gray-800 border-gray-700 text-gray-500"
                  }`}
                >
                  {d.name}
                  {d.question_count != null && (
                    <span className="ml-1 opacity-60">({d.question_count})</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Questions per student
            </label>
            <input
              type="number"
              min={1}
              value={questionsPerStudent}
              onChange={(e) => setQuestionsPerStudent(Number(e.target.value))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Time limit (min, optional)
            </label>
            <input
              type="number"
              min={1}
              value={timeLimit}
              onChange={(e) =>
                setTimeLimit(e.target.value ? Number(e.target.value) : "")
              }
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !selectedSubject}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded px-4 py-2 text-sm font-medium"
        >
          {submitting ? "Creating..." : "Create Session"}
        </button>
      </form>
    </div>
  );
}
