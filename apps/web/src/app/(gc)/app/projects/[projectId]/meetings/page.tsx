"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Users2, Clock, Video, MapPin, RotateCw } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Meeting } from "@/types/meeting";

const TYPE_STYLES: Record<string, string> = {
  OAC: "bg-purple-100 text-purple-700",
  PROGRESS: "bg-blue-100 text-blue-700",
  SAFETY: "bg-red-100 text-red-700",
  PRE_BID: "bg-orange-100 text-orange-700",
  KICKOFF: "bg-green-100 text-green-700",
  COORDINATION: "bg-cyan-100 text-cyan-700",
  CLOSEOUT: "bg-gray-100 text-gray-600",
  OTHER: "bg-gray-100 text-gray-600",
};

const MOCK_MEETINGS: Meeting[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "MTG-001",
    title: "Weekly OAC Meeting",
    meeting_type: "OAC",
    status: "COMPLETED",
    scheduled_date: "2026-02-19",
    start_time: "10:00",
    end_time: "11:30",
    location: "Conference Room A",
    virtual_provider: null,
    virtual_link: null,
    attendees: ["u1", "u2", "u3"],
    agenda: "1. Safety update\n2. Schedule review\n3. Budget update",
    minutes: "Meeting conducted as scheduled.",
    action_items: [{ description: "Submit revised schedule", assignee: "u2", due_date: "2026-02-26" }],
    recurring: true,
    recurrence_rule: "WEEKLY",
    minutes_published: true,
    minutes_published_at: "2026-02-19T16:00:00Z",
    created_by_name: "John Smith",
    created_at: "2026-02-10T08:00:00Z",
    updated_at: "2026-02-19T16:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "MTG-002",
    title: "Weekly OAC Meeting",
    meeting_type: "OAC",
    status: "SCHEDULED",
    scheduled_date: "2026-02-26",
    start_time: "10:00",
    end_time: "11:30",
    location: "Conference Room A",
    attendees: ["u1", "u2", "u3"],
    agenda: "1. Safety update\n2. Schedule review\n3. Budget update",
    minutes: null,
    action_items: [],
    recurring: true,
    recurrence_rule: "WEEKLY",
    parent_meeting_id: "1",
    minutes_published: false,
    created_by_name: "John Smith",
    created_at: "2026-02-19T16:00:00Z",
    updated_at: "2026-02-19T16:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "MTG-003",
    title: "Structural Steel Coordination",
    meeting_type: "COORDINATION",
    status: "SCHEDULED",
    scheduled_date: "2026-02-27",
    start_time: "14:00",
    end_time: "15:00",
    location: null,
    virtual_provider: "ZOOM",
    virtual_link: "https://zoom.us/j/123456",
    attendees: ["u1", "u2"],
    agenda: "Review steel connection details.",
    minutes: null,
    action_items: [],
    recurring: false,
    minutes_published: false,
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-22T10:00:00Z",
    updated_at: "2026-02-22T10:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    number: 4,
    formatted_number: "MTG-004",
    title: "Weekly Safety Meeting",
    meeting_type: "SAFETY",
    status: "CANCELLED",
    scheduled_date: "2026-02-20",
    start_time: "07:00",
    end_time: "07:30",
    location: "Job Site Trailer",
    attendees: ["u1"],
    agenda: null,
    minutes: null,
    action_items: [],
    recurring: true,
    recurrence_rule: "WEEKLY",
    minutes_published: false,
    created_by_name: "Mike Chen",
    created_at: "2026-02-10T08:00:00Z",
    updated_at: "2026-02-20T07:00:00Z",
  },
];

