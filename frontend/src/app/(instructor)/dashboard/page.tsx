"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Session = {
  id: string;
  title: string;
  subject_name?: string;
  question_count: number;
  is_active: boolean;
  created_at: string;
};

export default function DashboardPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSessions().then(setSessions).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-gray-400">Loading sessions...</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Sessions</h1>
        <Link
          href="/sessions/new"
          className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm font-medium"
        >
          + New Session
        </Link>
      </div>

      {sessions.length === 0 ? (
        <p className="text-gray-400">No sessions yet. Create one to get started.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col gap-2"
            >
              <div className="flex items-start justify-between">
                <Link
                  href={`/sessions/${s.id}`}
                  className="text-base font-medium text-gray-100 hover:text-blue-400"
                >
                  {s.title}
                </Link>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    s.is_active
                      ? "bg-green-900/50 text-green-400"
                      : "bg-gray-800 text-gray-500"
                  }`}
                >
                  {s.is_active ? "Active" : "Closed"}
                </span>
              </div>
              {s.subject_name && (
                <p className="text-xs text-gray-500">{s.subject_name}</p>
              )}
              <p className="text-xs text-gray-400">{s.question_count} questions</p>
              <div className="flex gap-2 mt-auto pt-2">
                <Link
                  href={`/sessions/${s.id}`}
                  className="text-xs text-blue-400 hover:underline"
                >
                  Manage
                </Link>
                <Link
                  href={`/session-results/${s.id}`}
                  className="text-xs text-gray-400 hover:text-gray-200"
                >
                  Results
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
