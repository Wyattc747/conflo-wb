"use client";

import { TopBar } from "@/components/gc/TopBar";
import { MobileMenu } from "@/components/shared/MobileMenu";

const GC_NAV_ITEMS = [
  { label: "Dashboard", href: "/app/dashboard" },
  { label: "Directory", href: "/app/contacts" },
  { label: "Projects", href: "/app/projects" },
];

export default function GCLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-100">
      <TopBar />
      <MobileMenu navItems={GC_NAV_ITEMS} />
      <main className="pt-14">{children}</main>
    </div>
  );
}