export default function MeetingsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sortKey, setSortKey] = useState("scheduled_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_MEETINGS;
  if (statusFilter) filtered = filtered.filter((m) => m.status === statusFilter);
  if (typeFilter) filtered = filtered.filter((m) => m.meeting_type === typeFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (m) =>
        m.title.toLowerCase().includes(s) ||
        m.formatted_number.toLowerCase().includes(s)
    );
  }

  const columns: Column<Meeting>[] = [
    {
      key: "number",
      label: "#",
      sortable: true,
      className: "w-28",
      render: (row) => (
        <span className="font-mono text-sm font-medium text-[#1B2A4A]">{row.formatted_number}</span>
      ),
    },
    {
      key: "title",
      label: "Title",
      sortable: true,
      className: "max-w-xs",
      render: (row) => (
        <div>
          <span className="font-medium truncate block max-w-xs">{row.title}</span>
          {row.recurring && (
            <span className="text-[10px] text-gray-500 flex items-center gap-0.5 mt-0.5">
              <RotateCw className="h-2.5 w-2.5" />Recurring
            </span>
          )}
        </div>
      ),
    },
    {
      key: "meeting_type",
      label: "Type",
      sortable: true,
      render: (row) => (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_STYLES[row.meeting_type] || TYPE_STYLES.OTHER}`}>
          {row.meeting_type.replace(/_/g, " ")}
        </span>
      ),
    },
    {
      key: "scheduled_date",
      label: "Date",
      sortable: true,
      render: (row) => {
        if (!row.scheduled_date) return "\u2014";
        return new Date(row.scheduled_date + "T00:00:00").toLocaleDateString();
      },
    },
    {
      key: "start_time",
      label: "Time",
      render: (row) => {
        if (!row.start_time) return "\u2014";
        return (
          <span className="flex items-center gap-1 text-sm">
            <Clock className="h-3.5 w-3.5 text-gray-400" />
            {row.start_time}{row.end_time ? ` - ${row.end_time}` : ""}
          </span>
        );
      },
    },
    {
      key: "location",
      label: "Location",
      render: (row) => {
        if (row.virtual_provider) {
          return (
            <span className="flex items-center gap-1 text-sm text-blue-600">
              <Video className="h-3.5 w-3.5" />
              {row.virtual_provider}
            </span>
          );
        }
        if (row.location) {
          return (
            <span className="flex items-center gap-1 text-sm">
              <MapPin className="h-3.5 w-3.5 text-gray-400" />
              {row.location}
            </span>
          );
        }
        return "\u2014";
      },
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "minutes_published",
      label: "Minutes",
      render: (row) =>
        row.minutes_published ? (
          <span className="text-xs text-green-600 font-medium">Published</span>
        ) : row.status === "COMPLETED" ? (
          <span className="text-xs text-orange-600">Pending</span>
        ) : null,
    },
  ];

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const hasData = MOCK_MEETINGS.length > 0;
  const upcomingCount = MOCK_MEETINGS.filter((m) => m.status === "SCHEDULED").length;
  const completedCount = MOCK_MEETINGS.filter((m) => m.status === "COMPLETED").length;

  return (
    <div>
      <PageHeader
        title="Meetings"
        subtitle="Schedule meetings and track minutes"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/meetings/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Meeting
          </button>
        }
      />

      {hasData && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Total</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{MOCK_MEETINGS.length}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Upcoming</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{upcomingCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Completed</div>
            <div className="text-2xl font-bold text-green-600 mt-1">{completedCount}</div>
          </div>
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search meetings..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Scheduled", value: "SCHEDULED" },
                  { label: "In Progress", value: "IN_PROGRESS" },
                  { label: "Completed", value: "COMPLETED" },
                  { label: "Cancelled", value: "CANCELLED" },
                ],
              },
              {
                key: "type",
                label: "All Types",
                value: typeFilter,
                onChange: setTypeFilter,
                options: [
                  { label: "OAC", value: "OAC" },
                  { label: "Progress", value: "PROGRESS" },
                  { label: "Safety", value: "SAFETY" },
                  { label: "Pre-Bid", value: "PRE_BID" },
                  { label: "Kickoff", value: "KICKOFF" },
                  { label: "Coordination", value: "COORDINATION" },
                  { label: "Closeout", value: "CLOSEOUT" },
                ],
              },
            ]}
          />
          <DataTable
            columns={columns}
            data={filtered}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={handleSort}
            onRowClick={(row) => router.push(`/app/projects/${projectId}/meetings/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Users2}
          title="No meetings yet"
          description="Schedule your first meeting to start tracking agendas and minutes."
          actionLabel="Schedule Meeting"
          onAction={() => router.push(`/app/projects/${projectId}/meetings/new`)}
        />
      )}
    </div>
  );
}
