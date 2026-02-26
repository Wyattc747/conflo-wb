"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface OwnerProjectTabsProps {
  projectId: string;
  visibleTools: string[];
}

const OWNER_TOOLS = [
  { key: "pay_apps", label: "Pay Apps", href: "/pay-apps" },
  { key: "change_orders", label: "Change Orders", href: "/change-orders" },
  { key: "schedule", label: "Schedule", href: "/schedule" },
  { key: "punch_list", label: "Punch List", href: "/punch-list" },
  { key: "submittals", label: "Submittals", href: "/submittals" },
  { key: "rfis", label: "RFIs", href: "/rfis" },
  { key: "drawings", label: "Drawings", href: "/drawings" },
  { key: "closeout", label: "Closeout", href: "/closeout" },
  { key: "directory", label: "Directory", href: "/directory" },
];

// Pay Apps and Change Orders are always visible for owners
const ALWAYS_VISIBLE = ["pay_apps", "change_orders"];

export function OwnerProjectTabs({ projectId, visibleTools }: OwnerProjectTabsProps) {
  const pathname = usePathname();
  const basePath = `/owner/projects/${projectId}`;

  const filteredTools = OWNER_TOOLS.filter(
    (t) => ALWAYS_VISIBLE.includes(t.key) || visibleTools.includes(t.key)
  );

  return (
    <div className="bg-white border-b border-gray-200 px-6">
      <nav className="flex gap-1 overflow-x-auto">
        {/* Overview tab */}
        <Link
          href={basePath}
          className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
            pathname === basePath
              ? "border-yellow-500 text-yellow-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          Overview
        </Link>
        {filteredTools.map((tool) => {
          const fullHref = `${basePath}${tool.href}`;
          const isActive = pathname.startsWith(fullHref);
          return (
            <Link
              key={tool.key}
              href={fullHref}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                isActive
                  ? "border-yellow-500 text-yellow-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tool.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
