"use client";

interface StatusAction {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}

interface StatusActionsProps {
  actions: StatusAction[];
}

const VARIANT_STYLES: Record<string, string> = {
  primary: "bg-[#1B2A4A] text-white hover:bg-[#243558]",
  secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

export function StatusActions({ actions }: StatusActionsProps) {
  return (
    <div className="flex items-center gap-2">
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={action.onClick}
          disabled={action.disabled}
          className={`px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed ${
            VARIANT_STYLES[action.variant || "secondary"]
          }`}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
