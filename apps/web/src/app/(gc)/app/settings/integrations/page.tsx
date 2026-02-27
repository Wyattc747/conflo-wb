"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  Calendar,
  DollarSign,
  ExternalLink,
  Loader2,
  Plug,
  Video,
  FileSignature,
  Check,
  X,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import { useIntegrations, useConnectIntegration, useDisconnectIntegration } from "@/hooks/use-integrations";
import type { IntegrationStatus } from "@/types/integration";

const PROVIDER_ICONS: Record<string, typeof Calendar> = {
  google_calendar: Calendar,
  microsoft: Calendar,
  quickbooks: DollarSign,
  zoom: Video,
  docusign: FileSignature,
};

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  CONNECTED: { label: "Connected", className: "text-green-700 bg-green-50 border-green-200" },
  DISCONNECTED: { label: "Connect", className: "text-blue-700 bg-blue-50 border-blue-200" },
  COMING_SOON: { label: "Coming Soon", className: "text-gray-500 bg-gray-50 border-gray-200" },
};

export default function IntegrationsPage() {
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  if (!token) {
    getToken().then(setToken);
  }

  const { data, isLoading } = useIntegrations(token);
  const connect = useConnectIntegration(token);
  const disconnect = useDisconnectIntegration(token);

  const integrations = data?.data || [];

  const handleConnect = async (provider: string) => {
    try {
      const result = await connect.mutateAsync(provider);
      if (result?.data?.auth_url) {
        window.location.href = result.data.auth_url;
      }
    } catch {
      // Error handled by mutation
    }
  };

  const handleDisconnect = (provider: string) => {
    if (window.confirm("Are you sure you want to disconnect this integration?")) {
      disconnect.mutate(provider);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Integrations" subtitle="Connect your favorite tools" />

      {isLoading ? (
        <div className="py-8 text-center">
          <Loader2 className="h-6 w-6 text-gray-400 animate-spin mx-auto" />
        </div>
      ) : (
        <div className="space-y-3">
          {integrations.map((integration) => {
            const Icon = PROVIDER_ICONS[integration.provider] || Plug;
            const style = STATUS_STYLES[integration.status] || STATUS_STYLES.DISCONNECTED;

            return (
              <Card key={integration.provider}>
                <div className="p-4 flex items-center gap-4">
                  <div className="h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Icon className="h-5 w-5 text-gray-600" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900">
                      {integration.name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {integration.description}
                    </p>
                    {integration.status === "CONNECTED" && integration.connected_at && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        Connected {new Date(integration.connected_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {integration.status === "CONNECTED" ? (
                      <>
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-green-50 text-green-700 border border-green-200">
                          <Check className="h-3 w-3" />
                          Connected
                        </span>
                        <button
                          onClick={() => handleDisconnect(integration.provider)}
                          className="text-xs text-red-600 hover:text-red-700 font-medium px-2 py-1"
                        >
                          Disconnect
                        </button>
                      </>
                    ) : integration.status === "DISCONNECTED" ? (
                      <button
                        onClick={() => handleConnect(integration.provider)}
                        disabled={connect.isPending}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                      >
                        {connect.isPending ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <ExternalLink className="h-3.5 w-3.5" />
                        )}
                        Connect
                      </button>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-gray-50 text-gray-500 border border-gray-200">
                        Coming Soon
                      </span>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
