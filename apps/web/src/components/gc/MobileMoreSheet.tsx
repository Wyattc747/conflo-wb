"use client";

import Link from "next/link";
import {
  Home, Users, FileText, Users2, BookOpen, Send,
  CheckSquare, Package, PenTool, Calendar, Settings,
  DollarSign, Receipt, ClipboardCheck, FolderOpen,
  Eye, Archive, X,
} from "lucide-react";
import { useMobileMoreSheetStore } from "@/stores/ui-store";

interface MobileMoreSheetProps {
  projectId: string;
}

const MORE_ITEMS = [
  { label: "Overview", icon: Home, href: "" },
  { label: "Directory", icon: Users, href: "/directory" },
  { label: "Documents", icon: FolderOpen, href: "/documents" },
  { label: "Meetings", icon: Users2, href: "/meetings" },
  { label: "Submittals", icon: BookOpen, href: "/submittals" },
  { label: "Transmittals", icon: Send, href: "/transmittals" },
  { label: "Tasks", icon: CheckSquare, href: "/todo" },
  { label: "Procurement", icon: Package, href: "/procurement" },
  { label: "Drawings", icon: PenTool, href: "/drawings" },
  { label: "Schedule", icon: Calendar, href: "/schedule" },
  { label: "Change Orders", icon: FileText, href: "/change-orders" },
  { label: "Budget", icon: DollarSign, href: "/budget" },
  { label: "Pay Apps", icon: Receipt, href: "/pay-apps" },
  { label: "Inspections", icon: ClipboardCheck, href: "/inspections" },
  { label: "Bid Packages", icon: Package, href: "/bid-packages" },
  { label: "Look Ahead", icon: Eye, href: "/look-ahead" },
  { label: "Closeout", icon: Archive, href: "/closeout" },
  { label: "Settings", icon: Settings, href: "/settings" },
];

export function MobileMoreSheet({ projectId }: MobileMoreSheetProps) {
  const { open, setOpen } = useMobileMoreSheetStore();
  const basePath = `/app/projects/${projectId}`;

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] md:hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />

      {/* Sheet */}
      <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl max-h-[70vh] overflow-y-auto">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <span className="text-sm font-semibold text-gray-900">All Tools</span>
          <button onClick={() => setOpen(false)} className="p-1 hover:bg-gray-100 rounded">
            <X className="h-4 w-4 text-gray-500" />
          </button>
        </div>
        <div className="grid grid-cols-4 gap-1 p-3">
          {MORE_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={`${basePath}${item.href}`}
                onClick={() => setOpen(false)}
                className="flex flex-col items-center gap-1.5 p-3 rounded-lg hover:bg-gray-50"
              >
                <Icon className="h-5 w-5 text-gray-500" />
                <span className="text-[11px] text-gray-700 text-center leading-tight">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
