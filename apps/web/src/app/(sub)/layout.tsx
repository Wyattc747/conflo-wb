"use client";

import { SubTopBar } from "@/components/sub/SubTopBar";
import { SubSidebar } from "@/components/sub/SubSidebar";
import { MobileMenu } from "@/components/shared/MobileMenu";
import { usePathname } from "next/navigation";

const SUB_NAV_ITEMS = [
  { label: "Dashboard", href: "/sub/dashboard" },
  { label: "Projects", href: "/sub/projects" },
  { label: "Bids", href: "/sub/bids" },
  { label: "Financials", href: "/sub/financials" },
  { label: "Company", href: "/sub/company" },
];

export default function SubLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Detect if inside a project
  const projectMatch = pathname.match(/\/sub\/projects\/([^/]+)/);
  const projectId = projectMatch?.[1];
  const isInProject = projectId && pathname !== "/sub/projects";

  return (
    <div className="min-h-screen bg-gray-100">
      <SubTopBar />
      <MobileMenu navItems={SUB_NAV_ITEMS} />
      <div className="pt-14 flex">
        <SubSidebar projectId={isInProject ? projectId : undefined} />
        <main className="flex-1 md:ml-[180px] p-6 pb-20 md:pb-6">{children}</main>
      </div>
    </div>
  );
}
