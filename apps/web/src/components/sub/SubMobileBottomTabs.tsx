"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Receipt, HelpCircle, Wrench, Gavel, MoreHorizontal } from "lucide-react";

interface SubMobileBottomTabsProps {
  projectId: string;
}

const TABS = [
  { label: "Pay Apps", icon: Receipt, href: "/financials" },
  { label: "RFIs", icon: HelpCircle, href: "/rfis" },
  { label: "Punch", icon: Wrench, href: "/punch-list" },
  { label: "Bids", icon: Gavel, href: "/bids" },
];

export function SubMobileBottomTabs({ projectId }: SubMobileBottomTabsProps) {
  const pathname = usePathname();
  const basePath = `/sub/projects/${projectId}`;

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
      <nav className="flex items-center justify-around h-14">
        {TABS.map((tab) => {
          // Some tabs link to project-level, others to global
          const isProjectTab = ["/rfis", "/punch-list"].includes(tab.href);
          const fullHref = isProjectTab ? `${basePath}${tab.href}` : `/sub${tab.href}`;
          const isActive = pathname.startsWith(fullHref);
          const Icon = tab.icon;
          return (
            <Link
              key={tab.label}
              href={fullHref}
              className={`flex flex-col items-center gap-0.5 px-2 py-1 ${
                isActive ? "text-yellow-500" : "text-gray-500"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium">{tab.label}</span>
            </Link>
          );
        })}
        <Link
          href={basePath}
          className="flex flex-col items-center gap-0.5 px-2 py-1 text-gray-500"
        >
          <MoreHorizontal className="h-5 w-5" />
          <span className="text-[10px] font-medium">More</span>
        </Link>
      </nav>
    </div>
  );
}
