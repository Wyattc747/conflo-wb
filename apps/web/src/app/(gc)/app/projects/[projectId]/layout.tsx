export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <aside className="w-52 min-h-screen bg-white border-r p-4">
        <nav className="space-y-1 text-sm text-gray-600">
          <p>Overview</p>
          <p>Daily Logs</p>
          <p>RFIs</p>
          <p>Submittals</p>
          <p>Change Orders</p>
          <p>Schedule</p>
          <p>Punch List</p>
          <p>Budget</p>
          <p>Pay Apps</p>
          <p>Drawings</p>
          <p>Inspections</p>
          <p>Bid Packages</p>
          <p>Meetings</p>
          <p>To-Do</p>
          <p>Procurement</p>
          <p>Documents</p>
          <p>Directory</p>
          <p>Settings</p>
        </nav>
      </aside>
      <div className="flex-1">{children}</div>
    </div>
  );
}
