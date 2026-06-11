"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

type SessionDetail = {
  id: string;
  title: string;
  is_active: boolean;
  session_type?: "normal" | "exam";
  qr_code: string;
  qr_url: string;
  question_count: number;
  subject_name?: string;
};

type ViolationDetails = {
  fullscreen?: number;
  tab?: number;
  window?: number;
};

type Attendee = {
  student_id: string;
  full_name: string;
  status: string;
  current_question?: number | null;
  total_questions: number;
  score?: number | null;
  violation_count: number;
  violation_details: ViolationDetails;
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
    const interval = setInterval(fetchAttendance, 5000);
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

  const handleCopy = async () => {
    if (!session?.qr_url) return;
    try {
      await navigator.clipboard.writeText(session.qr_url);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = session.qr_url;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!session) {
    return <p className="text-gray-400">Loading session...</p>;
  }

  const violators = attendance
    .filter((a) => a.violation_count > 0)
    .sort((a, b) => b.violation_count - a.violation_count);

  const violationTooltip = (d: ViolationDetails) => {
    const lines: string[] = [];
    if (d.fullscreen) lines.push(`Exited fullscreen: ${d.fullscreen}×`);
    if (d.tab) lines.push(`Switched tab: ${d.tab}×`);
    if (d.window) lines.push(`Switched window: ${d.window}×`);
    return lines.length ? lines.join("\n") : null;
  };

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
        {session.session_type === "exam" && (
          <span className="text-xs px-2 py-0.5 rounded bg-amber-900/50 text-amber-400">
            Exam Day
          </span>
        )}
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

      <div className="grid gap-6 lg:grid-cols-2 mb-6">
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
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-200">{a.full_name}</span>
                    {a.violation_count > 0 && (
                      <span className="group relative">
                        <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/50 text-red-400 font-medium cursor-default">
                          ⚠ {a.violation_count}
                        </span>
                        {violationTooltip(a.violation_details) && (
                          <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 z-20 hidden group-hover:flex flex-col gap-0.5 bg-gray-800 border border-gray-700 rounded px-2.5 py-2 text-xs text-gray-200 whitespace-nowrap shadow-lg">
                            {a.violation_details.fullscreen ? (
                              <span>🖥 Exited fullscreen: <b>{a.violation_details.fullscreen}×</b></span>
                            ) : null}
                            {a.violation_details.tab ? (
                              <span>🔁 Switched tab: <b>{a.violation_details.tab}×</b></span>
                            ) : null}
                            {a.violation_details.window ? (
                              <span>🪟 Switched window: <b>{a.violation_details.window}×</b></span>
                            ) : null}
                          </span>
                        )}
                      </span>
                    )}
                  </div>
                  {statusBadge(a)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cheating Log */}
      {violators.length > 0 && (
        <div className="bg-gray-900 border border-red-800/40 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span>⚠</span>
            <span>Cheating Violations ({violators.length} student{violators.length !== 1 ? "s" : ""})</span>
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            Recorded every time a student left the fullscreen exam window (tab switch, window blur, or fullscreen exit).
            Updates every 5 seconds.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-800">
                  <th className="pb-2 pr-4">Student</th>
                  <th className="pb-2 pr-6">Total</th>
                  <th className="pb-2 pr-4">Breakdown</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {violators.map((a, i) => (
                  <tr key={i} className="border-b border-gray-800/50 last:border-0">
                    <td className="py-2 pr-4 text-gray-200 font-medium">{a.full_name}</td>
                    <td className="py-2 pr-6">
                      <span className="text-red-400 font-bold">{a.violation_count}</span>
                    </td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-col gap-0.5 text-xs text-gray-400">
                        {a.violation_details.fullscreen ? (
                          <span>🖥 Fullscreen exit: <span className="text-red-400 font-medium">{a.violation_details.fullscreen}×</span></span>
                        ) : null}
                        {a.violation_details.tab ? (
                          <span>🔁 Tab switch: <span className="text-red-400 font-medium">{a.violation_details.tab}×</span></span>
                        ) : null}
                        {a.violation_details.window ? (
                          <span>🪟 Window switch: <span className="text-red-400 font-medium">{a.violation_details.window}×</span></span>
                        ) : null}
                        {!a.violation_details.fullscreen && !a.violation_details.tab && !a.violation_details.window && (
                          <span className="text-gray-600 italic">legacy data</span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 pr-4">
                      <span className={`text-xs ${
                        a.status === "completed" ? "text-green-400" :
                        a.status === "in_progress" ? "text-blue-400" : "text-gray-500"
                      }`}>
                        {a.status === "completed" ? "Submitted" :
                         a.status === "in_progress" ? `Q${a.current_question}/${a.total_questions}` : "Joined"}
                      </span>
                    </td>
                    <td className="py-2 text-gray-300">
                      {a.status === "completed" ? `${Math.round(a.score ?? 0)}%` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
