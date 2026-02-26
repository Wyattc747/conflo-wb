"use client";

import { useParams, useRouter } from "next/navigation";
import { AlertCircle, Calendar, Clock, User } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

// Mock data
const MOCK_RFI = {
  id: "1",
  project_id: "p1",
  number: 1,
  formatted_number: "RFI-001",
  subject: "Concrete mix design for foundation footings",
  question:
    "What concrete mix design should be used for the spread footings on grid A-C? The structural drawings reference 4000 PSI but the geotechnical report recommends 5000 PSI for the soil conditions. Please clarify which specification takes precedence.",
  official_response: null,
  status: "OPEN",
  priority: "HIGH",
  assigned_to: "u2",
  assigned_to_name: "Sarah Johnson",
  due_date: "2026-03-01",
  days_open: 5,
  cost_impact: false,
  schedule_impact: true,
  drawing_reference: "S-101",
  spec_section: "03 30 00",
  created_by: "u1",
  created_by_name: "John Smith",
  responded_by: null,
  responded_by_name: null,
  responded_at: null,
  created_at: "2026-02-20T10:00:00Z",
  updated_at: "2026-02-20T10:00:00Z",
  comments_count: 3,
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "I've reviewed the geotechnical report — the 5000 PSI recommendation is for the soil bearing, not the concrete mix. Let me confirm with the structural engineer.",
    author_name: "Sarah Johnson",
    author_type: "GC_USER",
    created_at: "2026-02-21T09:30:00Z",
    is_official_response: false,
  },
  {
    id: "c2",
    body: "Structural engineer confirmed: Use 4000 PSI per S-101. The geotech 5000 PSI refers to soil bearing capacity, not concrete strength. Will prepare formal response.",
    author_name: "Sarah Johnson",
    author_type: "GC_USER",
    created_at: "2026-02-22T11:00:00Z",
    is_official_response: false,
  },
  {
    id: "c3",
    body: "Thanks Sarah. We'll proceed with 4000 PSI once we get the official response.",
    author_name: "John Smith",
    author_type: "GC_USER",
    created_at: "2026-02-22T14:00:00Z",
    is_official_response: false,
  },
];

const PRIORITY_STYLES: Record<string, string> = {
  URGENT: "bg-red-100 text-red-700",
  HIGH: "bg-orange-100 text-orange-700",
  NORMAL: "bg-blue-100 text-blue-700",
  LOW: "bg-gray-100 text-gray-600",
};

export default function RFIDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const rfi = MOCK_RFI;

  const statusActions = [];
  if (rfi.status === "OPEN") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => {},
    });
    statusActions.push({
      label: "Respond",
      variant: "primary" as const,
      onClick: () => console.log("respond"),
    });
    statusActions.push({
      label: "Close",
      variant: "secondary" as const,
      onClick: () => console.log("close"),
    });
  }
  if (rfi.status === "RESPONDED") {
    statusActions.push({
      label: "Close",
      variant: "primary" as const,
      onClick: () => console.log("close"),
    });
  }
  if (rfi.status === "CLOSED") {
    statusActions.push({
      label: "Reopen",
      variant: "secondary" as const,
      onClick: () => console.log("reopen"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/rfis`}
        number={rfi.formatted_number}
        title={rfi.subject}
        status={rfi.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column — main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Question */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Question</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{rfi.question}</p>
          </Card>

          {/* Official Response */}
          {rfi.official_response ? (
            <Card className="border-green-200 bg-green-50/50">
              <h2 className="text-sm font-semibold text-green-800 mb-3">Official Response</h2>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{rfi.official_response}</p>
              {rfi.responded_by_name && (
                <p className="text-xs text-gray-500 mt-3">
                  Responded by {rfi.responded_by_name}
                  {rfi.responded_at && ` on ${new Date(rfi.responded_at).toLocaleDateString()}`}
                </p>
              )}
            </Card>
          ) : rfi.status === "OPEN" ? (
            <Card className="border-dashed border-gray-300">
              <div className="text-center py-4">
                <p className="text-sm text-gray-400">Awaiting official response</p>
              </div>
            </Card>
          ) : null}

          {/* Comments */}
          <CommentThread
            comments={MOCK_COMMENTS}
            onSubmit={(body) => console.log("Comment:", body)}
          />
        </div>

        {/* Right column — metadata */}
        <div className="space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Details</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> Assigned To
                </dt>
                <dd className="font-medium">{rfi.assigned_to_name || "Unassigned"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Priority</dt>
                <dd>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      PRIORITY_STYLES[rfi.priority] || ""
                    }`}
                  >
                    {rfi.priority}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Due Date
                </dt>
                <dd className={rfi.due_date && rfi.status === "OPEN" && new Date(rfi.due_date) < new Date() ? "text-red-600 font-medium" : ""}>
                  {rfi.due_date ? new Date(rfi.due_date + "T00:00:00").toLocaleDateString() : "—"}
                </dd>
              </div>
              {rfi.days_open != null && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" /> Days Open
                  </dt>
                  <dd>{rfi.days_open}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd>{rfi.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(rfi.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>

          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Impact</h2>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <AlertCircle className={`h-4 w-4 ${rfi.cost_impact ? "text-red-500" : "text-gray-300"}`} />
                <span className={`text-sm ${rfi.cost_impact ? "text-red-600 font-medium" : "text-gray-400"}`}>
                  {rfi.cost_impact ? "Cost Impact" : "No Cost Impact"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className={`h-4 w-4 ${rfi.schedule_impact ? "text-orange-500" : "text-gray-300"}`} />
                <span className={`text-sm ${rfi.schedule_impact ? "text-orange-600 font-medium" : "text-gray-400"}`}>
                  {rfi.schedule_impact ? "Schedule Impact" : "No Schedule Impact"}
                </span>
              </div>
            </div>
          </Card>

          {(rfi.drawing_reference || rfi.spec_section) && (
            <Card>
              <h2 className="text-sm font-semibold text-gray-900 mb-3">References</h2>
              <dl className="space-y-2 text-sm">
                {rfi.drawing_reference && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Drawing</dt>
                    <dd className="font-mono">{rfi.drawing_reference}</dd>
                  </div>
                )}
                {rfi.spec_section && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Spec Section</dt>
                    <dd className="font-mono">{rfi.spec_section}</dd>
                  </div>
                )}
              </dl>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
