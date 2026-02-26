"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { StatusBadge } from "./StatusBadge";

interface DetailHeaderProps {
  backHref?: string;
  number?: string;
  title: string;
  status?: string;
  actions?: React.ReactNode;
}

export function DetailHeader({
  backHref,
  number,
  title,
  status,
  actions,
}: DetailHeaderProps) {
  const router = useRouter();

  return (
    <div className="flex items-start justify-between mb-6">
      <div className="flex items-start gap-3">
        {backHref && (
          <button
            onClick={() => router.push(backHref)}
            className="mt-1 p-1 rounded hover:bg-gray-200"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </button>
        )}
        <div>
          <div className="flex items-center gap-2">
            {number && (
              <span className="text-sm font-mono text-gray-500">{number}</span>
            )}
            {status && <StatusBadge status={status} />}
          </div>
          <h1 className="text-xl font-bold text-gray-900 mt-0.5">{title}</h1>
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
