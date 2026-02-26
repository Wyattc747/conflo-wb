"use client";

import { User } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function ProfilePage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Profile" subtitle="Manage your account settings" />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <div className="h-20 w-20 rounded-full bg-gray-200 flex items-center justify-center mb-4">
            <User className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-gray-900 mb-1">Marcus Johnson</h3>
          <p className="text-sm text-gray-500">marcus@example.com</p>
          <p className="text-xs text-gray-400 mt-1">Owner/Admin</p>
        </div>
      </Card>
    </div>
  );
}
