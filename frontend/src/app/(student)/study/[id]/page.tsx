"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Markdown from "react-markdown";
import { api } from "@/lib/api";

type StudyCard = {
  domain_id: string;
  domain_name: string;
  content: string;
};

export default function StudyCardPage() {
  const params = useParams();
  const domainId = params.id as string;

  const [card, setCard] = useState<StudyCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getStudyCard(domainId)
      .then(setCard)
      .catch(() => setError("Failed to load study card"))
      .finally(() => setLoading(false));
  }, [domainId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading...</p>
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-red-400 text-lg">{error || "Card not found"}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link href="/study" className="text-blue-400 hover:text-blue-300 text-sm mb-6 inline-block">
          &larr; Back to Study Cards
        </Link>

        <h1 className="text-2xl font-bold mb-6">{card.domain_name}</h1>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 prose prose-invert max-w-none prose-headings:text-gray-100 prose-p:text-gray-300 prose-a:text-blue-400 prose-strong:text-gray-200 prose-code:text-blue-300 prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-800 prose-li:text-gray-300">
          <Markdown>{card.content}</Markdown>
        </div>
      </div>
    </div>
  );
}
