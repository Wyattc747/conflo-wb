"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Pencil, Users, FileText, ClipboardList, HelpCircle,
  Clock, CheckCircle, X, Zap,
} from "lucide-react";
import { PhaseBadge } from "@/components/shared/PhaseBadge";
import { Card } from "@/components/shared/Card";
import { useProject } from "@/providers/ProjectProvider";

function QuickStatCard({
  label,
  value,
  sublabel,
  color,
}: {
  label: string;
  value: string;
  sublabel: string;
  color: string;
}) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sublabel}</p>
    </Card>
  );
}

function GettingStartedCard({
  icon: Icon,
  title,
  href,
}: {
  icon: React.ElementType;
  title: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:border-yellow-300 hover:bg-yellow-50 transition-colors text-center"
    >
      <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
        <Icon className="h-5 w-5 text-yellow-600" />
      </div>
      <span className="text-sm font-medium text-gray-700">{title}</span>
    </Link>
  );
}

export default function ProjectOverviewPage() {
  const { projectId } = useProject();
  const [showGettingStarted, setShowGettingStarted] = useState(true);

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
          <p className="text-sm text-gray-500">Project details and information</p>
        </div>
        <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
          <Pencil className="h-4 w-4" />
          Edit Project
        </button>
      </div>

      {/* Project hero card */}
      <Card className="mb-4">
        <div className="flex gap-5">
          {/* Project image placeholder */}
          <div className="hidden sm:flex h-24 w-24 rounded-lg bg-gray-100 items-center justify-center flex-shrink-0">
            <FileText className="h-8 w-8 text-gray-300" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-lg font-bold text-gray-900">Tech Campus Expansion</h2>
              <PhaseBadge phase="ACTIVE" />
            </div>
            <p className="text-sm text-gray-500 mb-1">
              1000 Innovation Way, Palo Alto, CA 94301
            </p>
            <p className="text-sm text-gray-600 mb-2">
              New 150,000 sq ft office building with underground parking and sustainable design
              features.
            </p>
            <p className="text-xs text-gray-400">Created February 3, 2026</p>
          </div>
        </div>
      </Card>

      {/* Getting started (dismissible) */}
      {showGettingStarted && (
        <Card className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              <h3 className="text-sm font-semibold text-gray-900">Getting Started</h3>
            </div>
            <button
              onClick={() => setShowGettingStarted(false)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-4 w-4 text-gray-400" />
            </button>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Here are some suggested next steps to set up your project
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <GettingStartedCard
              icon={Users}
              title="Add Team Members"
              href={`/app/projects/${projectId}/directory`}
            />
            <GettingStartedCard
              icon={FileText}
              title="Upload Documents"
              href={`/app/projects/${projectId}/documents`}
            />
            <GettingStartedCard
              icon={ClipboardList}
              title="Create Daily Log"
              href={`/app/projects/${projectId}/daily-logs`}
            />
            <GettingStartedCard
              icon={HelpCircle}
              title="Submit an RFI"
              href={`/app/projects/${projectId}/rfis`}
            />
          </div>
        </Card>
      )}

      {/* Quick stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <QuickStatCard label="OPEN RFIS" value="--" sublabel="Pending" color="text-gray-400" />
        <QuickStatCard label="SUBMITTALS" value="--" sublabel="Pending" color="text-gray-400" />
        <QuickStatCard label="TASKS DUE" value="--" sublabel="Pending" color="text-gray-400" />
        <QuickStatCard label="PUNCH ITEMS" value="--" sublabel="Pending" color="text-gray-400" />
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recent Activity */}
        <Card>
          <h3 className="text-base font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="flex flex-col items-center py-8 text-center">
            <Clock className="h-10 w-10 text-gray-300 mb-3" />
            <p className="text-sm text-gray-500">Recent activity will appear here</p>
          </div>
        </Card>

        {/* Action Items */}
        <Card>
          <h3 className="text-base font-semibold text-gray-900 mb-4">Action Items</h3>
          <div className="flex flex-col items-center py-8 text-center">
            <CheckCircle className="h-10 w-10 text-green-300 mb-3" />
            <p className="text-sm text-gray-500">All caught up!</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
