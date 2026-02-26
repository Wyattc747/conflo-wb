"use client";

import { useParams, useRouter } from "next/navigation";
import { CalendarClock, Cloud, Sun, CloudRain, Users, Clock, AlertTriangle } from "lucide-react";
import { DetailHeader } from "@/components/shared/DetailHeader";
import { Card } from "@/components/shared/Card";
import { CommentThread } from "@/components/shared/CommentThread";
import { StatusActions } from "@/components/shared/StatusActions";

// Mock data
const MOCK_LOG = {
  id: "1",
  project_id: "p1",
  log_date: "2026-02-25",
  number: "DL-2026-02-25",
  weather_data: { condition: "Sunny", temp_high: 72, temp_low: 45, wind_speed: 8, humidity: 35 },
  work_performed:
    "Poured concrete for footings on grid A-C. Steel erection continued on level 2. MEP rough-in ongoing in level 1. Waterproofing applied to north foundation wall.",
  delays_text: null,
  schedule_delays: [
    { delay_days: 1, reason_category: "WEATHER", responsible_party: "GC", description: "Morning rain delayed concrete pour by 1 hour", status: "PENDING" },
  ],
  manpower: [
    { trade: "Concrete", workers: 8, hours: 64 },
    { trade: "Ironworkers", workers: 6, hours: 48 },
    { trade: "Plumbing", workers: 3, hours: 24 },
    { trade: "Electrical", workers: 4, hours: 32 },
  ],
  status: "DRAFT",
  created_by_name: "John Smith",
  created_at: "2026-02-25T08:00:00Z",
  updated_at: "2026-02-25T16:30:00Z",
};

const MOCK_COMMENTS = [
  {
    id: "c1",
    body: "Foundation pour looked good. Cylinders collected for 7-day break.",
    author_name: "Mike Chen",
    author_type: "GC_USER",
    created_at: "2026-02-25T12:30:00Z",
    is_official_response: false,
  },
  {
    id: "c2",
    body: "Steel delivery for level 3 confirmed for Thursday.",
    author_name: "John Smith",
    author_type: "GC_USER",
    created_at: "2026-02-25T14:15:00Z",
    is_official_response: false,
  },
];

function WeatherIcon({ condition }: { condition?: string }) {
  if (!condition) return null;
  const lower = condition.toLowerCase();
  if (lower.includes("rain")) return <CloudRain className="h-5 w-5 text-blue-500" />;
  if (lower.includes("cloud")) return <Cloud className="h-5 w-5 text-gray-400" />;
  return <Sun className="h-5 w-5 text-yellow-500" />;
}

export default function DailyLogDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const log = MOCK_LOG;

  const totalWorkers = log.manpower.reduce((sum, m) => sum + m.workers, 0);
  const totalHours = log.manpower.reduce((sum, m) => sum + m.hours, 0);

  const statusActions = [];
  if (log.status === "DRAFT") {
    statusActions.push({
      label: "Edit",
      variant: "secondary" as const,
      onClick: () => router.push(`/app/projects/${projectId}/daily-logs/${log.id}/edit`),
    });
    statusActions.push({
      label: "Submit for Approval",
      variant: "primary" as const,
      onClick: () => console.log("submit"),
    });
  }
  if (log.status === "SUBMITTED") {
    statusActions.push({
      label: "Approve",
      variant: "primary" as const,
      onClick: () => console.log("approve"),
    });
  }

  return (
    <div>
      <DetailHeader
        backHref={`/app/projects/${projectId}/daily-logs`}
        number={log.number}
        title={new Date(log.log_date + "T00:00:00").toLocaleDateString("en-US", {
          weekday: "long",
          year: "numeric",
          month: "long",
          day: "numeric",
        })}
        status={log.status}
        actions={<StatusActions actions={statusActions} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column — main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Weather */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Weather</h2>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <WeatherIcon condition={log.weather_data?.condition} />
                <span className="text-sm font-medium">{log.weather_data?.condition}</span>
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium">{log.weather_data?.temp_high}°</span>
                <span className="text-gray-400"> / </span>
                <span>{log.weather_data?.temp_low}°</span>
              </div>
              {log.weather_data?.wind_speed != null && (
                <div className="text-sm text-gray-500">
                  Wind: {log.weather_data.wind_speed} mph
                </div>
              )}
              {log.weather_data?.humidity != null && (
                <div className="text-sm text-gray-500">
                  Humidity: {log.weather_data.humidity}%
                </div>
              )}
            </div>
          </Card>

          {/* Work Performed */}
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Work Performed</h2>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {log.work_performed || "No work recorded."}
            </p>
          </Card>

          {/* Manpower */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-gray-900">Manpower</h2>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" />
                  {totalWorkers} workers
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {totalHours} hours
                </span>
              </div>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 font-medium text-gray-500 text-xs uppercase">Trade</th>
                  <th className="text-right py-2 font-medium text-gray-500 text-xs uppercase">Workers</th>
                  <th className="text-right py-2 font-medium text-gray-500 text-xs uppercase">Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {log.manpower.map((row, idx) => (
                  <tr key={idx}>
                    <td className="py-2 text-gray-700">{row.trade}</td>
                    <td className="py-2 text-right text-gray-700">{row.workers}</td>
                    <td className="py-2 text-right text-gray-700">{row.hours}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-gray-200 font-medium">
                  <td className="py-2">Total</td>
                  <td className="py-2 text-right">{totalWorkers}</td>
                  <td className="py-2 text-right">{totalHours}</td>
                </tr>
              </tfoot>
            </table>
          </Card>

          {/* Delays */}
          {log.delays_text && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                <h2 className="text-sm font-semibold text-gray-900">Delays & Issues</h2>
              </div>
              <p className="text-sm text-gray-700">{log.delays_text}</p>
            </Card>
          )}

          {/* Schedule Impact */}
          {log.schedule_delays && log.schedule_delays.length > 0 && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <CalendarClock className="h-4 w-4 text-[#2E75B6]" />
                <h2 className="text-sm font-semibold text-gray-900">Schedule Impact</h2>
              </div>
              <div className="space-y-3">
                {log.schedule_delays.map((delay: any, idx: number) => (
                  <div key={idx} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-gray-500 uppercase">
                          {delay.reason_category.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-gray-400">|</span>
                        <span className="text-xs text-gray-500">{delay.responsible_party}</span>
                      </div>
                      <p className="text-sm text-gray-700">{delay.description}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-4 shrink-0">
                      <span className="text-sm font-semibold text-red-600">+{delay.delay_days}d</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        delay.status === "PENDING" ? "bg-yellow-100 text-yellow-700" :
                        delay.status === "APPROVED" ? "bg-green-100 text-green-700" :
                        delay.status === "APPLIED" ? "bg-blue-100 text-blue-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>
                        {delay.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right column — metadata & comments */}
        <div className="space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Details</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Created By</dt>
                <dd className="font-medium">{log.created_by_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(log.created_at).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Last Updated</dt>
                <dd>{new Date(log.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </Card>

          <CommentThread
            comments={MOCK_COMMENTS}
            onSubmit={(body) => console.log("Comment:", body)}
          />
        </div>
      </div>
    </div>
  );
}
