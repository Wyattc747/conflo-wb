"use client";

import { Hash } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function CostCodesPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Cost Codes" subtitle="Manage cost code templates for your projects" />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Hash className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">Cost Code Templates</h3>
          <p className="text-sm text-gray-500">Cost code management will be available in a future update.</p>
        </div>
      </Card>
    </div>
  );
}
