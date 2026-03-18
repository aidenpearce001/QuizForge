"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Sessions", icon: "\u{1F4CB}" },
  { href: "/uploads", label: "PDF Uploads", icon: "\u{1F4C4}" },
  { href: "/questions", label: "Question Bank", icon: "\u2753" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-52 border-r border-gray-800 p-4 min-h-screen bg-gray-950">
      <div className="text-xs uppercase tracking-wider text-gray-500 mb-4 font-semibold">
        QuizForge
      </div>
      <nav className="flex flex-col gap-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`px-3 py-2 rounded text-sm ${
              pathname.startsWith(l.href)
                ? "bg-blue-500/10 text-blue-400"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {l.icon} {l.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
