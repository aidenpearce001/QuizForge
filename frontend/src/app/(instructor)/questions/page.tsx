"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

type Subject = { id: string; name: string };
type Domain = { id: string; name: string };
type Question = {
  id: string;
  question_text: string;
  question_type: string;
  domain_name: string;
  domain_id: string;
  source: string;
  choices: { text: string; is_correct: boolean }[];
  explanation: string | null;
  created_at: string;
};

export default function QuestionsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{
    question_text: string;
    choices: { text: string; is_correct: boolean }[];
    explanation: string;
  }>({ question_text: "", choices: [], explanation: "" });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    api.getSubjects().then((s: Subject[]) => {
      setSubjects(s);
      if (s.length > 0) setSelectedSubject(s[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedSubject) {
      api.getDomains(selectedSubject).then(setDomains).catch(() => {});
      setSelectedDomain("");
      setPage(1);
    }
  }, [selectedSubject]);

  const fetchQuestions = useCallback(() => {
    if (!selectedSubject) return;
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), limit: "20" });
    if (selectedDomain) params.set("domain_id", selectedDomain);
    api
      .getQuestions(selectedSubject, params.toString())
      .then((data: Question[]) => {
        setQuestions(data);
        setHasMore(data.length === 20);
      })
      .catch(() => setQuestions([]))
      .finally(() => setLoading(false));
  }, [selectedSubject, selectedDomain, page]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const startEdit = (q: Question) => {
    setEditingId(q.id);
    setEditForm({
      question_text: q.question_text,
      choices: q.choices || [],
      explanation: q.explanation || "",
    });
  };

  const saveEdit = async () => {
    if (!editingId) return;
    await api.updateQuestion(editingId, editForm);
    setEditingId(null);
    fetchQuestions();
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteQuestion(id);
      setDeleteConfirm(null);
      fetchQuestions();
    } catch (err: any) {
      alert(err.message);
      setDeleteConfirm(null);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Question Bank</h1>

      <div className="flex gap-3 mb-4">
        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
        >
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select
          value={selectedDomain}
          onChange={(e) => { setSelectedDomain(e.target.value); setPage(1); }}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Domains</option>
          {domains.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading questions...</p>
      ) : questions.length === 0 ? (
        <p className="text-gray-500">No questions found.</p>
      ) : (
        <>
          <p className="text-xs text-gray-500 mb-3">Showing {questions.length} questions (page {page})</p>
          <div className="flex flex-col gap-3">
            {questions.map((q) => (
              <div key={q.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                {editingId === q.id ? (
                  <div className="flex flex-col gap-3">
                    <textarea
                      value={editForm.question_text}
                      onChange={(e) => setEditForm({ ...editForm, question_text: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500 min-h-[60px]"
                    />
                    {editForm.choices.map((c, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={c.is_correct}
                          onChange={(e) => {
                            const choices = [...editForm.choices];
                            choices[i] = { ...choices[i], is_correct: e.target.checked };
                            setEditForm({ ...editForm, choices });
                          }}
                          className="accent-blue-500"
                        />
                        <input
                          type="text"
                          value={c.text}
                          onChange={(e) => {
                            const choices = [...editForm.choices];
                            choices[i] = { ...choices[i], text: e.target.value };
                            setEditForm({ ...editForm, choices });
                          }}
                          className="flex-1 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    ))}
                    <textarea
                      placeholder="Explanation (optional)"
                      value={editForm.explanation}
                      onChange={(e) => setEditForm({ ...editForm, explanation: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
                    />
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="bg-blue-600 hover:bg-blue-700 text-white rounded px-3 py-1.5 text-xs font-medium">Save</button>
                      <button onClick={() => setEditingId(null)} className="bg-gray-800 hover:bg-gray-700 text-gray-300 rounded px-3 py-1.5 text-xs">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-sm text-gray-200 mb-2 line-clamp-2">{q.question_text}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-400">{q.domain_name}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-500">{q.source}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-500">{q.question_type}</span>
                      <div className="ml-auto flex gap-2">
                        <button onClick={() => startEdit(q)} className="text-xs text-blue-400 hover:underline">Edit</button>
                        {deleteConfirm === q.id ? (
                          <span className="flex gap-1">
                            <button onClick={() => handleDelete(q.id)} className="text-xs text-red-400 hover:underline">Confirm</button>
                            <button onClick={() => setDeleteConfirm(null)} className="text-xs text-gray-500 hover:underline">Cancel</button>
                          </span>
                        ) : (
                          <button onClick={() => setDeleteConfirm(q.id)} className="text-xs text-red-400 hover:underline">Delete</button>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 rounded text-xs"
            >
              Prev
            </button>
            <span className="text-xs text-gray-500">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 rounded text-xs"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
