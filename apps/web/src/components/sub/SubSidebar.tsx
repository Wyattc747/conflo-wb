"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, FolderOpen, Gavel, DollarSign,
  Building2, HelpCircle, ArrowLeft, Home,
  BookOpen, Wrench, PenTool, Calendar, Archive,
} from "lucide-react";

interface SubSidebarProps {
  projectId?: string;
}

const MAIN_NAV = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/sub/dashboard" },
  { label: "Projects", icon: FolderOpen, href: "/sub/projects" },
  { label: "Bids", icon: Gavel, href: "/sub/bids" },
  { label: "Financials", icon: DollarSign, href: "/sub/financials" },
  { label: "Company", icon: Building2, href: "/sub/company" },
  { label: "Help", icon: HelpCircle, href: "/sub/help" },
];

const PROJECT_NAV = [
  { label: "Overview", icon: Home, href: "" },
  { label: "RFIs", icon: HelpCircle, href: "/rfis" },
  { label: "Submittals", icon: BookOpen, href: "/submittals" },
  { label: "Punch List", icon: Wrench, href: "/punch-list" },
  { label: "Drawings", icon: PenTool, href: "/drawings" },
  { label: "Schedule", icon: Calendar, href: "/schedule" },
  { label: "Closeout", icon: Archive, href: "/closeout" },
];

export function SubSidebar({ projectId }: SubSidebarProps) {
  const pathname = usePathname();

  if (projectId) {
    const basePath = `/sub/projects/${projectId}`;
    return (
      <aside className="hidden md:block w-[180px] bg-white border-r border-gray-200 fixed left-0 top-14 bottom-0 z-40 overflow-y-auto">
        {/* Back link */}
        <Link
          href="/sub/projects"
          className="flex items-center gap-2 px-3 py-3 text-xs text-gray-500 hover:text-gray-700 border-b border-gray-100"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to Projects
        </Link>

        <nav className="py-1">
          {PROJECT_NAV.map((item) => {
            const fullHref = `${basePath}${item.href}`;
            const isActive =
              item.href === ""
                ? pathname === basePath || pathname === `${basePath}/`
                : pathname.startsWith(fullHref);
            const Icon = item.icon;

            return (
              <Link
                key={item.label}
                href={fullHref}
                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "text-yellow-500 bg-yellow-50"
                    : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <Icon
                  className={`h-4 w-4 flex-shrink-0 ${
                    isActive ? "text-yellow-500" : "text-gray-400"
                  }`}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    );
  }

  return (
    <aside className="hidden md:block w-[180px] bg-white border-r border-gray-200 fixed left-0 top-14 bottom-0 z-40">
      <nav className="py-2">
        {MAIN_NAV.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "text-yellow-500 bg-yellow-50"
                  : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon
                className={`h-4 w-4 flex-shrink-0 ${
                  isActive ? "text-yellow-500" : "text-gray-400"
                }`}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
