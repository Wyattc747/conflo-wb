const PHASE_STYLES: Record<string, string> = {
  BIDDING: "bg-purple-100 text-purple-700 border-purple-200",
  BUYOUT: "bg-blue-100 text-blue-700 border-blue-200",
  ACTIVE: "bg-green-100 text-green-700 border-green-200",
  CLOSEOUT: "bg-amber-100 text-amber-700 border-amber-200",
  CLOSED: "bg-gray-100 text-gray-500 border-gray-200",
};

export function PhaseBadge({ phase }: { phase: string }) {
  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-medium border ${
        PHASE_STYLES[phase] || PHASE_STYLES.ACTIVE
      }`}
    >
      {phase.charAt(0) + phase.slice(1).toLowerCase()}
    </span>
  );
}
