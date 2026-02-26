"use client";

import { CreditCard } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function BillingPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Billing" subtitle="Manage your subscription and payment methods" />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <CreditCard className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">Subscription Management</h3>
          <p className="text-sm text-gray-500">Billing settings will be connected to Stripe in a future update.</p>
        </div>
      </Card>
    </div>
  );
}
