"use client";

import { useState, useEffect, createContext, useContext } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  Users,
  BarChart3,
  Settings,
  LogOut,
  Shield,
} from "lucide-react";

interface AdminContext {
  token: string | null;
  admin: { id: string; name: string; email: string; role: string } | null;
  logout: () => void;
}

const AdminCtx = createContext<AdminContext>({
  token: null,
  admin: null,
  logout: () => {},
});

export const useAdmin = () => useContext(AdminCtx);

const NAV_ITEMS = [
  { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { label: "Organizations", href: "/admin/organizations", icon: Building2 },
  { label: "Users", href: "/admin/users", icon: Users },
  { label: "Metrics", href: "/admin/metrics", icon: BarChart3 },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [admin, setAdmin] = useState<AdminContext["admin"]>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("admin_token");
    const storedAdmin = localStorage.getItem("admin_user");
    if (stored && storedAdmin) {
      setToken(stored);
      setAdmin(JSON.parse(storedAdmin));
    } else if (pathname !== "/admin/login") {
      router.push("/admin/login");
    }
  }, [pathname, router]);

  const logout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    setToken(null);
    setAdmin(null);
    router.push("/admin/login");
  };

  // Show login page without chrome
  if (pathname === "/admin/login") {
    return <>{children}</>;
  }

  if (!token) {
    return null; // Loading / redirecting
  }

  return (
    <AdminCtx.Provider value={{ token, admin, logout }}>
      <div className="min-h-screen bg-gray-50 flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-900 text-white flex flex-col fixed inset-y-0 left-0 z-40">
          <div className="h-14 flex items-center gap-2 px-4 border-b border-gray-800">
            <Shield className="h-6 w-6 text-yellow-500" />
            <span className="font-bold text-lg">Conflo Admin</span>
          </div>

          <nav className="flex-1 py-4 space-y-1 px-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href ||
                (item.href !== "/admin" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-gray-800 text-yellow-500"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-gray-800">
            <div className="text-sm text-gray-400 mb-2">{admin?.email}</div>
            <button
              onClick={logout}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 ml-64">
          <div className="p-6">{children}</div>
        </main>
      </div>
    </AdminCtx.Provider>
  );
}
