"use client";

import Link from "next/link";
import { Bell, Menu, X } from "lucide-react";
import { useMobileMenuStore } from "@/stores/ui-store";

export function SubTopBar() {
  const { open: mobileMenuOpen, toggle: toggleMobileMenu } = useMobileMenuStore();

  return (
    <header className="h-14 bg-black flex items-center justify-between px-4 fixed top-0 left-0 right-0 z-50">
      {/* Left: Logo + Project Switcher placeholder */}
      <div className="flex items-center gap-4">
        <Link href="/sub/dashboard" className="flex-shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo-cf-white.svg" alt="Conflo" className="h-8 w-auto" />
        </Link>

        {/* Project switcher (stub) */}
        <button className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 text-sm text-gray-300 hover:bg-gray-700">
          <span className="truncate max-w-[200px]">Select Project</span>
          <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        <Link href="/sub/dashboard" className="text-white hover:text-yellow-300 relative">
          <Bell className="h-5 w-5" />
        </Link>
        <div className="h-8 w-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-medium">
          S
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
