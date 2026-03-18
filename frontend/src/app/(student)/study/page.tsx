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

const DOMAIN_META: Record<
  string,
  { icon: string; color: string; description: string }
> = {
  "AWS Global Infrastructure & Cloud Economics": {
    icon: "\uD83C\uDF0D",
    color: "#3b82f6",
    description:
      "Regions, AZs, edge locations, cloud benefits, Well-Architected Framework, and CAF.",
  },
  "IAM \u2014 Identity, Access & Security Fundamentals": {
    icon: "\uD83D\uDD10",
    color: "#f59e0b",
    description:
      "Users, groups, roles, policies, MFA, root account, and access management.",
  },
  "Core Compute \u2014 EC2, Lambda & Containers": {
    icon: "\u2699\uFE0F",
    color: "#10b981",
    description:
      "EC2 instances, purchasing options, Lambda serverless, ECS, EKS, Fargate.",
  },
  "Storage Services \u2014 S3, EBS, EFS & Glacier": {
    icon: "\uD83D\uDCC1",
    color: "#8b5cf6",
    description:
      "Object, block, and file storage, storage classes, lifecycle policies, encryption.",
  },
  "Databases & Analytics on AWS": {
    icon: "\uD83D\uDDD2\uFE0F",
    color: "#ef4444",
    description:
      "RDS, Aurora, DynamoDB, Redshift, Athena, and data migration services.",
  },
  "Networking \u2014 VPC, CloudFront & Route 53": {
    icon: "\uD83C\uDF10",
    color: "#06b6d4",
    description:
      "VPC, subnets, security groups, NACLs, Direct Connect, CloudFront CDN.",
  },
  "Security, Compliance & Governance": {
    icon: "\uD83D\uDEE1\uFE0F",
    color: "#f97316",
    description:
      "Shared responsibility, Shield, WAF, GuardDuty, CloudTrail, Config, Organizations.",
  },
  "Billing, Pricing & AWS Support Plans": {
    icon: "\uD83D\uDCB0",
    color: "#84cc16",
    description:
      "Pricing models, free tier, Cost Explorer, Budgets, Trusted Advisor, support tiers.",
  },
};

function countTopics(content: string): number {
  const headings = content.match(/^#{2,3}\s+/gm);
  return headings ? headings.length : 0;
}

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
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-lg">Loading study cards...</p>
        </div>
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
      <div className="max-w-5xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-gray-50">
            Study Cards
          </h1>
          <p className="mt-2 text-gray-400 text-lg">
            Review key concepts before your quiz
          </p>
        </div>

        {cards.length === 0 ? (
          <p className="text-gray-400">No study cards available yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {cards.map((card) => {
              const meta = DOMAIN_META[card.domain_name] || {
                icon: "\uD83D\uDCD8",
                color: "#6b7280",
                description: "",
              };
              const topicCount = countTopics(card.content);

              return (
                <Link
                  key={card.domain_id}
                  href={`/study/${card.domain_id}`}
                  className="group relative bg-gray-900 border border-gray-800 rounded-xl overflow-hidden transition-all duration-200 hover:border-gray-600 hover:shadow-lg hover:shadow-blue-500/5 block"
                >
                  {/* Colored left border */}
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1 transition-all duration-200 group-hover:w-1.5"
                    style={{ backgroundColor: meta.color }}
                  />

                  <div className="p-6 pl-7">
                    {/* Icon and domain name */}
                    <div className="flex items-start gap-3 mb-3">
                      <span className="text-2xl leading-none flex-shrink-0 mt-0.5">
                        {meta.icon}
                      </span>
                      <h2 className="font-semibold text-gray-100 text-lg leading-snug group-hover:text-white transition-colors">
                        {card.domain_name}
                      </h2>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-400 mb-4 leading-relaxed">
                      {meta.description}
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                        {topicCount} topics
                      </span>
                      <span className="text-xs text-gray-500 group-hover:text-gray-300 transition-colors flex items-center gap-1">
                        Read card
                        <svg
                          className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                      </span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
