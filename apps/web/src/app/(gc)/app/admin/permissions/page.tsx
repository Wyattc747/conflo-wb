"use client";

import { Shield } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function PermissionsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Permissions"
        subtitle="View and manage permission levels"
      />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Shield className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">Permission Matrix</h3>
          <p className="text-sm text-gray-500">Permission management will be available in a future update.</p>
        </div>
      </Card>
    </div>
  );
}
