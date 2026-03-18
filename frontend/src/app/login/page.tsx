"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function InstructorLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();
  const { refresh } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await api.login({ username, password });
      if (res.user.role !== "instructor") {
        setError("This login is for instructors only");
        await api.logout();
        return;
      }
      await refresh();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-lg p-6">
        <Link href="/" className="text-xs text-gray-500 hover:text-gray-300 mb-4 block">← Back</Link>
        <h1 className="text-xl font-semibold text-gray-100 mb-1">QuizForge</h1>
        <p className="text-sm text-gray-400 mb-6">Instructor Login</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
            required
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded px-4 py-2 text-sm font-medium"
          >
            {submitting ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
