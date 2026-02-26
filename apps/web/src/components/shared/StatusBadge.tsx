const STATUS_STYLES: Record<string, string> = {
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
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
        STATUS_STYLES[status] || "bg-gray-100 text-gray-600"
      }`}
    >
      {status}
    </span>
  );
}
