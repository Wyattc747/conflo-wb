"use client";

import { useParams, useRouter } from "next/navigation";
import { Calendar, Clock, User, BookOpen, FileText } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";
import { StatusBadge } from "@/components/shared/StatusBadge";

const MOCK_SUBMITTAL = {
  id: "1",
  project_id: "p1",
  number: 1,
  revision: 0,
  formatted_number: "001.00",
  title: "Structural steel shop drawings - Level 2",
  description: "Shop drawings for structural steel connections and member details on Level 2, grids A-F / 1-8. Includes moment connections, shear tabs, base plates, and embed plates per S-201 through S-210.",
  spec_section: "05 12 00",
  submittal_type: "SHOP_DRAWING",
  status: "SUBMITTED",
  sub_company_id: "sub1",
  sub_company_name: "Apex Steel Fabricators",
  assigned_to: "u2",
  assigned_to_name: "Sarah Johnson",
  due_date: "2026-03-10",
  days_open: 8,
  lead_time_days: 21,
  drawing_reference: "S-201 through S-210",
  review_notes: null as string | null,
  reviewed_by_name: null as string | null,
  reviewed_at: null as string | null,
  revision_history: [
    { revision: 0, formatted_number: "001.00", status: "SUBMITTED", created_at: "2026-02-18T10:00:00Z", reviewed_at: null },
  ],
  comments_count: 2,
  created_by: "u1",
  created_by_name: "John Smith",
  created_at: "2026-02-18T10:00:00Z",
  updated_at: "2026-02-20T10:00:00Z",
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "Shop drawings uploaded. Please review connections at grid B/4 -- the engineer may want to verify the moment connection detail.",
    author_name: "John Smith",
    author_type: "GC_USER",
    created_at: "2026-02-18T10:30:00Z",
    is_official_response: false,
  },
  {
    id: "c2",
    body: "Reviewing now. Will check the connection details against the structural calcs.",
    author_name: "Sarah Johnson",
    author_type: "GC_USER",
    created_at: "2026-02-19T09:00:00Z",
    is_official_response: false,
  },
];

const TYPE_LABELS: Record<string, string> = {
  SHOP_DRAWING: "Shop Drawing",
  PRODUCT_DATA: "Product Data",
  SAMPLE: "Sample",
  MOCK_UP: "Mock-Up",
  OTHER: "Other",
};

export default function SubmittalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const submittal = MOCK_SUBMITTAL;

  const statusActions = [];
  if (submittal.status === "DRAFT") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => {},
    });
    statusActions.push({
      label: "Submit for Review",
      variant: "primary" as const,
      onClick: () => console.log("submit"),
    });
  }
  if (submittal.status === "SUBMITTED") {
    statusActions.push({
      label: "Approve",
      variant: "primary" as const,
      onClick: () => console.log("approve"),
    });
    statusActions.push({
      label: "Approve as Noted",
      variant: "secondary" as const,
      onClick: () => console.log("approve_as_noted"),
    });
    statusActions.push({
      label: "Revise & Resubmit",
      variant: "secondary" as const,
      onClick: () => console.log("revise_and_resubmit"),
    });
    statusActions.push({
      label: "Reject",
      variant: "danger" as const,
      onClick: () => console.log("reject"),
    });
  }
  if (submittal.status === "REVISE_AND_RESUBMIT" || submittal.status === "REJECTED") {
    statusActions.push({
      label: "Create Revision",
      variant: "primary" as const,
      onClick: () => console.log("revise"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/submittals`}
        number={submittal.formatted_number}
        title={submittal.title}
        status={submittal.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column -- main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Description */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Description</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {submittal.description || "No description provided."}
            </p>
          </Card>

          {/* Review Notes */}
          {submittal.review_notes ? (
            <Card className="border-blue-200 bg-blue-50/50">
              <h2 className="text-sm font-semibold text-blue-800 mb-3">Review Notes</h2>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{submittal.review_notes}</p>
              {submittal.reviewed_by_name && (
                <p className="text-xs text-gray-500 mt-3">
                  Reviewed by {submittal.reviewed_by_name}
                  {submittal.reviewed_at && ` on ${new Date(submittal.reviewed_at).toLocaleDateString()}`}
                </p>
              )}
            </Card>
          ) : submittal.status === "SUBMITTED" ? (
            <Card className="border-dashed border-gray-300">
              <div className="text-center py-4">
                <p className="text-sm text-gray-400">Awaiting review</p>
              </div>
            </Card>
          ) : null}

          {/* Revision History */}
          {submittal.revision_history.length > 0 && (
            <Card>
              <h2 className="text-sm font-semibold text-gray-900 mb-3">Revision History</h2>
              <div className="space-y-3">
                {submittal.revision_history.map((rev, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-sm">
                    <div className="flex-shrink-0 w-2 h-2 rounded-full bg-[#2E75B6]" />
                    <div className="flex-1">
                      <span className="font-mono font-medium">{rev.formatted_number}</span>
                      <span className="text-gray-400 mx-2">-</span>
                      <StatusBadge status={rev.status} />
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(rev.created_at).toLocaleDateString()}
                    </span>
                    {rev.reviewed_at && (
                      <span className="text-xs text-gray-400">
                        Reviewed {new Date(rev.reviewed_at).toLocaleDateString()}
                      </span>
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
                <dt className="text-gray-500 flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5" /> Type
                </dt>
                <dd className="font-medium">{TYPE_LABELS[submittal.submittal_type || "OTHER"]}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <FileText className="h-3.5 w-3.5" /> Spec Section
                </dt>
                <dd className="font-mono">{submittal.spec_section || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Subcontractor</dt>
                <dd className="font-medium">{submittal.sub_company_name || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> Assigned To
                </dt>
                <dd className="font-medium">{submittal.assigned_to_name || "Unassigned"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Due Date
                </dt>
                <dd className={submittal.due_date && submittal.status === "SUBMITTED" && new Date(submittal.due_date) < new Date() ? "text-red-600 font-medium" : ""}>
                  {submittal.due_date ? new Date(submittal.due_date + "T00:00:00").toLocaleDateString() : "—"}
                </dd>
              </div>
              {submittal.days_open != null && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" /> Days Open
                  </dt>
                  <dd>{submittal.days_open}</dd>
                </div>
              )}
              {submittal.lead_time_days != null && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Lead Time</dt>
                  <dd>{submittal.lead_time_days} days</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd>{submittal.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(submittal.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>

          {submittal.drawing_reference && (
            <Card>
              <h2 className="text-sm font-semibold text-gray-900 mb-3">References</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Drawing</dt>
                  <dd className="font-mono">{submittal.drawing_reference}</dd>
                </div>
              </dl>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
