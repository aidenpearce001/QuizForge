"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

const navLinks = [
  { href: "/study", label: "Study Cards" },
  { href: "/practice", label: "Practice" },
  { href: "/my-quizzes", label: "My Quizzes" },
];

export default function StudentNav() {
  const pathname = usePathname();
  const { user, refresh } = useAuth();

  // Hide nav during quiz taking (don't distract students)
  if (pathname.startsWith("/quiz/")) return null;
  // Hide nav on session join page (has its own auth flow)
  if (pathname.startsWith("/session/")) return null;

  const handleLogout = async () => {
    await api.logout();
    await refresh();
    window.location.href = "/study";
  };

  return (
    <nav className="sticky top-0 z-50 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800">
      <div className="max-w-5xl mx-auto px-4 h-12 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/study" className="text-sm font-semibold text-gray-200 tracking-tight">
            QuizForge
          </Link>
          <div className="flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive =
                pathname === link.href || pathname.startsWith(link.href + "/");
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded text-sm transition-colors ${
                    isActive
                      ? "bg-blue-500/15 text-blue-400 font-medium"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
        {user && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">{user.full_name}</span>
            <button
              onClick={handleLogout}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
