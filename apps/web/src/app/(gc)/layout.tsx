export default function GCLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* GC Portal Shell: top bar + sidebar — placeholder */}
      <div className="flex">
        <aside className="w-64 min-h-screen bg-primary text-white p-4">
          <div className="text-xl font-bold mb-8">Conflo</div>
          <nav className="space-y-2 text-sm text-gray-300">
            <p>Dashboard</p>
            <p>Projects</p>
            <p>Contacts</p>
            <p>Admin</p>
            <p>Settings</p>
          </nav>
        </aside>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
