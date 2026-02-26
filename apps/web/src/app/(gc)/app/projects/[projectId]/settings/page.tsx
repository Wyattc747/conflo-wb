"use client";

import { Settings } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function ProjectSettingsPage() {
  return (
    <div>
      <PageHeader
        title="Project Settings"
        subtitle="Configure project preferences and access"
      />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Settings className="h-10 w-10 text-gray-300 mb-3" />
          <p className="text-sm text-gray-500">Project settings will be available in a future update.</p>
        </div>
      </Card>
    </div>
  );
}
