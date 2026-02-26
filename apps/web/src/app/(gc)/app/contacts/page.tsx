"use client";

import { Plus, Users } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ContactsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Directory"
        subtitle="Manage your company contacts and external partners"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Contact
          </button>
        }
      />
      <EmptyState
        icon={Users}
        title="No contacts yet"
        description="Add your first contact to build your company directory."
        actionLabel="Add Contact"
        onAction={() => {}}
      />
    </div>
  );
}
