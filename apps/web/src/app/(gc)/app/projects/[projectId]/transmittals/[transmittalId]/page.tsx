"use client";

import { useParams, useRouter } from "next/navigation";
import { Calendar, User, Send, Package } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

const PURPOSE_STYLES: Record<string, string> = {
  FOR_APPROVAL: "bg-blue-100 text-blue-700",
  FOR_REVIEW: "bg-yellow-100 text-yellow-700",
  FOR_INFORMATION: "bg-gray-100 text-gray-600",
  FOR_RECORD: "bg-purple-100 text-purple-700",
  AS_REQUESTED: "bg-green-100 text-green-700",
};

const MOCK_TRANSMITTAL = {
  id: "1",
  project_id: "p1",
  number: 1,
  formatted_number: "TR-001",
  subject: "Revised structural drawings - Set 3",
  to_company: "Heritage Masonry",
  to_contact: "Tom Baker",
  from_company: "ABC General Contractors",
  from_contact: "John Smith",
  purpose: "FOR_REVIEW",
  description: "Updated structural drawings incorporating RFI-001 response. Please review and confirm receipt. Drawings reflect the 4000 PSI concrete mix confirmation per structural engineer direction.",
  status: "SENT",
  items: [
    { description: "S-201 Rev 3 - Foundation Plan", quantity: 2, document_type: "Drawing" },
    { description: "S-202 Rev 3 - Level 2 Framing", quantity: 2, document_type: "Drawing" },
    { description: "S-210 Rev 3 - Connection Details", quantity: 2, document_type: "Drawing" },
  ],
  sent_via: "EMAIL",
  sent_at: "2026-02-20T14:00:00Z",
  received_at: null as string | null,
  due_date: "2026-03-01",
  comments_count: 1,
  created_by: "u1",
  created_by_name: "John Smith",
  created_at: "2026-02-20T13:00:00Z",
  updated_at: "2026-02-20T14:00:00Z",
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "Sent via email with delivery confirmation. Hard copies will follow by courier tomorrow.",
    author_name: "John Smith",
    author_type: "GC_USER",
    created_at: "2026-02-20T14:05:00Z",
    is_official_response: false,
  },
];

export default function TransmittalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const transmittal = MOCK_TRANSMITTAL;

  const statusActions = [];
  if (transmittal.status === "DRAFT") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => {},
    });
    statusActions.push({
      label: "Send",
      variant: "primary" as const,
      onClick: () => console.log("send"),
    });
  }
  if (transmittal.status === "SENT") {
    statusActions.push({
      label: "Mark Acknowledged",
      variant: "primary" as const,
      onClick: () => console.log("acknowledge"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/transmittals`}
        number={transmittal.formatted_number}
        title={transmittal.subject}
        status={transmittal.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column -- main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Description */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Description</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {transmittal.description || "No description provided."}
            </p>
          </Card>

          {/* Items */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">
              Items ({transmittal.items.length})
            </h2>
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500">#</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500">Description</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-500">Type</th>
                    <th className="text-right px-3 py-2 text-xs font-medium text-gray-500">Qty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {transmittal.items.map((item, idx) => (
                    <tr key={idx}>
                      <td className="px-3 py-2 text-gray-400">{idx + 1}</td>
                      <td className="px-3 py-2 font-medium">{item.description}</td>
                      <td className="px-3 py-2 text-gray-600">{item.document_type || "—"}</td>
                      <td className="px-3 py-2 text-right">{item.quantity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

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
                <dt className="text-gray-500">Purpose</dt>
                <dd>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PURPOSE_STYLES[transmittal.purpose] || ""}`}>
                    {transmittal.purpose.replace(/_/g, " ")}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Send className="h-3.5 w-3.5" /> Sent Via
                </dt>
                <dd className="font-medium">{transmittal.sent_via.replace(/_/g, " ")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> To
                </dt>
                <dd>
                  <div className="text-right">
                    <div className="font-medium">{transmittal.to_contact || "—"}</div>
                    <div className="text-xs text-gray-400">{transmittal.to_company}</div>
                  </div>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> From
                </dt>
                <dd>
                  <div className="text-right">
                    <div className="font-medium">{transmittal.from_contact || "—"}</div>
                    <div className="text-xs text-gray-400">{transmittal.from_company}</div>
                  </div>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Due Date
                </dt>
                <dd>
                  {transmittal.due_date ? new Date(transmittal.due_date + "T00:00:00").toLocaleDateString() : "—"}
                </dd>
              </div>
              {transmittal.sent_at && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Sent</dt>
                  <dd>{new Date(transmittal.sent_at).toLocaleDateString()}</dd>
                </div>
              )}
              {transmittal.received_at && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Received</dt>
                  <dd>{new Date(transmittal.received_at).toLocaleDateString()}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Package className="h-3.5 w-3.5" /> Items
                </dt>
                <dd>{transmittal.items.length}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd>{transmittal.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(transmittal.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>
    </div>
  );
}
