export default function OwnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Owner Portal Shell: top bar + horizontal tabs — placeholder */}
      <header className="bg-primary text-white px-6 py-4">
        <div className="text-xl font-bold">Conflo — Owner Portal</div>
      </header>
      <main>{children}</main>
    </div>
  );
}
