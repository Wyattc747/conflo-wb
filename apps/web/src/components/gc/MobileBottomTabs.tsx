"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ClipboardList, HelpCircle, Wrench, Camera, MoreHorizontal } from "lucide-react";
import { useMobileMoreSheetStore } from "@/stores/ui-store";
import { MobileMoreSheet } from "@/components/gc/MobileMoreSheet";

interface MobileBottomTabsProps {
  projectId: string;
}

const TABS = [
  { label: "Daily Logs", icon: ClipboardList, href: "/daily-logs" },
  { label: "RFIs", icon: HelpCircle, href: "/rfis" },
  { label: "Punch", icon: Wrench, href: "/punch-list" },
  { label: "Camera", icon: Camera, href: "/photos" },
];

export function MobileBottomTabs({ projectId }: MobileBottomTabsProps) {
  const pathname = usePathname();
  const basePath = `/app/projects/${projectId}`;
  const { setOpen } = useMobileMoreSheetStore();

  return (
    <>
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
          <button
            onClick={() => setOpen(true)}
            className="flex flex-col items-center gap-0.5 px-2 py-1 text-gray-500"
          >
            <MoreHorizontal className="h-5 w-5" />
            <span className="text-[10px] font-medium">More</span>
          </button>
        </nav>
      </div>
      <MobileMoreSheet projectId={projectId} />
    </>
  );
}
