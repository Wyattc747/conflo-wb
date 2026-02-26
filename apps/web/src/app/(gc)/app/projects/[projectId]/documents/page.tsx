"use client";

import { Plus, FolderOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function DocumentsPage() {
  return (
    <div>
      <PageHeader
        title="Documents"
        subtitle="Upload and organize project documents"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Upload Document
          </button>
        }
      />
      <EmptyState
        icon={FolderOpen}
        title="No documents yet"
        description="Upload your first document to start organizing project files."
        actionLabel="Upload Document"
        onAction={() => {}}
      />
    </div>
  );
}
