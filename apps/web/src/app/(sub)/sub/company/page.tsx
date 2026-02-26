"use client";

import { Building2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function SubCompanyPage() {
  return (
    <div>
      <PageHeader
        title="Company Profile"
        subtitle="Manage your company information"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558]">
            Edit Profile
          </button>
        }
      />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <div className="h-16 w-16 rounded-lg bg-gray-100 flex items-center justify-center mb-4">
            <Building2 className="h-8 w-8 text-gray-300" />
          </div>
          <h3 className="text-base font-semibold text-gray-900 mb-1">Company Name</h3>
          <p className="text-sm text-gray-500 mb-4">Complete your company profile to help GCs find you.</p>
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558]">
            Complete Profile
          </button>
        </div>
      </Card>
    </div>
  );
}
