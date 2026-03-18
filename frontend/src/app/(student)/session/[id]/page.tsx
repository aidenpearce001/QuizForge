"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type SessionInfo = {
  id: string;
  title: string;
  subject_name: string;
  question_count: number;
  time_limit_minutes: number | null;
  is_active: boolean;
};

export default function SessionLoginPage() {
  const params = useParams();
  const router = useRouter();
  const { user, refresh } = useAuth();
  const sessionId = params.id as string;

  const [session, setSession] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"login" | "register">("login");
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    api.getSession(sessionId)
      .then(setSession)
      .catch(() => setError("Session not found"))
      .finally(() => setLoading(false));
  }, [sessionId]);

  // If already logged in as student, try joining directly
  useEffect(() => {
    if (user && user.role === "student" && session) {
      joinAndRedirect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, session]);

  async function joinAndRedirect() {
    try {
      setSubmitting(true);
      const result = await api.joinSession(sessionId);
      router.push(`/quiz/${result.quiz_id}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to join session";
      setError(msg);
      setSubmitting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      if (tab === "register") {
        await api.register({ full_name: fullName, username, password });
      } else {
        await api.login({ username, password });
      }
      await refresh();
      const result = await api.joinSession(sessionId);
      router.push(`/quiz/${result.quiz_id}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Authentication failed";
      setError(msg);
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading session...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-red-400 text-lg">{error || "Session not found"}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col lg:flex-row">
      {/* Left: Session Info */}
      <div className="lg:w-1/2 p-8 lg:p-16 flex flex-col justify-center">
        <h1 className="text-3xl font-bold mb-2">QuizForge</h1>
        <div className="mt-8 space-y-4">
          <h2 className="text-2xl font-semibold text-blue-400">{session.title}</h2>
          <div className="space-y-2 text-gray-300">
            <p><span className="text-gray-500">Subject:</span> {session.subject_name}</p>
            <p><span className="text-gray-500">Questions:</span> {session.question_count}</p>
            {session.time_limit_minutes && (
              <p><span className="text-gray-500">Time Limit:</span> {session.time_limit_minutes} minutes</p>
            )}
          </div>
          {!session.is_active && (
            <p className="text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 rounded-lg p-3 text-sm">
              This session is not currently active.
            </p>
          )}
        </div>
      </div>

      {/* Right: Auth Form */}
      <div className="lg:w-1/2 p-8 lg:p-16 flex items-center justify-center">
        <div className="w-full max-w-md">
          {user && user.role === "student" ? (
            <div className="text-center">
              <p className="text-gray-300 mb-4">Logged in as <span className="text-blue-400 font-semibold">{user.full_name}</span></p>
              {submitting && <p className="text-gray-400">Joining session...</p>}
              {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
            </div>
          ) : user && user.role === "instructor" ? (
            <div className="text-center space-y-4">
              <p className="text-gray-400">You are logged in as <span className="text-blue-400 font-semibold">instructor</span>.</p>
              <p className="text-gray-500 text-sm">Please logout first to join as a student.</p>
              <button
                onClick={async () => { await api.logout(); await refresh(); }}
                className="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm"
              >
                Logout & continue as student
              </button>
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="flex mb-6 bg-gray-900 rounded-lg p-1">
                <button
                  onClick={() => setTab("login")}
                  className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                    tab === "login" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Login
                </button>
                <button
                  onClick={() => setTab("register")}
                  className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                    tab === "register" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Register
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {tab === "register" && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                      className="w-full px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
                      placeholder="John Doe"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
                    placeholder="username"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
                    placeholder="password"
                  />
                </div>

                {error && (
                  <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg p-3">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg font-medium transition-colors"
                >
                  {submitting ? "Please wait..." : tab === "login" ? "Login & Join Quiz" : "Register & Join Quiz"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
