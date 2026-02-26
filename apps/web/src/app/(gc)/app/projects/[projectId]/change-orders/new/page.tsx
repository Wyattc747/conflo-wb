"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Loader2 } from "lucide-react";
import { toCents } from "@/lib/money";
import { useCreateChangeOrder } from "@/hooks/use-change-orders";

export default function NewChangeOrderPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useState(() => { getToken().then(setToken); });

  const createMutation = useCreateChangeOrder(projectId, token);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [reason, setReason] = useState("");
  const [amount, setAmount] = useState("");
  const [scheduleImpact, setScheduleImpact] = useState("0");
  const [priority, setPriority] = useState("NORMAL");
  const [drawingRef, setDrawingRef] = useState("");
  const [specSection, setSpecSection] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = () => {
    if (!title.trim()) { setError("Title is required"); return; }
    if (!reason) { setError("Reason is required"); return; }
    setError("");

    createMutation.mutate(
      {
        title: title.trim(),
        description: description.trim() || undefined,
        reason,
        amount: toCents(amount || "0"),
        schedule_impact_days: parseInt(scheduleImpact) || 0,
        priority,
        drawing_reference: drawingRef.trim() || undefined,
        spec_section: specSection.trim() || undefined,
      },
      {
        onSuccess: (data) => {
          const coId = data?.data?.id;
          router.push(coId
            ? `/app/projects/${projectId}/change-orders/${coId}`
            : `/app/projects/${projectId}/change-orders`
          );
        },
        onError: () => {
          setError("Failed to create change order. Please try again.");
        },
      }
    );
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push(`/app/projects/${projectId}/change-orders`)} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-semibold">New Change Order</h1>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6 max-w-3xl">
        {error && <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Brief description of the change" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} placeholder="Detailed description of the change and justification..." className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason *</label>
            <select value={reason} onChange={(e) => setReason(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">Select reason...</option>
              <option value="OWNER_REQUESTED">Owner Requested</option>
              <option value="DESIGN_CHANGE">Design Change</option>
              <option value="DESIGN_CONFLICT">Design Conflict</option>
              <option value="UNFORESEEN_CONDITION">Unforeseen Condition</option>
              <option value="CODE_COMPLIANCE">Code Compliance</option>
              <option value="VALUE_ENGINEERING">Value Engineering</option>
              <option value="SCOPE_CLARIFICATION">Scope Clarification</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="LOW">Low</option>
              <option value="NORMAL">Normal</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Amount ($)</label>
            <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" step="0.01" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Schedule Impact (days)</label>
            <input type="number" value={scheduleImpact} onChange={(e) => setScheduleImpact(e.target.value)} min="0" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Drawing Reference</label>
            <input type="text" value={drawingRef} onChange={(e) => setDrawingRef(e.target.value)} placeholder="e.g. S-201" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Spec Section</label>
            <input type="text" value={specSection} onChange={(e) => setSpecSection(e.target.value)} placeholder="e.g. 03 30 00" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button onClick={() => router.push(`/app/projects/${projectId}/change-orders`)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={createMutation.isPending} className="px-4 py-2 bg-[#1B2A4A] text-white rounded-lg text-sm font-medium hover:bg-[#243558] disabled:opacity-50 flex items-center gap-2">
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Create Change Order
          </button>
        </div>
      </div>
    </div>
  );
}
