"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, ShoppingCart, AlertTriangle, Truck } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ViewToggle } from "@/components/shared/ViewToggle";
import { KanbanBoard } from "@/components/shared/KanbanBoard";
import { ProgressBar } from "@/components/shared/ProgressBar";
import type { ProcurementItem } from "@/types/procurement";

const STATUS_ORDER = ["IDENTIFIED", "QUOTED", "ORDERED", "SHIPPED", "DELIVERED", "INSTALLED"];

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0 }).format(cents / 100);
}

const MOCK_PROCUREMENT: ProcurementItem[] = [
  {
    id: "1",
    project_id: "p1",
    item_name: "Structural Steel W-Shapes",
    description: "W14x30 and W12x26 beams for levels 2-4.",
    status: "ORDERED",
    category: "METALS",
    spec_section: "05 12 00",
    quantity: 150,
    unit: "tons",
    vendor: "Nucor Steel",
    vendor_contact: "Tom Williams",
    vendor_phone: "555-0101",
    vendor_email: "tom@nucor.example.com",
    estimated_cost_cents: 52500000,
    actual_cost_cents: 51000000,
    po_number: "PO-2026-0042",
    lead_time_days: 45,
    required_on_site_date: "2026-04-15",
    order_by_date: "2026-02-28",
    expected_delivery_date: "2026-04-10",
    actual_delivery_date: null,
    tracking_number: "TRK-998877",
    is_at_risk: false,
    assigned_to: "u2",
    sub_company_id: null,
    linked_schedule_task_id: null,
    notes: "Mill cert required.",
    created_by: "u1",
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    item_name: "RTU HVAC Units (x4)",
    description: "Carrier 50XC rooftop units, 25-ton each.",
    status: "QUOTED",
    category: "MECHANICAL",
    spec_section: "23 74 00",
    quantity: 4,
    unit: "each",
    vendor: "Carrier Commercial",
    vendor_contact: null,
    vendor_phone: null,
    vendor_email: null,
    estimated_cost_cents: 28000000,
    actual_cost_cents: 0,
    po_number: null,
    lead_time_days: 90,
    required_on_site_date: "2026-06-01",
    order_by_date: "2026-03-01",
    expected_delivery_date: null,
    actual_delivery_date: null,
    tracking_number: null,
    is_at_risk: true,
    assigned_to: "u3",
    sub_company_id: null,
    linked_schedule_task_id: null,
    notes: "Long lead item - order ASAP.",
    created_by: "u1",
    created_at: "2026-02-05T09:00:00Z",
    updated_at: "2026-02-15T14:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    item_name: "Electrical Switchgear",
    description: "Main 4000A switchboard and distribution panels.",
    status: "IDENTIFIED",
    category: "ELECTRICAL",
    spec_section: "26 24 00",
    quantity: 1,
    unit: "lot",
    vendor: null,
    vendor_contact: null,
    vendor_phone: null,
    vendor_email: null,
    estimated_cost_cents: 18500000,
    actual_cost_cents: 0,
    po_number: null,
    lead_time_days: 120,
    required_on_site_date: "2026-07-01",
    order_by_date: "2026-03-01",
    expected_delivery_date: null,
    actual_delivery_date: null,
    tracking_number: null,
    is_at_risk: true,
    assigned_to: null,
    sub_company_id: null,
    linked_schedule_task_id: null,
    notes: "Need to get quotes from 3 vendors.",
    created_by: "u1",
    created_at: "2026-02-10T11:00:00Z",
    updated_at: "2026-02-10T11:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    item_name: "Exterior Brick - Heritage Blend",
    description: "Face brick for exterior cladding.",
    status: "DELIVERED",
    category: "MASONRY",
    spec_section: "04 21 00",
    quantity: 45000,
    unit: "units",
    vendor: "Boral Bricks",
    vendor_contact: "Lisa Park",
    vendor_phone: "555-0202",
    vendor_email: "lisa@boral.example.com",
    estimated_cost_cents: 6750000,
    actual_cost_cents: 6500000,
    po_number: "PO-2026-0031",
    lead_time_days: 30,
    required_on_site_date: "2026-03-01",
    order_by_date: "2026-01-30",
    expected_delivery_date: "2026-02-25",
    actual_delivery_date: "2026-02-24",
    tracking_number: null,
    is_at_risk: false,
    assigned_to: "u2",
    sub_company_id: null,
    linked_schedule_task_id: null,
    notes: null,
    created_by: "u1",
    created_at: "2026-01-15T08:00:00Z",
    updated_at: "2026-02-24T10:00:00Z",
  },
];

const KANBAN_COLUMNS = [
  { id: "IDENTIFIED", title: "Identified", color: "bg-gray-400" },
  { id: "QUOTED", title: "Quoted", color: "bg-blue-400" },
  { id: "ORDERED", title: "Ordered", color: "bg-indigo-400" },
  { id: "SHIPPED", title: "Shipped", color: "bg-yellow-400" },
  { id: "DELIVERED", title: "Delivered", color: "bg-green-400" },
  { id: "INSTALLED", title: "Installed", color: "bg-emerald-400" },
];

