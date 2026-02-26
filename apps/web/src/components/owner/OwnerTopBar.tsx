"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Menu, X } from "lucide-react";
import { useMobileMenuStore } from "@/stores/ui-store";

export function OwnerTopBar() {
  const pathname = usePathname();
  const { open: mobileMenuOpen, toggle: toggleMobileMenu } = useMobileMenuStore();

  const isProjectsActive = pathname.startsWith("/owner");

  return (
    <header className="h-14 bg-black flex items-center justify-between px-4 fixed top-0 left-0 right-0 z-50">
      {/* Left: Logo + Nav */}
      <div className="flex items-center gap-6">
        <Link href="/owner" className="flex-shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo-cf-white.svg" alt="Conflo" className="h-8 w-auto" />
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          <Link
            href="/owner"
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              isProjectsActive
                ? "bg-yellow-500 text-white"
                : "text-white hover:text-yellow-300"
            }`}
          >
            Projects
          </Link>
        </nav>
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        <Link href="/owner" className="text-white hover:text-yellow-300 relative">
          <Bell className="h-5 w-5" />
        </Link>
        <div className="h-8 w-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-medium">
          O
        </div>
        <button
          onClick={toggleMobileMenu}
          className="md:hidden text-white hover:text-yellow-300"
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
    </header>
  );
}
