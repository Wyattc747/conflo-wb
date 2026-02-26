"use client";

import { useParams, useRouter } from "next/navigation";
import { Calendar, MapPin, User, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

const RESULT_STYLES: Record<string, string> = {
  PASS: "bg-green-100 text-green-700",
  FAIL: "bg-red-100 text-red-700",
  PARTIAL: "bg-yellow-100 text-yellow-700",
  N_A: "bg-gray-100 text-gray-500",
};

const RESULT_ICONS: Record<string, React.ReactNode> = {
  PASS: <CheckCircle className="h-4 w-4 text-green-600" />,
  FAIL: <XCircle className="h-4 w-4 text-red-600" />,
  PARTIAL: <AlertTriangle className="h-4 w-4 text-yellow-600" />,
};

const MOCK_INSPECTION = {
  id: "4",
  project_id: "p1",
  number: 4,
  formatted_number: "INSP-004",
  title: "Roofing membrane inspection",
  template_id: "t4",
  template_name: "Roofing",
  category: "BUILDING_ENVELOPE",
  scheduled_date: "2026-02-25",
  scheduled_time: "08:00",
  location: "Roof, All Areas",
  inspector_name: "Mark Taylor",
  inspector_company: "ABC General Contractors",
  status: "COMPLETED",
  overall_result: "FAIL",
  checklist_results: [
    { item_label: "Membrane adhesion test", result: "PASS", notes: null },
    { item_label: "Seam integrity", result: "FAIL", notes: "Seam separation at parapet NE corner. Approximately 8 linear feet of separated seam. Sub notified." },
    { item_label: "Flashing details", result: "PASS", notes: null },
    { item_label: "Drainage slope verification", result: "PASS", notes: "Slope confirmed at 1/4\" per foot minimum" },
  ],
  photo_ids: ["ph3"],
  notes: "Failed due to seam separation at NE parapet. Sub to repair and re-inspect. All other items satisfactory. Re-inspection scheduled for March 2.",
  comments_count: 3,
  created_by: "u3",
  created_by_name: "Mike Chen",
  created_at: "2026-02-18T07:00:00Z",
  completed_at: "2026-02-25T10:00:00Z",
  updated_at: "2026-02-25T10:00:00Z",
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "Roof inspection scheduled for 8:00 AM Tuesday. Make sure roofing sub has area cleaned up and accessible.",
    author_name: "Mike Chen",
    author_type: "GC_USER",
    created_at: "2026-02-22T16:00:00Z",
    is_official_response: false,
  },
  {
    id: "c2",
    body: "Inspection complete. Found seam separation issue at NE parapet. See checklist notes for details.",
    author_name: "Mark Taylor",
    author_type: "GC_USER",
    created_at: "2026-02-25T10:15:00Z",
    is_official_response: false,
  },
  {
    id: "c3",
    body: "Notified roofing sub. They will have a crew on site Thursday to address the seam issue.",
    author_name: "Mike Chen",
    author_type: "GC_USER",
    created_at: "2026-02-25T14:00:00Z",
    is_official_response: false,
  },
];

export default function InspectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const inspection = MOCK_INSPECTION;

  const statusActions = [];
  if (inspection.status === "SCHEDULED") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => {},
    });
    statusActions.push({
      label: "Start Inspection",
      variant: "primary" as const,
      onClick: () => console.log("start"),
    });
  }
  if (inspection.status === "IN_PROGRESS") {
    statusActions.push({
      label: "Complete",
      variant: "primary" as const,
      onClick: () => console.log("complete"),
    });
  }

  const passCount = inspection.checklist_results.filter((r) => r.result === "PASS").length;
  const failCount = inspection.checklist_results.filter((r) => r.result === "FAIL").length;
  const totalCount = inspection.checklist_results.length;

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/inspections`}
        number={inspection.formatted_number}
        title={inspection.title}
        status={inspection.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column -- main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Overall Result */}
          {inspection.overall_result && (
            <Card className={inspection.overall_result === "FAIL" ? "border-red-200 bg-red-50/50" : inspection.overall_result === "PASS" ? "border-green-200 bg-green-50/50" : ""}>
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900">Overall Result</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${RESULT_STYLES[inspection.overall_result] || ""}`}>
                  {inspection.overall_result}
                </span>
              </div>
              {inspection.notes && (
                <p className="text-sm text-gray-700 mt-3 whitespace-pre-wrap">{inspection.notes}</p>
              )}
            </Card>
          )}

          {/* Checklist Results */}
          {inspection.checklist_results.length > 0 && (
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-900">
                  Checklist ({passCount}/{totalCount} passed)
                </h2>
                {failCount > 0 && (
                  <span className="text-xs text-red-600 font-medium">{failCount} failed</span>
                )}
              </div>
              <div className="space-y-3">
                {inspection.checklist_results.map((item, idx) => (
                  <div key={idx} className={`p-3 rounded-lg border ${item.result === "FAIL" ? "border-red-200 bg-red-50/30" : "border-gray-100"}`}>
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        {RESULT_ICONS[item.result] || <div className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <span className="text-sm font-medium">{item.item_label}</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${RESULT_STYLES[item.result] || ""}`}>
                        {item.result}
                      </span>
                    </div>
                    {item.notes && (
                      <p className="text-xs text-gray-600 mt-2 ml-7">{item.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Comments */}
          <CommentThread
            comments={MOCK_COMMENTS}
            onSubmit={(body) => console.log("Comment:", body)}
          />
        </div>

        {/* Right column -- metadata */}
        <div className="space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Details</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Category</dt>
                <dd className="font-medium">{inspection.category.replace(/_/g, " ")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Template</dt>
                <dd>{inspection.template_name || "Custom"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Scheduled
                </dt>
                <dd>
                  {inspection.scheduled_date
                    ? new Date(inspection.scheduled_date + "T00:00:00").toLocaleDateString()
                    : "—"}
                  {inspection.scheduled_time && <span className="text-gray-400 ml-1">{inspection.scheduled_time}</span>}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" /> Location
                </dt>
                <dd>{inspection.location || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> Inspector
                </dt>
                <dd>
                  <div className="text-right">
                    <div className="font-medium">{inspection.inspector_name || "—"}</div>
                    {inspection.inspector_company && (
                      <div className="text-xs text-gray-400">{inspection.inspector_company}</div>
                    )}
                  </div>
                </dd>
              </div>
              {inspection.completed_at && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Completed</dt>
                  <dd>{new Date(inspection.completed_at).toLocaleDateString()}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd>{inspection.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(inspection.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>
    </div>
  );
}
