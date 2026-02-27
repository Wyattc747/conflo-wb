export interface IntegrationStatus {
  provider: string;
  name: string;
  description: string;
  status: "CONNECTED" | "DISCONNECTED" | "COMING_SOON";
  connected_at?: string | null;
}
