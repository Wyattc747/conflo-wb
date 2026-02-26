"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Receipt, FileText, Wrench, MoreHorizontal } from "lucide-react";

interface OwnerMobileBottomTabsProps {
  projectId: string;
}

const TABS = [
  { label: "Pay Apps", icon: Receipt, href: "/pay-apps" },
  { label: "COs", icon: FileText, href: "/change-orders" },
  { label: "Punch", icon: Wrench, href: "/punch-list" },
];

export function OwnerMobileBottomTabs({ projectId }: OwnerMobileBottomTabsProps) {
  const pathname = usePathname();
  const basePath = `/owner/projects/${projectId}`;

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
      <nav className="flex items-center justify-around h-14">
        {TABS.map((tab) => {
          const fullHref = `${basePath}${tab.href}`;
          const isActive = pathname.startsWith(fullHref);
          const Icon = tab.icon;
          return (
            <Link
              key={tab.href}
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
