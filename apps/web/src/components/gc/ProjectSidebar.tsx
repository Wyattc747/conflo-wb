"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Users,
  FileText,
  ClipboardList,
  Users2,
  HelpCircle,
  BookOpen,
  Send,
  Wrench,
  CheckSquare,
  Package,
  PenTool,
  Calendar,
  Settings,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useProjectSidebarStore } from "@/stores/ui-store";

interface ProjectSidebarProps {
  projectId: string;
  projectName: string;
  visibleTools: string[];
}

const SIDEBAR_ITEMS = [
  { key: "overview", label: "Overview", icon: Home, href: "" },
  { key: "directory", label: "Directory", icon: Users, href: "/directory" },
  { key: "documents", label: "Documents", icon: FileText, href: "/documents" },
  { key: "daily_logs", label: "Daily Logs", icon: ClipboardList, href: "/daily-logs" },
  { key: "meetings", label: "Meetings", icon: Users2, href: "/meetings" },
  { key: "rfis", label: "RFIs", icon: HelpCircle, href: "/rfis" },
  { key: "submittals", label: "Submittals", icon: BookOpen, href: "/submittals" },
  { key: "transmittals", label: "Transmittals", icon: Send, href: "/transmittals" },
  { key: "punch_list", label: "Punch List", icon: Wrench, href: "/punch-list" },
  { key: "todo", label: "Tasks", icon: CheckSquare, href: "/todo" },
  { key: "procurement", label: "Procurement", icon: Package, href: "/procurement" },
  { key: "drawings", label: "Drawings", icon: PenTool, href: "/drawings" },
  { key: "schedule", label: "Schedule", icon: Calendar, href: "/schedule" },
  { key: "settings", label: "Settings", icon: Settings, href: "/settings" },
];

const ALWAYS_VISIBLE = ["overview", "directory", "settings"];

export function ProjectSidebar({ projectId, projectName, visibleTools }: ProjectSidebarProps) {
  const pathname = usePathname();
  const { collapsed, toggle } = useProjectSidebarStore();
  const basePath = `/app/projects/${projectId}`;

  const filteredItems = SIDEBAR_ITEMS.filter(
    (item) => ALWAYS_VISIBLE.includes(item.key) || visibleTools.includes(item.key)
  );

  if (collapsed) {
    return (
      <aside className="hidden md:flex w-10 bg-white border-r border-gray-200 fixed left-0 top-14 bottom-0 z-40 flex-col items-center pt-3">
        <button onClick={toggle} className="p-1 hover:bg-gray-100 rounded mb-3">
          <ChevronsRight className="h-4 w-4 text-gray-400" />
        </button>
        {filteredItems.map((item) => {
          const fullHref = `${basePath}${item.href}`;
          const isActive =
            item.href === ""
              ? pathname === basePath || pathname === `${basePath}/`
              : pathname.startsWith(fullHref);
          const Icon = item.icon;
          return (
            <Link
              key={item.key}
              href={fullHref}
              title={item.label}
              className={`p-2 rounded mb-0.5 ${
                isActive ? "text-yellow-500" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <Icon className="h-4 w-4" />
            </Link>
          );
        })}
      </aside>
    );
  }

  return (
    <aside className="hidden md:block w-[180px] bg-white border-r border-gray-200 fixed left-0 top-14 bottom-0 z-40 overflow-y-auto">
      {/* Project name + collapse */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-gray-100">
        <span className="text-xs font-medium text-gray-700 truncate">{projectName}</span>
        <button onClick={toggle} className="p-0.5 hover:bg-gray-100 rounded flex-shrink-0">
          <ChevronsLeft className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Nav items */}
      <nav className="py-1">
        {filteredItems.map((item) => {
          const fullHref = `${basePath}${item.href}`;
          const isActive =
            item.href === ""
              ? pathname === basePath || pathname === `${basePath}/`
              : pathname.startsWith(fullHref);
          const Icon = item.icon;

          return (
            <Link
              key={item.key}
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
