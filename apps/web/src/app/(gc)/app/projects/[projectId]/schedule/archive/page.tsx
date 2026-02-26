"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Calendar, FileText, Download } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";
import type { ScheduleVersion } from "@/types/schedule";

const MOCK_VERSIONS: ScheduleVersion[] = [
  {
    id: "v1",
    project_id: "p1",
    version_type: "FULL_SCHEDULE",
    version_number: 1,
    title: "Baseline Schedule",
    notes: "Initial baseline schedule approved by owner. Includes all phases from excavation through closeout.",
    snapshot_data: {},
    published_by: "u1",
    published_at: "2026-02-05T10:00:00Z",
  },
  {
    id: "v2",
    project_id: "p1",
    version_type: "FULL_SCHEDULE",
    version_number: 2,
    title: "Schedule Update #1 - Weather Delay",
    notes: "Updated schedule reflecting 2-day weather delay on foundation excavation. Critical path adjusted.",
    snapshot_data: {},
    published_by: "u1",
    published_at: "2026-02-20T14:00:00Z",
  },
  {
    id: "v3",
    project_id: "p1",
    version_type: "LOOK_AHEAD",
    version_number: 1,
    title: "3-Week Look Ahead - Feb 24",
    notes: "Look ahead for weeks of Feb 24, Mar 3, and Mar 10.",
    snapshot_data: {},
    published_by: "u2",
    published_at: "2026-02-24T08:00:00Z",
  },
  {
    id: "v4",
    project_id: "p1",
    version_type: "LOOK_AHEAD",
    version_number: 2,
    title: "3-Week Look Ahead - Mar 3",
    notes: "Updated look ahead reflecting concrete pour progress.",
    snapshot_data: {},
    published_by: "u2",
    published_at: "2026-03-03T08:00:00Z",
  },
];

export default function ScheduleArchivePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const fullSchedules = MOCK_VERSIONS.filter((v) => v.version_type === "FULL_SCHEDULE");
  const lookAheads = MOCK_VERSIONS.filter((v) => v.version_type === "LOOK_AHEAD");

  const hasData = MOCK_VERSIONS.length > 0;

  const renderVersion = (version: ScheduleVersion) => (
    <div
      key={version.id}
      className="flex items-start gap-4 p-4 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50/50 transition-colors cursor-pointer"
    >
      <div className="flex-shrink-0 mt-0.5">
        <div className="w-8 h-8 rounded-lg bg-[#1B2A4A]/10 flex items-center justify-center">
          <FileText className="h-4 w-4 text-[#1B2A4A]" />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{version.title}</span>
          <span className="text-xs text-gray-400">v{version.version_number}</span>
        </div>
        {version.notes && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{version.notes}</p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          Published {new Date(version.published_at).toLocaleDateString()} at{" "}
          {new Date(version.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); console.log("download", version.id); }}
        className="flex-shrink-0 p-2 rounded hover:bg-gray-200"
        title="Download"
      >
        <Download className="h-4 w-4 text-gray-400" />
      </button>
    </div>
  );

  return (
    <div>
      <PageHeader
        title={
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/app/projects/${projectId}/schedule`)}
              className="p-1 rounded hover:bg-gray-200"
            >
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </button>
            <span>Schedule Archive</span>
          </div>
        }
        subtitle="View published schedule versions"
      />

      {hasData ? (
        <div className="space-y-5">
          {/* Full Schedule Versions */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-[#2E75B6]" />
              Full Schedule ({fullSchedules.length})
            </h2>
            <div className="space-y-2">
              {fullSchedules.map(renderVersion)}
            </div>
          </Card>

          {/* Look Ahead Versions */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-[#2E75B6]" />
              Look Ahead ({lookAheads.length})
            </h2>
            <div className="space-y-2">
              {lookAheads.map(renderVersion)}
            </div>
          </Card>
        </div>
      ) : (
        <EmptyState
          icon={Calendar}
          title="No published versions"
          description="Published schedule versions will appear here. Use the Publish button on the Schedule page to create a version."
        />
      )}
    </div>
  );
}