export default function ProcurementPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [view, setView] = useState<"table" | "board">("table");
  const [sortKey, setSortKey] = useState("item_name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_PROCUREMENT;
  if (statusFilter) filtered = filtered.filter((p) => p.status === statusFilter);
  if (categoryFilter) filtered = filtered.filter((p) => p.category === categoryFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.item_name.toLowerCase().includes(s) ||
        (p.vendor && p.vendor.toLowerCase().includes(s)) ||
        (p.po_number && p.po_number.toLowerCase().includes(s))
    );
  }

  const columns: Column<ProcurementItem>[] = [
    {
      key: "item_name",
      label: "Item",
      sortable: true,
      className: "max-w-xs",
      render: (row) => (
        <div>
          <div className="flex items-center gap-1.5">
            {row.is_at_risk && <AlertTriangle className="h-3.5 w-3.5 text-red-500 flex-shrink-0" />}
            <span className="font-medium truncate block max-w-xs">{row.item_name}</span>
          </div>
          {row.category && <span className="text-xs text-gray-500">{row.category}</span>}
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "vendor",
      label: "Vendor",
      render: (row) => row.vendor || "\u2014",
    },
    {
      key: "estimated_cost_cents",
      label: "Est. Cost",
      sortable: true,
      render: (row) => formatMoney(row.estimated_cost_cents),
    },
    {
      key: "po_number",
      label: "PO #",
      render: (row) => row.po_number ? (
        <span className="font-mono text-sm">{row.po_number}</span>
      ) : "\u2014",
    },
    {
      key: "lead_time_days",
      label: "Lead Time",
      render: (row) => row.lead_time_days ? `${row.lead_time_days}d` : "\u2014",
    },
    {
      key: "required_on_site_date",
      label: "Required By",
      sortable: true,
      render: (row) => {
        if (!row.required_on_site_date) return "\u2014";
        const d = new Date(row.required_on_site_date + "T00:00:00");
        const isOverdue = !["DELIVERED", "INSTALLED"].includes(row.status) && d < new Date();
        return <span className={isOverdue ? "text-red-600 font-medium" : ""}>{d.toLocaleDateString()}</span>;
      },
    },
    {
      key: "progress",
      label: "Progress",
      className: "w-28",
      render: (row) => {
        const idx = STATUS_ORDER.indexOf(row.status);
        const pct = idx >= 0 ? Math.round(((idx + 1) / STATUS_ORDER.length) * 100) : 0;
        return <ProgressBar value={pct} />;
      },
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

  const hasData = MOCK_PROCUREMENT.length > 0;
  const atRiskCount = MOCK_PROCUREMENT.filter((p) => p.is_at_risk).length;

  const kanbanColumns = KANBAN_COLUMNS.map((col) => ({
    ...col,
    items: filtered.filter((p) => p.status === col.id),
  }));

  return (
    <div>
      <PageHeader
        title="Procurement"
        subtitle="Track material orders and deliveries"
        action={
          <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
            {hasData && <ViewToggle view={view} onViewChange={setView} />}
            <button
              onClick={() => router.push(`/app/projects/${projectId}/procurement/new`)}
              className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 flex-1 sm:flex-none justify-center"
            >
              <Plus className="h-4 w-4" />
              New Item
            </button>
          </div>
        }
      />

      {hasData && (
        <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4 sm:mb-5">
          <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
            <div className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wide">Total Items</div>
            <div className="text-lg sm:text-2xl font-bold text-gray-900 mt-1">{MOCK_PROCUREMENT.length}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
            <div className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wide">At Risk</div>
            <div className="text-lg sm:text-2xl font-bold text-red-600 mt-1">{atRiskCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
            <div className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wide">Total Est. Value</div>
            <div className="text-lg sm:text-2xl font-bold text-gray-900 mt-1">
              {formatMoney(MOCK_PROCUREMENT.reduce((sum, p) => sum + p.estimated_cost_cents, 0))}
            </div>
          </div>
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search procurement..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: STATUS_ORDER.map((s) => ({ label: s.charAt(0) + s.slice(1).toLowerCase(), value: s })),
              },
              {
                key: "category",
                label: "All Categories",
                value: categoryFilter,
                onChange: setCategoryFilter,
                options: [
                  { label: "Metals", value: "METALS" },
                  { label: "Mechanical", value: "MECHANICAL" },
                  { label: "Electrical", value: "ELECTRICAL" },
                  { label: "Masonry", value: "MASONRY" },
                  { label: "Concrete", value: "CONCRETE" },
                ],
              },
            ]}
          />

          {view === "table" ? (
            <DataTable
              columns={columns}
              data={filtered}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSort={handleSort}
              onRowClick={(row) => router.push(`/app/projects/${projectId}/procurement/${row.id}`)}
              page={page}
              totalPages={1}
              total={filtered.length}
              onPageChange={setPage}
            />
          ) : (
            <KanbanBoard
              columns={kanbanColumns}
              getItemId={(item) => item.id}
              renderCard={(item) => (
                <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-1.5">
                    {item.is_at_risk && <AlertTriangle className="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />}
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{item.item_name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{item.vendor || "No vendor"}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">{formatMoney(item.estimated_cost_cents)}</span>
                    {item.required_on_site_date && (
                      <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                        <Truck className="h-2.5 w-2.5" />
                        {new Date(item.required_on_site_date + "T00:00:00").toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              )}
            />
          )}
        </>
      ) : (
        <EmptyState
          icon={ShoppingCart}
          title="No procurement items yet"
          description="Add your first procurement item to start tracking orders and deliveries."
          actionLabel="Add Item"
          onAction={() => router.push(`/app/projects/${projectId}/procurement/new`)}
        />
      )}
    </div>
  );
}
