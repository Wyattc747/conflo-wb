"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Send, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatMoney, formatPercent } from "@/lib/money";
import { usePayApp, useSubmitPayApp, useApprovePayApp, useRejectPayApp } from "@/hooks/use-pay-apps";

function G702Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100">
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`text-sm ${bold ? "font-semibold text-gray-900" : "text-gray-900"}`}>{value}</span>
    </div>
  );
}

export default function PayAppDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const payAppId = params.payAppId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useState(() => { getToken().then(setToken); });

  const { data, isLoading, error } = usePayApp("gc", projectId, payAppId, token);
  const submitMutation = useSubmitPayApp("gc", projectId, payAppId, token);
  const approveMutation = useApprovePayApp("gc", projectId, payAppId, token);
  const rejectMutation = useRejectPayApp("gc", projectId, payAppId, token);

  const pa = data?.data;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !pa) {
    return (
      <div>
        <button onClick={() => router.push(`/app/projects/${projectId}/pay-apps`)} className="text-gray-400 hover:text-gray-600 mb-4 flex items-center gap-2">
          <ArrowLeft className="h-5 w-5" /> Back to Pay Apps
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          Pay application not found or failed to load.
        </div>
      </div>
    );
  }

  const handleSubmit = () => {
    if (confirm("Submit this pay application?")) {
      submitMutation.mutate();
    }
  };

  const handleApprove = () => {
    if (confirm("Approve this pay application?")) {
      approveMutation.mutate(undefined);
    }
  };

  const handleReject = () => {
    const reason = prompt("Rejection reason (optional):");
    rejectMutation.mutate(reason || undefined);
  };

  const isActioning = submitMutation.isPending || approveMutation.isPending || rejectMutation.isPending;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push(`/app/projects/${projectId}/pay-apps`)} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3 flex-1">
          <span className="text-lg font-semibold">Pay App {pa.formatted_number}</span>
          <StatusBadge status={pa.status} />
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
            pa.pay_app_type === "GC_TO_OWNER" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"
          }`}>
            {pa.pay_app_type === "GC_TO_OWNER" ? "GC \u2192 Owner" : "Sub \u2192 GC"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {pa.status === "DRAFT" && (
            <button onClick={handleSubmit} disabled={isActioning} className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] disabled:opacity-50 flex items-center gap-2">
              {submitMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Submit
            </button>
          )}
          {pa.status === "SUBMITTED" && pa.pay_app_type === "SUB_TO_GC" && (
            <>
              <button onClick={handleApprove} disabled={isActioning} className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center gap-2">
                {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                Approve
              </button>
              <button onClick={handleReject} disabled={isActioning} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2">
                {rejectMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
                Reject
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* G702 Summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider">G702 Summary</h3>
          <G702Row label="1. Original Contract Sum" value={formatMoney(pa.original_contract_sum)} />
          <G702Row label="2. Net Change Orders" value={formatMoney(pa.net_change_orders)} />
          <G702Row label="3. Contract Sum to Date" value={formatMoney(pa.contract_sum_to_date)} bold />
          <G702Row label="4. Total Completed & Stored" value={formatMoney(pa.total_completed_and_stored)} />
          <G702Row label={`5. Retainage (${pa.retainage_percent}%)`} value={formatMoney(pa.retainage_amount)} />
          <G702Row label="6. Total Earned Less Retainage" value={formatMoney(pa.total_earned_less_retainage)} />
          <G702Row label="7. Less Previous Certificates" value={formatMoney(pa.previous_certificates)} />
          <div className="flex justify-between py-3 mt-1 bg-blue-50 -mx-5 px-5 rounded-b-lg">
            <span className="text-sm font-semibold text-[#1B2A4A]">8. Current Payment Due</span>
            <span className="text-lg font-bold text-[#1B2A4A]">{formatMoney(pa.current_payment_due)}</span>
          </div>
        </div>

        {/* Metadata */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider">Details</h3>
          <div className="space-y-3 text-sm">
            <div><span className="text-gray-500">Period:</span> <span className="ml-2">{new Date(pa.period_from + "T00:00:00").toLocaleDateString()} \u2013 {new Date(pa.period_to + "T00:00:00").toLocaleDateString()}</span></div>
            <div><span className="text-gray-500">Balance to Finish:</span> <span className="ml-2 font-medium">{formatMoney(pa.balance_to_finish)}</span></div>
            {pa.sub_company_name && <div><span className="text-gray-500">Subcontractor:</span> <span className="ml-2">{pa.sub_company_name}</span></div>}
            {pa.submitted_by_name && <div><span className="text-gray-500">Submitted By:</span> <span className="ml-2">{pa.submitted_by_name}</span></div>}
            {pa.submitted_at && <div><span className="text-gray-500">Submitted:</span> <span className="ml-2">{new Date(pa.submitted_at).toLocaleDateString()}</span></div>}
            {pa.reviewed_by_name && <div><span className="text-gray-500">Reviewed By:</span> <span className="ml-2">{pa.reviewed_by_name}</span></div>}
            {pa.reviewed_at && <div><span className="text-gray-500">Reviewed:</span> <span className="ml-2">{new Date(pa.reviewed_at).toLocaleDateString()}</span></div>}
            {pa.review_notes && <div><span className="text-gray-500">Notes:</span> <span className="ml-2">{pa.review_notes}</span></div>}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider">Progress</h3>
          <div className="space-y-4">
            {pa.line_items.slice(0, 4).map((li, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 truncate mr-2">{li.description}</span>
                  <span className="text-gray-900 font-medium">{formatPercent(li.percent_complete)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div className="bg-[#2E75B6] h-1.5 rounded-full" style={{ width: `${Math.min(li.percent_complete, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* G703 Schedule of Values */}
      {pa.line_items.length > 0 && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">G703 -- Schedule of Values</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Item</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Description</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Scheduled Value</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Previous</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">This Period</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Materials</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Total Completed</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">%</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Balance</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">Retainage</th>
                </tr>
              </thead>
              <tbody>
                {pa.line_items.map((li, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-gray-500">{li.cost_code || (i + 1)}</td>
                    <td className="px-4 py-2">{li.description}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.scheduled_value)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.previous_applications)}</td>
                    <td className="px-4 py-2 text-right font-medium">{formatMoney(li.current_amount)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.materials_stored)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.total_completed)}</td>
                    <td className="px-4 py-2 text-right">{formatPercent(li.percent_complete)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.balance_to_finish)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(li.retainage)}</td>
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
