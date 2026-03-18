"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

type SessionDetail = {
  id: string;
  title: string;
  is_active: boolean;
  qr_code: string;
  qr_url: string;
  question_count: number;
  subject_name?: string;
};

type Attendee = {
  student_id: string;
  full_name: string;
  status: string;
  current_question?: number | null;
  total_questions: number;
  score?: number | null;
};

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [attendance, setAttendance] = useState<Attendee[]>([]);
  const [toggling, setToggling] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchSession = useCallback(() => {
    api.getSession(id).then(setSession);
  }, [id]);

  const fetchAttendance = useCallback(() => {
    api.getAttendance(id).then(setAttendance);
  }, [id]);

  useEffect(() => {
    fetchSession();
    fetchAttendance();
    const interval = setInterval(fetchAttendance, 10000);
    return () => clearInterval(interval);
  }, [fetchSession, fetchAttendance]);

  const handleToggle = async () => {
    setToggling(true);
    try {
      await api.toggleSession(id);
      fetchSession();
    } finally {
      setToggling(false);
    }
  };

  const handleCopy = () => {
    if (session?.qr_url) {
      navigator.clipboard.writeText(session.qr_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!session) {
    return <p className="text-gray-400">Loading session...</p>;
  }

  const statusBadge = (a: Attendee) => {
    switch (a.status) {
      case "completed":
        return <span className="text-xs px-2 py-0.5 rounded bg-green-900/50 text-green-400">Done — {Math.round(a.score ?? 0)}%</span>;
      case "in_progress":
        return (
          <span className="text-xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-400">
            Q{a.current_question}/{a.total_questions}
          </span>
        );
      default:
        return <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-500">Joined</span>;
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-semibold">{session.title}</h1>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            session.is_active
              ? "bg-green-900/50 text-green-400"
              : "bg-gray-800 text-gray-500"
          }`}
        >
          {session.is_active ? "Active" : "Closed"}
        </span>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* QR Code */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col items-center gap-4">
          {session.qr_code && (
            <img
              src={`data:image/png;base64,${session.qr_code}`}
              alt="Session QR Code"
              className="w-64 h-64 bg-white rounded p-2"
            />
          )}
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 rounded px-4 py-2 text-sm"
            >
              {copied ? "Copied!" : "Copy Link"}
            </button>
            <button
              onClick={handleToggle}
              disabled={toggling}
              className={`rounded px-4 py-2 text-sm font-medium ${
                session.is_active
                  ? "bg-red-600/20 text-red-400 hover:bg-red-600/30"
                  : "bg-green-600/20 text-green-400 hover:bg-green-600/30"
              }`}
            >
              {session.is_active ? "Close Session" : "Reopen Session"}
            </button>
          </div>
          <Link
            href={`/session-results/${session.id}`}
            className="text-sm text-blue-400 hover:underline"
          >
            View Results
          </Link>
        </div>

        {/* Attendance */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Attendance ({attendance.length})
          </h2>
          {attendance.length === 0 ? (
            <p className="text-sm text-gray-500">No students have joined yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {attendance.map((a, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-1.5 border-b border-gray-800 last:border-0"
                >
                  <span className="text-sm text-gray-200">{a.full_name}</span>
                  {statusBadge(a)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
