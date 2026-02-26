"use client";

import { useParams, useRouter } from "next/navigation";
import { AlertCircle, Calendar, Clock, User } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

const MOCK_RFI = {
  id: "1",
  project_id: "p1",
  number: 1,
  formatted_number: "RFI-001",
  subject: "Concrete mix design for foundation footings",
  question:
    "What concrete mix design should be used for the spread footings on grid A-C? The structural drawings reference 4000 PSI but the geotechnical report recommends 5000 PSI.",
  official_response: null,
  status: "OPEN",
  priority: "HIGH",
  assigned_to_name: "Sarah Johnson",
  due_date: "2026-03-01",
  days_open: 5,
  cost_impact: false,
  schedule_impact: true,
  created_by_name: "John Smith",
  created_at: "2026-02-20T10:00:00Z",
  updated_at: "2026-02-20T10:00:00Z",
  comments_count: 2,
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "We've reviewed the geotech report and believe 4000 PSI per the structural drawings is correct.",
    author_name: "Alex Rivera",
    author_type: "SUB_USER",
    created_at: "2026-02-21T10:00:00Z",
    is_official_response: false,
  },
];

const PRIORITY_STYLES: Record<string, string> = {
  URGENT: "bg-red-100 text-red-700",
  HIGH: "bg-orange-100 text-orange-700",
  NORMAL: "bg-blue-100 text-blue-700",
  LOW: "bg-gray-100 text-gray-600",
};

export default function SubRFIDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const rfi = MOCK_RFI;

  const statusActions = [];
  if (rfi.status === "OPEN") {
    statusActions.push({
      label: "Respond",
      variant: "primary" as const,
      onClick: () => console.log("respond"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/sub/projects/${projectId}/rfis`}
        number={rfi.formatted_number}
        title={rfi.subject}
        status={rfi.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Question</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{rfi.question}</p>
          </Card>

          {rfi.official_response ? (
            <Card className="border-green-200 bg-green-50/50">
              <h2 className="text-sm font-semibold text-green-800 mb-3">Official Response</h2>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{rfi.official_response}</p>
            </Card>
          ) : (
            <Card className="border-dashed border-gray-300">
              <div className="text-center py-4">
                <p className="text-sm text-gray-400">Awaiting official response</p>
              </div>
            </Card>
          )}

          <CommentThread
            comments={MOCK_COMMENTS}
            onSubmit={(body) => console.log("Comment:", body)}
          />
        </div>

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
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_STYLES[rfi.priority] || ""}`}>
                    {rfi.priority}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Due Date
                </dt>
                <dd>{rfi.due_date ? new Date(rfi.due_date + "T00:00:00").toLocaleDateString() : "—"}</dd>
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
        </div>
      </div>
    </div>
  );
}
