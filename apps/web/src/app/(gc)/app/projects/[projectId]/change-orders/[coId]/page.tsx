"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Send, DollarSign, Clock, Loader2 } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatMoney } from "@/lib/money";
import { useChangeOrder, useSubmitToOwner } from "@/hooks/use-change-orders";

export default function ChangeOrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const coId = params.coId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useState(() => { getToken().then(setToken); });

  const { data, isLoading, error } = useChangeOrder("gc", projectId, coId, token);
  const submitToOwner = useSubmitToOwner(projectId, coId, token);

  const co = data?.data;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !co) {
    return (
      <div>
        <button onClick={() => router.push(`/app/projects/${projectId}/change-orders`)} className="text-gray-400 hover:text-gray-600 mb-4 flex items-center gap-2">
          <ArrowLeft className="h-5 w-5" /> Back to Change Orders
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          Change order not found or failed to load.
        </div>
      </div>
    );
  }

  const canSubmitToOwner = ["DRAFT", "PRICING_COMPLETE", "PRICING_REQUESTED"].includes(co.status);

  const handleSubmitToOwner = () => {
    if (confirm("Submit this change order to the owner for approval?")) {
      submitToOwner.mutate();
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push(`/app/projects/${projectId}/change-orders`)} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3 flex-1">
          <span className="font-mono text-lg font-semibold">{co.formatted_number}</span>
          <StatusBadge status={co.status} />
          {co.priority !== "NORMAL" && (
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
              co.priority === "HIGH" || co.priority === "URGENT" ? "bg-red-100 text-red-800" : "bg-blue-100 text-blue-700"
            }`}>{co.priority}</span>
          )}
        </div>
        {canSubmitToOwner && (
          <button
            onClick={handleSubmitToOwner}
            disabled={submitToOwner.isPending}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] disabled:opacity-50 flex items-center gap-2"
          >
            {submitToOwner.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Submit to Owner
          </button>
        )}
      </div>

      <h2 className="text-xl font-semibold mb-2">{co.title}</h2>
      {co.description && <p className="text-gray-600 mb-6">{co.description}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Financial Summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> Cost Summary
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Sub Amount</span>
              <span className="text-sm font-medium">{formatMoney(co.amount)}</span>
            </div>
            {co.markup_percent != null && (
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Markup ({co.markup_percent}%)</span>
                <span className="text-sm">{formatMoney(co.markup_amount)}</span>
              </div>
            )}
            <div className="flex justify-between py-2 bg-blue-50 -mx-5 px-5 rounded-b-lg">
              <span className="text-sm font-semibold text-[#1B2A4A]">GC Amount</span>
              <span className="text-lg font-bold text-[#1B2A4A]">{formatMoney(co.gc_amount)}</span>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider">Details</h3>
          <div className="space-y-3 text-sm">
            <div><span className="text-gray-500">Reason:</span> <span className="ml-2">{(co.reason || "").replace(/_/g, " ")}</span></div>
            <div><span className="text-gray-500">Cost Code:</span> <span className="ml-2 font-mono">{co.cost_code || "\u2014"}</span></div>
            {co.drawing_reference && <div><span className="text-gray-500">Drawing Ref:</span> <span className="ml-2">{co.drawing_reference}</span></div>}
            {co.spec_section && <div><span className="text-gray-500">Spec Section:</span> <span className="ml-2">{co.spec_section}</span></div>}
            <div><span className="text-gray-500">Created By:</span> <span className="ml-2">{co.created_by_name || "\u2014"}</span></div>
            <div><span className="text-gray-500">Created:</span> <span className="ml-2">{new Date(co.created_at).toLocaleDateString()}</span></div>
          </div>
        </div>

        {/* Schedule Impact */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider flex items-center gap-2">
            <Clock className="h-4 w-4" /> Schedule Impact
          </h3>
          <div className="text-center py-4">
            <p className={`text-3xl font-bold ${co.schedule_impact_days > 0 ? "text-amber-700" : "text-green-700"}`}>
              {co.schedule_impact_days > 0 ? `+${co.schedule_impact_days}` : "0"}
            </p>
            <p className="text-sm text-gray-500 mt-1">calendar days</p>
          </div>
          {co.submitted_to_owner_at && (
            <div className="border-t border-gray-100 pt-3 mt-3 text-sm">
              <div><span className="text-gray-500">Submitted to Owner:</span> <span className="ml-2">{new Date(co.submitted_to_owner_at).toLocaleDateString()}</span></div>
            </div>
          )}
          {co.owner_decision && (
            <div className="border-t border-gray-100 pt-3 mt-3 text-sm space-y-2">
              <div><span className="text-gray-500">Owner Decision:</span> <span className="ml-2"><StatusBadge status={co.owner_decision} /></span></div>
              {co.owner_decision_at && <div><span className="text-gray-500">Decision Date:</span> <span className="ml-2">{new Date(co.owner_decision_at).toLocaleDateString()}</span></div>}
              {co.owner_decision_notes && <div><span className="text-gray-500">Notes:</span> <span className="ml-2">{co.owner_decision_notes}</span></div>}
            </div>
          )}
        </div>
      </div>

      {/* Sub Pricings */}
      {co.sub_pricings.length > 0 && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Sub Pricing</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Subcontractor</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Amount</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Description</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Schedule Impact</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {co.sub_pricings.map((sp, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="px-4 py-3">{sp.sub_company_name || sp.sub_company_id}</td>
                    <td className="px-4 py-3 text-right font-medium">{sp.amount != null ? formatMoney(sp.amount) : "Pending"}</td>
                    <td className="px-4 py-3 text-gray-600">{sp.description || "\u2014"}</td>
                    <td className="px-4 py-3 text-right">{sp.schedule_impact_days > 0 ? `+${sp.schedule_impact_days}d` : "\u2014"}</td>
                    <td className="px-4 py-3"><StatusBadge status={sp.status} /></td>
                    <td className="px-4 py-3 text-gray-500">{sp.submitted_at ? new Date(sp.submitted_at).toLocaleDateString() : "\u2014"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
