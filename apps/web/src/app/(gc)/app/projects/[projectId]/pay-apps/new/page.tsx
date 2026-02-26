"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Plus, Trash2, Loader2 } from "lucide-react";
import { formatMoney, toCents } from "@/lib/money";
import { useCreatePayApp } from "@/hooks/use-pay-apps";

interface LineItemInput {
  description: string;
  scheduled_value: string;
  previous_applications: string;
  current_amount: string;
  materials_stored: string;
}

export default function NewPayAppPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useState(() => { getToken().then(setToken); });

  const createMutation = useCreatePayApp("gc", projectId, token);

  const [periodFrom, setPeriodFrom] = useState("");
  const [periodTo, setPeriodTo] = useState("");
  const [retainagePercent, setRetainagePercent] = useState("10");
  const [error, setError] = useState("");
  const [lineItems, setLineItems] = useState<LineItemInput[]>([
    { description: "", scheduled_value: "", previous_applications: "0", current_amount: "", materials_stored: "0" },
  ]);

  const addLineItem = () => {
    setLineItems([...lineItems, { description: "", scheduled_value: "", previous_applications: "0", current_amount: "", materials_stored: "0" }]);
  };

  const removeLineItem = (index: number) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const updateLineItem = (index: number, field: keyof LineItemInput, value: string) => {
    const updated = [...lineItems];
    updated[index] = { ...updated[index], [field]: value };
    setLineItems(updated);
  };

  const totalScheduled = lineItems.reduce((sum, li) => sum + toCents(li.scheduled_value || "0"), 0);
  const totalCurrent = lineItems.reduce((sum, li) => sum + toCents(li.current_amount || "0"), 0);

  const handleSubmit = () => {
    if (!periodFrom) { setError("Period from date is required"); return; }
    if (!periodTo) { setError("Period to date is required"); return; }
    if (periodFrom > periodTo) { setError("Period from must be before period to"); return; }

    const validLines = lineItems.filter((li) => li.description.trim() && li.scheduled_value);
    if (validLines.length === 0) { setError("At least one line item is required"); return; }
    setError("");

    createMutation.mutate(
      {
        pay_app_type: "GC_TO_OWNER",
        period_from: periodFrom,
        period_to: periodTo,
        retainage_percent: parseFloat(retainagePercent) || 10,
        line_items: validLines.map((li) => ({
          description: li.description.trim(),
          scheduled_value: toCents(li.scheduled_value),
          previous_applications: toCents(li.previous_applications || "0"),
          current_amount: toCents(li.current_amount || "0"),
          materials_stored: toCents(li.materials_stored || "0"),
        })),
      },
      {
        onSuccess: (data) => {
          const paId = data?.data?.id;
          router.push(paId
            ? `/app/projects/${projectId}/pay-apps/${paId}`
            : `/app/projects/${projectId}/pay-apps`
          );
        },
        onError: () => {
          setError("Failed to create pay application. Please try again.");
        },
      }
    );
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push(`/app/projects/${projectId}/pay-apps`)} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-semibold">New Pay Application</h1>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        {error && <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period From *</label>
            <input type="date" value={periodFrom} onChange={(e) => setPeriodFrom(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period To *</label>
            <input type="date" value={periodTo} onChange={(e) => setPeriodTo(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Retainage %</label>
            <input type="number" value={retainagePercent} onChange={(e) => setRetainagePercent(e.target.value)} min="0" max="100" step="0.5" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Schedule of Values (G703)</h3>
            <button onClick={addLineItem} className="text-sm text-[#2E75B6] hover:text-[#1B2A4A] flex items-center gap-1">
              <Plus className="h-3 w-3" /> Add Line
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-3 py-2 font-medium text-gray-600">Description</th>
                  <th className="text-right px-3 py-2 font-medium text-gray-600">Scheduled Value ($)</th>
                  <th className="text-right px-3 py-2 font-medium text-gray-600">Previous ($)</th>
                  <th className="text-right px-3 py-2 font-medium text-gray-600">This Period ($)</th>
                  <th className="text-right px-3 py-2 font-medium text-gray-600">Materials ($)</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {lineItems.map((li, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="px-3 py-2"><input type="text" value={li.description} onChange={(e) => updateLineItem(i, "description", e.target.value)} placeholder="Line item description" className="w-full border border-gray-300 rounded px-2 py-1 text-sm" /></td>
                    <td className="px-3 py-2"><input type="number" value={li.scheduled_value} onChange={(e) => updateLineItem(i, "scheduled_value", e.target.value)} placeholder="0.00" step="0.01" className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-right" /></td>
                    <td className="px-3 py-2"><input type="number" value={li.previous_applications} onChange={(e) => updateLineItem(i, "previous_applications", e.target.value)} placeholder="0.00" step="0.01" className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-right" /></td>
                    <td className="px-3 py-2"><input type="number" value={li.current_amount} onChange={(e) => updateLineItem(i, "current_amount", e.target.value)} placeholder="0.00" step="0.01" className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-right" /></td>
                    <td className="px-3 py-2"><input type="number" value={li.materials_stored} onChange={(e) => updateLineItem(i, "materials_stored", e.target.value)} placeholder="0.00" step="0.01" className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-right" /></td>
                    <td className="px-3 py-2">
                      {lineItems.length > 1 && (
                        <button onClick={() => removeLineItem(i)} className="text-gray-400 hover:text-red-500"><Trash2 className="h-4 w-4" /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between mt-3 px-3 text-sm text-gray-600">
            <span>Total Scheduled: <span className="font-medium">{formatMoney(totalScheduled)}</span></span>
            <span>This Period: <span className="font-medium">{formatMoney(totalCurrent)}</span></span>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button onClick={() => router.push(`/app/projects/${projectId}/pay-apps`)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={createMutation.isPending} className="px-4 py-2 bg-[#1B2A4A] text-white rounded-lg text-sm font-medium hover:bg-[#243558] disabled:opacity-50 flex items-center gap-2">
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Create Pay App
          </button>
        </div>
      </div>
    </div>
  );
}
