"use client";

import { useParams, useRouter } from "next/navigation";
import { Calendar, User, MapPin, Camera, CheckCircle, Shield } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-700",
  HIGH: "bg-orange-100 text-orange-700",
  MEDIUM: "bg-blue-100 text-blue-700",
  LOW: "bg-gray-100 text-gray-600",
};

const MOCK_PUNCH_ITEM = {
  id: "2",
  project_id: "p1",
  number: 2,
  formatted_number: "PL-002",
  title: "Missing fire caulk at MEP penetrations, Room 204",
  description: "Fire caulking missing at multiple MEP penetrations through 2-hour rated wall between Room 204 and corridor. Affects plumbing risers and electrical conduit runs. Must be corrected before fire marshal inspection.",
  location: "Room 204, Level 2",
  category: "FIRE_PROTECTION",
  priority: "CRITICAL",
  status: "COMPLETED_BY_SUB",
  assigned_to_sub_id: "sub2",
  assigned_to_sub_name: "Summit Fire Protection",
  assigned_to_user_id: "su1",
  assigned_to_user_name: "Ray Martinez",
  due_date: "2026-02-28",
  drawing_reference: "A-204",
  before_photo_ids: ["ph2", "ph3"],
  after_photo_ids: ["ph4", "ph5"],
  verification_photo_ids: [],
  completion_notes: "Fire caulk applied to all MEP penetrations per UL W-L-2079 listing. Used 3M CP 25WB+ caulk. All gaps sealed to minimum 1-inch depth.",
  completed_by: "sub_u1",
  completed_at: "2026-02-26T15:00:00Z",
  verification_notes: null as string | null,
  verified_by: null as string | null,
  verified_at: null as string | null,
  comments_count: 3,
  created_by: "u2",
  created_by_name: "Sarah Johnson",
  created_at: "2026-02-18T14:00:00Z",
  updated_at: "2026-02-26T15:00:00Z",
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "Identified during routine walkthrough. Multiple penetrations are missing fire caulk. This is a code violation that needs to be addressed before the fire marshal inspection on March 3.",
    author_name: "Sarah Johnson",
    author_type: "GC_USER",
    created_at: "2026-02-18T14:10:00Z",
    is_official_response: false,
  },
  {
    id: "c2",
    body: "We will have a crew on site Wednesday to address all penetrations in Room 204.",
    author_name: "Ray Martinez",
    author_type: "SUB_USER",
    created_at: "2026-02-20T09:00:00Z",
    is_official_response: false,
  },
  {
    id: "c3",
    body: "Work complete. All penetrations sealed with 3M CP 25WB+ per the UL listing. After photos uploaded.",
    author_name: "Ray Martinez",
    author_type: "SUB_USER",
    created_at: "2026-02-26T15:00:00Z",
    is_official_response: false,
  },
];

export default function PunchItemDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const item = MOCK_PUNCH_ITEM;

  const statusActions = [];
  if (item.status === "OPEN") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => {},
    });
  }
  if (item.status === "COMPLETED_BY_SUB") {
    statusActions.push({
      label: "Verify & Close",
      variant: "primary" as const,
      onClick: () => console.log("verify"),
    });
    statusActions.push({
      label: "Reject Completion",
      variant: "danger" as const,
      onClick: () => console.log("reject"),
    });
  }
  if (item.status === "VERIFIED_BY_GC") {
    statusActions.push({
      label: "Close",
      variant: "primary" as const,
      onClick: () => console.log("close"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/punch-list`}
        number={item.formatted_number}
        title={item.title}
        status={item.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column -- main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Description */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Description</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {item.description || "No description provided."}
            </p>
          </Card>

          {/* Before Photos */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Camera className="h-4 w-4" /> Before Photos ({item.before_photo_ids.length})
            </h2>
            {item.before_photo_ids.length > 0 ? (
              <div className="grid grid-cols-3 gap-3">
                {item.before_photo_ids.map((id) => (
                  <div key={id} className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
                    <Camera className="h-8 w-8 text-gray-300" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No before photos</p>
            )}
          </Card>

          {/* Completion Notes */}
          {item.completion_notes && (
            <Card className="border-blue-200 bg-blue-50/50">
              <h2 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" /> Completion Notes
              </h2>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.completion_notes}</p>
              {item.completed_at && (
                <p className="text-xs text-gray-500 mt-3">
                  Completed on {new Date(item.completed_at).toLocaleDateString()}
                </p>
              )}
            </Card>
          )}

          {/* After Photos */}
          {item.after_photo_ids.length > 0 && (
            <Card>
              <h2 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Camera className="h-4 w-4" /> After Photos ({item.after_photo_ids.length})
              </h2>
              <div className="grid grid-cols-3 gap-3">
                {item.after_photo_ids.map((id) => (
                  <div key={id} className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
                    <Camera className="h-8 w-8 text-gray-300" />
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Verification Notes */}
          {item.verification_notes && (
            <Card className="border-green-200 bg-green-50/50">
              <h2 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-2">
                <Shield className="h-4 w-4" /> Verification Notes
              </h2>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.verification_notes}</p>
              {item.verified_at && (
                <p className="text-xs text-gray-500 mt-3">
                  Verified on {new Date(item.verified_at).toLocaleDateString()}
                </p>
              )}
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
                  <MapPin className="h-3.5 w-3.5" /> Location
                </dt>
                <dd className="font-medium">{item.location || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Category</dt>
                <dd className="font-medium">{item.category.replace(/_/g, " ")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Priority</dt>
                <dd>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_STYLES[item.priority] || ""}`}>
                    {item.priority}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <User className="h-3.5 w-3.5" /> Assigned Sub
                </dt>
                <dd className="font-medium">{item.assigned_to_sub_name || "Unassigned"}</dd>
              </div>
              {item.assigned_to_user_name && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Contact</dt>
                  <dd>{item.assigned_to_user_name}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> Due Date
                </dt>
                <dd className={item.due_date && ["OPEN", "IN_PROGRESS"].includes(item.status) && new Date(item.due_date) < new Date() ? "text-red-600 font-medium" : ""}>
                  {item.due_date ? new Date(item.due_date + "T00:00:00").toLocaleDateString() : "—"}
                </dd>
              </div>
              {item.drawing_reference && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Drawing</dt>
                  <dd className="font-mono">{item.drawing_reference}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd>{item.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(item.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>
    </div>
  );
}
