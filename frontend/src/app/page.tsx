"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push(user.role === "instructor" ? "/dashboard" : "/study");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-100 mb-2">QuizForge</h1>
          <p className="text-gray-400">Classroom quiz platform</p>
        </div>

        <div className="flex flex-col gap-4">
          {/* Instructor */}
          <button
            onClick={() => router.push("/login")}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg p-6 text-left hover:border-blue-500/50 transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center text-2xl">
                📋
              </div>
              <div>
                <div className="text-gray-100 font-semibold group-hover:text-blue-400 transition-colors">
                  Instructor
                </div>
                <div className="text-sm text-gray-500">
                  Manage sessions, questions & view results
                </div>
              </div>
            </div>
          </button>

          {/* Student */}
          <button
            onClick={() => router.push("/student-login")}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg p-6 text-left hover:border-green-500/50 transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center justify-center text-2xl">
                🎓
              </div>
              <div>
                <div className="text-gray-100 font-semibold group-hover:text-green-400 transition-colors">
                  Student
                </div>
                <div className="text-sm text-gray-500">
                  Take quizzes & study materials
                </div>
              </div>
            </div>
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 my-2">
            <div className="flex-1 border-t border-gray-800"></div>
            <span className="text-xs text-gray-600">or scan QR code to join a session</span>
            <div className="flex-1 border-t border-gray-800"></div>
          </div>

          {/* Study Cards (public) */}
          <button
            onClick={() => router.push("/study")}
            className="w-full text-center text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            Browse study materials →
          </button>
        </div>
      </div>
    </div>
  );
}
