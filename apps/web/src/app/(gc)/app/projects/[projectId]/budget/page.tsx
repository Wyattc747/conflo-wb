"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Plus, DollarSign, Upload, AlertCircle, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { formatMoney, formatPercent, toCents } from "@/lib/money";
import { useBudget, useCreateBudgetLineItem, useDeleteBudgetLineItem } from "@/hooks/use-budget";
import type { BudgetLineItem } from "@/types/budget";

function SummaryCard({ label, amount, variant }: { label: string; amount: number; variant?: "default" | "positive" | "negative" | "warning" }) {
  const colorMap = {
    default: "text-gray-900",
    positive: "text-green-700",
    negative: "text-red-700",
    warning: "text-amber-700",
  };
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-semibold mt-1 ${colorMap[variant || "default"]}`}>{formatMoney(amount)}</p>
    </div>
  );
}

function AddLineItemModal({ onClose, onSubmit, isLoading }: { onClose: () => void; onSubmit: (data: { cost_code: string; description: string; original_amount: number; notes?: string }) => void; isLoading: boolean }) {
  const [costCode, setCostCode] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = () => {
    if (!costCode.trim()) { setError("Cost code is required"); return; }
    if (!description.trim()) { setError("Description is required"); return; }
    if (!amount || parseFloat(amount) <= 0) { setError("Amount must be greater than 0"); return; }
    setError("");
    onSubmit({ cost_code: costCode.trim(), description: description.trim(), original_amount: toCents(amount), notes: notes.trim() || undefined });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg border border-gray-200 p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Add Budget Line Item</h3>
        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cost Code *</label>
            <input type="text" value={costCode} onChange={(e) => setCostCode(e.target.value)} placeholder="e.g. 03-100" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
            <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Concrete Foundations" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Original Amount ($) *</label>
            <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" step="0.01" min="0" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSubmit} disabled={isLoading} className="px-4 py-2 bg-[#1B2A4A] text-white rounded-lg text-sm font-medium hover:bg-[#243558] disabled:opacity-50 flex items-center gap-2">
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            Add Line Item
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BudgetPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [sortKey, setSortKey] = useState("cost_code");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  // Fetch token on mount
  useState(() => { getToken().then(setToken); });

  const { data: budgetData, isLoading, error } = useBudget(projectId, token);
  const createMutation = useCreateBudgetLineItem(projectId, token);
  const deleteMutation = useDeleteBudgetLineItem(projectId, token);

  const summary = budgetData?.data;
  const items = summary?.line_items || [];

  const columns: Column<BudgetLineItem>[] = [
    {
      key: "cost_code",
      label: "Cost Code",
      sortable: true,
      render: (row) => <span className="font-mono text-sm font-medium">{row.cost_code}</span>,
    },
    {
      key: "description",
      label: "Description",
      sortable: true,
      render: (row) => row.description,
    },
    {
      key: "original_amount",
      label: "Original",
      sortable: true,
      className: "text-right",
      render: (row) => <span className="text-right block">{formatMoney(row.original_amount)}</span>,
    },
    {
      key: "approved_changes",
      label: "Changes",
      className: "text-right",
      render: (row) => {
        if (row.approved_changes === 0) return <span className="text-right block text-gray-400">&mdash;</span>;
        const isPositive = row.approved_changes > 0;
        return (
          <span className={`text-right block ${isPositive ? "text-red-600" : "text-green-600"}`}>
            {isPositive ? "+" : ""}{formatMoney(row.approved_changes)}
          </span>
        );
      },
    },
    {
      key: "revised_amount",
      label: "Revised",
      sortable: true,
      className: "text-right",
      render: (row) => <span className="text-right block font-medium">{formatMoney(row.revised_amount)}</span>,
    },
    {
      key: "billed_to_date",
      label: "Billed",
      className: "text-right",
      render: (row) => <span className="text-right block">{formatMoney(row.billed_to_date)}</span>,
    },
    {
      key: "remaining",
      label: "Remaining",
      className: "text-right",
      render: (row) => {
        const variant = row.remaining < 0 ? "text-red-600 font-medium" : "";
        return <span className={`text-right block ${variant}`}>{formatMoney(row.remaining)}</span>;
      },
    },
    {
      key: "percent_complete",
      label: "% Complete",
      sortable: true,
      className: "text-right",
      render: (row) => (
        <div className="flex items-center justify-end gap-2">
          <div className="w-16 bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-[#2E75B6] h-1.5 rounded-full"
              style={{ width: `${Math.min(row.percent_complete, 100)}%` }}
            />
          </div>
          <span className="text-sm text-gray-600 w-12 text-right">{formatPercent(row.percent_complete)}</span>
        </div>
      ),
    },
  ];

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  };

  const handleAddLineItem = (data: { cost_code: string; description: string; original_amount: number; notes?: string }) => {
    createMutation.mutate(data, {
      onSuccess: () => setShowAddModal(false),
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        Failed to load budget data. Please try again.
      </div>
    );
  }

  const hasData = items.length > 0;

  return (
    <div>
      <PageHeader
        title="Budget"
        subtitle="Track project costs and budget"
        action={
          <div className="flex items-center gap-2">
            <button className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Import
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Line Item
            </button>
          </div>
        }
      />

      {hasData && summary ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
            <SummaryCard label="Original Budget" amount={summary.original_contract} />
            <SummaryCard label="Approved Changes" amount={summary.approved_changes} variant={summary.approved_changes > 0 ? "negative" : "default"} />
            <SummaryCard label="Revised Budget" amount={summary.revised_contract} />
            <SummaryCard label="Billed to Date" amount={summary.billed_to_date} />
            <SummaryCard label="Remaining" amount={summary.remaining} variant={summary.remaining < 0 ? "negative" : "positive"} />
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">% Complete</p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-lg font-semibold">{formatPercent(summary.percent_complete)}</p>
              </div>
            </div>
          </div>

          {/* Pending COs alert */}
          {summary.change_orders_pending > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0" />
              <span className="text-sm text-amber-800">
                {summary.change_orders_pending} pending change order{summary.change_orders_pending !== 1 ? "s" : ""} totaling{" "}
                <span className="font-medium">{formatMoney(summary.change_orders_pending_amount)}</span> awaiting approval
              </span>
            </div>
          )}

          {/* Budget Table */}
          <DataTable
            columns={columns}
            data={items}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={handleSort}
            page={1}
            totalPages={1}
            total={items.length}
            onPageChange={() => {}}
          />

          {/* Totals Row */}
          <div className="bg-gray-50 border border-t-0 border-gray-200 rounded-b-lg px-4 py-3 flex items-center text-sm font-semibold">
            <span className="flex-1">Totals</span>
            <span className="w-28 text-right">{formatMoney(summary.original_contract)}</span>
            <span className="w-28 text-right">{formatMoney(summary.approved_changes)}</span>
            <span className="w-28 text-right">{formatMoney(summary.revised_contract)}</span>
            <span className="w-28 text-right">{formatMoney(summary.billed_to_date)}</span>
            <span className="w-28 text-right">{formatMoney(summary.remaining)}</span>
            <span className="w-32 text-right">{formatPercent(summary.percent_complete)}</span>
          </div>
        </>
      ) : (
        <EmptyState
          icon={DollarSign}
          title="No budget items yet"
          description="Add your first budget line item to start tracking project costs."
          actionLabel="Add Line Item"
          onAction={() => setShowAddModal(true)}
        />
      )}

      {showAddModal && (
        <AddLineItemModal
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddLineItem}
          isLoading={createMutation.isPending}
        />
      )}
    </div>
  );
}
