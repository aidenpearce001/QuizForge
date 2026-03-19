const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

export const api = {
  // Auth
  register: (data: { full_name: string; username: string; password: string }) =>
    apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { username: string; password: string }) =>
    apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => apiFetch("/api/auth/me"),
  logout: () => apiFetch("/api/auth/logout", { method: "POST" }),

  // Subjects & Domains
  getSubjects: () => apiFetch("/api/subjects"),
  getDomains: (subjectId: string) => apiFetch(`/api/subjects/${subjectId}/domains`),

  // Sessions
  getSessions: () => apiFetch("/api/sessions"),
  getSession: (id: string) => apiFetch(`/api/sessions/${id}`),
  createSession: (data: any) => apiFetch("/api/sessions", { method: "POST", body: JSON.stringify(data) }),
  toggleSession: (id: string) => apiFetch(`/api/sessions/${id}/toggle`, { method: "PUT" }),
  getAttendance: (id: string) => apiFetch(`/api/sessions/${id}/attendance`),
  getResults: (id: string) => apiFetch(`/api/sessions/${id}/results`),
  getLeaderboard: (sessionId: string) => apiFetch(`/api/sessions/${sessionId}/leaderboard`),

  // Quiz (student)
  joinSession: (sessionId: string) => apiFetch(`/api/sessions/${sessionId}/join`, { method: "POST" }),
  getQuizMeta: (quizId: string) => apiFetch(`/api/quiz/${quizId}`),
  getQuestion: (quizId: string, n: number) => apiFetch(`/api/quiz/${quizId}/question/${n}`),
  saveAnswer: (quizId: string, n: number, data: { selected_choices: number[] }) =>
    apiFetch(`/api/quiz/${quizId}/question/${n}/answer`, { method: "POST", body: JSON.stringify(data) }),
  submitQuiz: (quizId: string) => apiFetch(`/api/quiz/${quizId}/submit`, { method: "POST" }),
  getQuizResults: (quizId: string) => apiFetch(`/api/quiz/${quizId}/results`),

  // Questions
  getQuestions: (subjectId: string, params?: string) => apiFetch(`/api/subjects/${subjectId}/questions${params ? `?${params}` : ""}`),
  createQuestion: (subjectId: string, data: any) => apiFetch(`/api/subjects/${subjectId}/questions`, { method: "POST", body: JSON.stringify(data) }),
  updateQuestion: (id: string, data: any) => apiFetch(`/api/questions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteQuestion: (id: string) => apiFetch(`/api/questions/${id}`, { method: "DELETE" }),

  // PDFs
  uploadPdfs: async (subjectId: string, files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append("files", f));
    const res = await fetch(`${API_BASE}/api/subjects/${subjectId}/pdfs`, {
      method: "POST", credentials: "include", body: formData,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || "Upload failed");
    }
    return res.json();
  },
  getPdfs: (subjectId: string) => apiFetch(`/api/subjects/${subjectId}/pdfs`),

  // Study
  getStudyCards: (subjectId: string) => apiFetch(`/api/study/${subjectId}/cards`),
  getStudyCard: (domainId: string) => apiFetch(`/api/study/domain/${domainId}`),
};
