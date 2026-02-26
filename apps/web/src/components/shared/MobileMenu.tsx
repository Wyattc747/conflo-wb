"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, Bell, User, LogOut } from "lucide-react";
import { useMobileMenuStore } from "@/stores/ui-store";

interface MobileMenuProps {
  navItems: { label: string; href: string }[];
}

export function MobileMenu({ navItems }: MobileMenuProps) {
  const pathname = usePathname();
  const { open, setOpen } = useMobileMenuStore();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] md:hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />

      {/* Menu panel */}
      <div className="absolute top-0 left-0 right-0 bg-black text-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 h-14 border-b border-gray-800">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo-cf-white.svg" alt="Conflo" className="h-8 w-auto" />
          <button onClick={() => setOpen(false)} className="text-white hover:text-yellow-300">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="px-2 py-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`block px-3 py-2.5 rounded-lg text-sm font-medium ${
                  isActive ? "bg-yellow-500 text-white" : "text-gray-300 hover:bg-gray-800"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Divider */}
        <div className="border-t border-gray-800 mx-4" />

        {/* Extra links */}
        <div className="px-2 py-3 space-y-1">
          <Link
            href="/app/notifications"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-gray-800 rounded-lg"
          >
            <Bell className="h-4 w-4" />
            Notifications
          </Link>
          <Link
            href="/app/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-gray-800 rounded-lg"
          >
            <User className="h-4 w-4" />
            Profile
          </Link>
          <button className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-gray-800 rounded-lg w-full text-left">
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
