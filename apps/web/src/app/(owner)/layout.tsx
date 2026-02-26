"use client";

import { OwnerTopBar } from "@/components/owner/OwnerTopBar";
import { MobileMenu } from "@/components/shared/MobileMenu";

const OWNER_NAV_ITEMS = [{ label: "Projects", href: "/owner" }];

export default function OwnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-100">
      <OwnerTopBar />
      <MobileMenu navItems={OWNER_NAV_ITEMS} />
      <main className="pt-14">{children}</main>
    </div>
  );
}
