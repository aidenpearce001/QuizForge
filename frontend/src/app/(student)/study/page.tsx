"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Subject = {
  id: string;
  name: string;
};

type StudyCard = {
  domain_id: string;
  domain_name: string;
  content: string;
};

export default function StudyPage() {
  const [cards, setCards] = useState<StudyCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const subjects: Subject[] = await api.getSubjects();
        if (subjects.length === 0) {
          setError("No subjects available");
          setLoading(false);
          return;
        }
        const data = await api.getStudyCards(subjects[0].id);
        setCards(data);
      } catch {
        setError("Failed to load study cards");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Loading study cards...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-red-400 text-lg">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Study Cards</h1>

        {cards.length === 0 ? (
          <p className="text-gray-400">No study cards available yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {cards.map((card) => (
              <Link
                key={card.domain_id}
                href={`/study/${card.domain_id}`}
                className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors block"
              >
                <h2 className="font-semibold text-blue-400 mb-2">{card.domain_name}</h2>
                <p className="text-sm text-gray-400 line-clamp-3">
                  {card.content?.slice(0, 100)}
                  {card.content?.length > 100 ? "..." : ""}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
