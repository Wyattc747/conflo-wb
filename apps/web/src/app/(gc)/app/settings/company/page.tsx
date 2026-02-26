"use client";

import { Building2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function CompanySettingsPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Company Settings" subtitle="Manage your organization profile" />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Building2 className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">Company Profile</h3>
          <p className="text-sm text-gray-500">Company settings will be available in a future update.</p>
        </div>
      </Card>
    </div>
  );
}
