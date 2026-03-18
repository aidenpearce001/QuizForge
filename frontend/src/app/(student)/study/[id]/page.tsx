"use client";

import { useEffect, useState, type ComponentPropsWithoutRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "@/lib/api";

type StudyCard = {
  domain_id: string;
  domain_name: string;
  content: string;
};

/* ---------- Custom Markdown components for dark theme ---------- */

function MdH2({ children, ...props }: ComponentPropsWithoutRef<"h2">) {
  return (
    <h2
      className="text-xl font-bold text-gray-50 mt-10 mb-4 pb-2 border-b border-gray-800"
      {...props}
    >
      {children}
    </h2>
  );
}

function MdH3({ children, ...props }: ComponentPropsWithoutRef<"h3">) {
  return (
    <h3
      className="text-lg font-semibold text-blue-300 mt-8 mb-3"
      {...props}
    >
      {children}
    </h3>
  );
}

function MdH4({ children, ...props }: ComponentPropsWithoutRef<"h4">) {
  return (
    <h4
      className="text-base font-semibold text-gray-200 mt-6 mb-2"
      {...props}
    >
      {children}
    </h4>
  );
}

function MdP({ children, ...props }: ComponentPropsWithoutRef<"p">) {
  return (
    <p className="text-gray-300 leading-relaxed mb-4" {...props}>
      {children}
    </p>
  );
}

function MdUl({ children, ...props }: ComponentPropsWithoutRef<"ul">) {
  return (
    <ul className="list-disc list-outside ml-5 mb-4 space-y-1.5 text-gray-300" {...props}>
      {children}
    </ul>
  );
}

function MdOl({ children, ...props }: ComponentPropsWithoutRef<"ol">) {
  return (
    <ol className="list-decimal list-outside ml-5 mb-4 space-y-1.5 text-gray-300" {...props}>
      {children}
    </ol>
  );
}

function MdLi({ children, ...props }: ComponentPropsWithoutRef<"li">) {
  return (
    <li className="leading-relaxed" {...props}>
      {children}
    </li>
  );
}

function MdStrong({ children, ...props }: ComponentPropsWithoutRef<"strong">) {
  return (
    <strong className="font-semibold text-gray-100" {...props}>
      {children}
    </strong>
  );
}

function MdCode({ children, className, ...props }: ComponentPropsWithoutRef<"code">) {
  // Inline code vs code blocks
  if (className) {
    return (
      <code className={`${className} text-sm`} {...props}>
        {children}
      </code>
    );
  }
  return (
    <code
      className="text-blue-300 bg-gray-800/80 px-1.5 py-0.5 rounded text-sm font-mono"
      {...props}
    >
      {children}
    </code>
  );
}

function MdBlockquote({ children, ...props }: ComponentPropsWithoutRef<"blockquote">) {
  return (
    <blockquote
      className="border-l-4 border-blue-500/50 bg-blue-950/20 pl-4 pr-4 py-3 my-4 rounded-r-lg text-gray-300 italic"
      {...props}
    >
      {children}
    </blockquote>
  );
}

function MdTable({ children, ...props }: ComponentPropsWithoutRef<"table">) {
  return (
    <div className="overflow-x-auto my-5 rounded-lg border border-gray-800">
      <table className="w-full text-sm" {...props}>
        {children}
      </table>
    </div>
  );
}

function MdThead({ children, ...props }: ComponentPropsWithoutRef<"thead">) {
  return (
    <thead className="bg-gray-800/80 text-gray-200" {...props}>
      {children}
    </thead>
  );
}

function MdTr({ children, ...props }: ComponentPropsWithoutRef<"tr">) {
  return (
    <tr className="border-b border-gray-800 even:bg-gray-900/50" {...props}>
      {children}
    </tr>
  );
}

function MdTh({ children, ...props }: ComponentPropsWithoutRef<"th">) {
  return (
    <th
      className="px-4 py-2.5 text-left font-semibold text-gray-200 whitespace-nowrap"
      {...props}
    >
      {children}
    </th>
  );
}

function MdTd({ children, ...props }: ComponentPropsWithoutRef<"td">) {
  return (
    <td className="px-4 py-2.5 text-gray-300" {...props}>
      {children}
    </td>
  );
}

function MdHr(props: ComponentPropsWithoutRef<"hr">) {
  return <hr className="border-gray-800 my-8" {...props} />;
}

function MdA({ children, href, ...props }: ComponentPropsWithoutRef<"a">) {
  return (
    <a
      href={href}
      className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  );
}

const markdownComponents = {
  h2: MdH2,
  h3: MdH3,
  h4: MdH4,
  p: MdP,
  ul: MdUl,
  ol: MdOl,
  li: MdLi,
  strong: MdStrong,
  code: MdCode,
  blockquote: MdBlockquote,
  table: MdTable,
  thead: MdThead,
  tr: MdTr,
  th: MdTh,
  td: MdTd,
  hr: MdHr,
  a: MdA,
};

export default function StudyCardPage() {
  const params = useParams();
  const domainId = params.id as string;

  const [card, setCard] = useState<StudyCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getStudyCard(domainId)
      .then(setCard)
      .catch(() => setError("Failed to load study card"))
      .finally(() => setLoading(false));
  }, [domainId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center flex-col gap-4">
        <p className="text-red-400 text-lg">{error || "Card not found"}</p>
        <Link
          href="/study"
          className="text-blue-400 hover:text-blue-300 text-sm"
        >
          &larr; Back to Study Cards
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-[800px] mx-auto px-6 py-3 flex items-center gap-4">
          <Link
            href="/study"
            className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-1.5 text-sm font-medium flex-shrink-0"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Study Cards
          </Link>
          <span className="text-gray-700">|</span>
          <h1 className="text-sm font-medium text-gray-200 truncate">
            {card.domain_name}
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[800px] mx-auto px-6 py-10">
        {/* Domain title */}
        <h1 className="text-2xl font-bold text-gray-50 mb-8">
          {card.domain_name}
        </h1>

        {/* Markdown body */}
        <article className="study-card-content">
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {card.content}
          </Markdown>
        </article>

        {/* Back to study cards */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <Link
            href="/study"
            className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors font-medium"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Study Cards
          </Link>
        </div>
      </div>

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          .sticky {
            position: static !important;
            border-bottom: 1px solid #ccc !important;
          }
          body,
          .min-h-screen {
            background: white !important;
            color: black !important;
          }
          .study-card-content h2,
          .study-card-content h3,
          .study-card-content h4,
          .study-card-content strong {
            color: black !important;
          }
          .study-card-content p,
          .study-card-content li,
          .study-card-content td {
            color: #333 !important;
          }
          .study-card-content th {
            color: black !important;
            background: #eee !important;
          }
          .study-card-content tr {
            border-color: #ccc !important;
          }
          .study-card-content code {
            background: #f0f0f0 !important;
            color: #333 !important;
          }
          .study-card-content blockquote {
            background: #f8f8f8 !important;
            border-color: #999 !important;
            color: #333 !important;
          }
          .study-card-content table {
            border-color: #ccc !important;
          }
          .study-card-content hr {
            border-color: #ccc !important;
          }
          a[href="/study"] {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
