const STATUS_STYLES: Record<string, string> = {
  // Display-format (title case) — original mappings
  "On Track": "bg-green-100 text-green-700",
  "At Risk": "bg-yellow-100 text-yellow-700",
  "Behind": "bg-red-100 text-red-700",
  "Open": "bg-blue-100 text-blue-700",
  "In Review": "bg-yellow-100 text-yellow-700",
  "Closed": "bg-gray-100 text-gray-500",
  "Approved": "bg-green-100 text-green-700",
  "Rejected": "bg-red-100 text-red-700",
  "Draft": "bg-gray-100 text-gray-600",
  "Submitted": "bg-blue-100 text-blue-700",
  "Pending": "bg-yellow-100 text-yellow-700",

  // API-format (UPPER_CASE) — Sprint 5-8
  "DRAFT": "bg-gray-100 text-gray-600",
  "SUBMITTED": "bg-blue-100 text-blue-700",
  "CLOSED": "bg-gray-100 text-gray-500",
  "APPROVED": "bg-green-100 text-green-700",
  "REJECTED": "bg-red-100 text-red-700",
  "RESPONDED": "bg-green-100 text-green-700",
  "SCHEDULED": "bg-blue-100 text-blue-700",
  "IN_PROGRESS": "bg-yellow-100 text-yellow-700",
  "COMPLETED": "bg-green-100 text-green-700",
  "CANCELLED": "bg-gray-100 text-gray-500",
  "OPEN": "bg-blue-100 text-blue-700",
  "IDENTIFIED": "bg-gray-100 text-gray-600",
  "QUOTED": "bg-blue-100 text-blue-700",
  "ORDERED": "bg-indigo-100 text-indigo-700",
  "SHIPPED": "bg-yellow-100 text-yellow-700",
  "IN_TRANSIT": "bg-yellow-100 text-yellow-700",
  "DELIVERED": "bg-green-100 text-green-700",
  "INSTALLED": "bg-emerald-100 text-emerald-700",
  "PUBLISHED": "bg-blue-100 text-blue-700",
  "AWARDED": "bg-green-100 text-green-700",
  "ACCEPTED": "bg-green-100 text-green-700",
  "FAILED": "bg-red-100 text-red-700",
  "UNDER_REVIEW": "bg-yellow-100 text-yellow-700",
  "APPROVED_AS_NOTED": "bg-green-100 text-green-700",
  "REVISE_AND_RESUBMIT": "bg-orange-100 text-orange-700",
};

function formatStatus(status: string): string {
  // Convert UPPER_CASE to Title Case for display
  if (status === status.toUpperCase() && status.includes("_")) {
    return status
      .split("_")
      .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
      .join(" ");
  }
  if (status === status.toUpperCase() && status.length > 1) {
    return status.charAt(0) + status.slice(1).toLowerCase();
  }
  return status;
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
        STATUS_STYLES[status] || "bg-gray-100 text-gray-600"
      }`}
    >
      {formatStatus(status)}
    </span>
  );
}
