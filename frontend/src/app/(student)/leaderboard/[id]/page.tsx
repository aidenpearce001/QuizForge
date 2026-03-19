"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type LeaderboardEntry = {
  rank: number;
  full_name: string;
  score: number;
  total_correct: number;
  total_questions: number;
  time_taken_seconds: number | null;
};

type LeaderboardData = {
  session_title: string;
  entries: LeaderboardEntry[];
};

function formatTime(seconds: number | null): string {
  if (seconds === null) return "-";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function scoreColor(pct: number): string {
  if (pct >= 80) return "text-green-400";
  if (pct >= 50) return "text-yellow-400";
  return "text-red-400";
}

function trophyIcon(rank: number): string {
  if (rank === 1) return "\u{1F947}";
  if (rank === 2) return "\u{1F948}";
  if (rank === 3) return "\u{1F949}";
  return "";
}

export default function LeaderboardPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const { user } = useAuth();

  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getLeaderboard(sessionId)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading leaderboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center flex-col gap-4">
        <p className="text-gray-400 text-lg">{error || "Leaderboard not available"}</p>
        <a href="/study" className="text-blue-400 hover:text-blue-300 text-sm">
          Go to Study Cards &rarr;
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-100">{data.session_title}</h1>
          <p className="text-gray-400 mt-1">Leaderboard</p>
        </div>

        {data.entries.length === 0 ? (
          <p className="text-center text-gray-500">No submissions yet.</p>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wider">
                  <th className="px-4 py-3 text-left">Rank</th>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-right">Score</th>
                  <th className="px-4 py-3 text-right">Correct</th>
                  <th className="px-4 py-3 text-right">Time</th>
                </tr>
              </thead>
              <tbody>
                {data.entries.map((entry) => {
                  const isCurrentUser = user?.full_name === entry.full_name;
                  return (
                    <tr
                      key={entry.rank}
                      className={`border-b border-gray-800/50 last:border-b-0 ${
                        isCurrentUser ? "border-l-4 border-l-blue-500 bg-blue-500/5" : ""
                      }`}
                    >
                      <td className="px-4 py-3 font-medium">
                        {trophyIcon(entry.rank) ? (
                          <span className="text-lg mr-1">{trophyIcon(entry.rank)}</span>
                        ) : (
                          <span className="text-gray-500">{entry.rank}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-200">
                        {entry.full_name}
                        {isCurrentUser && (
                          <span className="ml-2 text-xs text-blue-400">(you)</span>
                        )}
                      </td>
                      <td className={`px-4 py-3 text-right font-semibold ${scoreColor(entry.score)}`}>
                        {Math.round(entry.score)}%
                      </td>
                      <td className="px-4 py-3 text-right text-gray-400">
                        {entry.total_correct}/{entry.total_questions}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-400">
                        {formatTime(entry.time_taken_seconds)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="text-center mt-8">
          <a href="/study" className="text-blue-400 hover:text-blue-300 text-sm">
            Go to Study Cards &rarr;
          </a>
        </div>
      </div>
    </div>
  );
}
