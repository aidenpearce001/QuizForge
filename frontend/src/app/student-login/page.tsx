"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function StudentLoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
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
      if (mode === "register") {
        await api.register({ full_name: fullName, username, password });
      } else {
        await api.login({ username, password });
      }
      await refresh();
      router.push("/study");
    } catch (err: any) {
      setError(err.message || "Failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-lg p-6">
        <Link href="/" className="text-xs text-gray-500 hover:text-gray-300 mb-4 block">← Back</Link>
        <h1 className="text-xl font-semibold text-gray-100 mb-1">QuizForge</h1>
        <p className="text-sm text-gray-400 mb-4">Student Access</p>

        {/* Toggle */}
        <div className="flex rounded-lg border border-gray-700 overflow-hidden mb-6">
          <button
            onClick={() => setMode("login")}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              mode === "login"
                ? "bg-green-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setMode("register")}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              mode === "register"
                ? "bg-green-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {mode === "register" && (
            <input
              type="text"
              placeholder="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-green-500"
              required
            />
          )}
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-green-500"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-green-500"
            required
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded px-4 py-2 text-sm font-medium"
          >
            {submitting ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="text-xs text-gray-600 mt-4 text-center">
          Tip: Scan a QR code from your instructor to join a quiz session directly
        </p>
      </div>
    </div>
  );
}
