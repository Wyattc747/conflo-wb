"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CalendarClock, Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/shared/Card";

const WEATHER_CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Overcast", "Rain", "Snow", "Wind", "Fog"];
const TRADES = [
  "General Conditions", "Concrete", "Masonry", "Metals", "Carpentry", "Thermal/Moisture Protection",
  "Doors/Windows", "Finishes", "Plumbing", "HVAC", "Electrical", "Fire Protection", "Low Voltage",
  "Earthwork", "Paving", "Landscaping", "Demolition", "Other",
];
const DELAY_REASONS = [
  "WEATHER", "OWNER_CHANGE", "DESIGN_ERROR", "PERMITTING", "MATERIAL_DELIVERY",
  "LABOR_SHORTAGE", "UNFORESEEN_CONDITIONS", "SUB_CAUSED", "FORCE_MAJEURE", "OTHER",
];
const RESPONSIBLE_PARTIES = ["GC", "OWNER", "SUB", "AE", "OTHER"];

type ScheduleDelayEntry = {
  delay_days: number;
  reason_category: string;
  responsible_party: string;
  description: string;
};

export default function NewDailyLogPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [logDate, setLogDate] = useState(new Date().toISOString().split("T")[0]);
  const [weatherCondition, setWeatherCondition] = useState("");
  const [tempHigh, setTempHigh] = useState("");
  const [tempLow, setTempLow] = useState("");
  const [workPerformed, setWorkPerformed] = useState("");
  const [delays, setDelays] = useState("");
  const [scheduleDelays, setScheduleDelays] = useState<ScheduleDelayEntry[]>([]);
  const [manpower, setManpower] = useState<{ trade: string; workers: number; hours: number }[]>([]);

  const addManpowerRow = () => {
    setManpower([...manpower, { trade: "", workers: 0, hours: 0 }]);
  };

  const updateManpower = (idx: number, field: string, value: any) => {
    const updated = [...manpower];
    (updated[idx] as any)[field] = value;
    setManpower(updated);
  };

  const removeManpower = (idx: number) => {
    setManpower(manpower.filter((_, i) => i !== idx));
  };

  const totalWorkers = manpower.reduce((sum, m) => sum + (m.workers || 0), 0);
  const totalHours = manpower.reduce((sum, m) => sum + (m.hours || 0), 0);

  const addScheduleDelay = () => {
    setScheduleDelays([...scheduleDelays, { delay_days: 1, reason_category: "", responsible_party: "", description: "" }]);
  };

  const updateScheduleDelay = (idx: number, field: string, value: any) => {
    const updated = [...scheduleDelays];
    (updated[idx] as any)[field] = value;
    setScheduleDelays(updated);
  };

  const removeScheduleDelay = (idx: number) => {
    setScheduleDelays(scheduleDelays.filter((_, i) => i !== idx));
  };

  const handleSave = (asDraft: boolean) => {
    // TODO: Wire to API via useCreateDailyLog hook
    console.log({
      log_date: logDate,
      weather_condition: weatherCondition,
      temp_high: tempHigh ? Number(tempHigh) : undefined,
      temp_low: tempLow ? Number(tempLow) : undefined,
      work_performed: workPerformed,
      delays,
      schedule_delays: scheduleDelays.filter((d) => d.reason_category && d.description),
      manpower: manpower.filter((m) => m.trade),
      status: asDraft ? "DRAFT" : "DRAFT",
    });
    router.push(`/app/projects/${projectId}/daily-logs`);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push(`/app/projects/${projectId}/daily-logs`)}
            className="p-1 rounded hover:bg-gray-200"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">New Daily Log</h1>
            <p className="text-sm text-gray-500">Record today&apos;s project activity</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => router.back()}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => handleSave(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-[#1B2A4A] rounded-lg hover:bg-[#243558]"
          >
            Save Draft
          </button>
        </div>
      </div>

      <div className="space-y-5">
        {/* Date & Weather */}
        <Card>
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Date & Weather</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Log Date *</label>
              <input
                type="date"
                value={logDate}
                onChange={(e) => setLogDate(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Condition</label>
              <select
                value={weatherCondition}
                onChange={(e) => setWeatherCondition(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
              >
                <option value="">Select...</option>
                {WEATHER_CONDITIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">High Temp (°F)</label>
              <input
                type="number"
                value={tempHigh}
                onChange={(e) => setTempHigh(e.target.value)}
                placeholder="72"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Low Temp (°F)</label>
              <input
                type="number"
                value={tempLow}
                onChange={(e) => setTempLow(e.target.value)}
                placeholder="45"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
              />
            </div>
          </div>
        </Card>

        {/* Work Performed */}
        <Card>
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Work Performed</h2>
          <textarea
            value={workPerformed}
            onChange={(e) => setWorkPerformed(e.target.value)}
            rows={5}
            placeholder="Describe work performed on site today..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
          />
        </Card>

        {/* Manpower */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Manpower</h2>
            <button
              onClick={addManpowerRow}
              className="flex items-center gap-1 text-sm text-[#1B2A4A] hover:underline"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Trade
            </button>
          </div>

          {manpower.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">
              No manpower entries. Click &quot;Add Trade&quot; to track on-site workers.
            </p>
          ) : (
            <div className="space-y-2">
              <div className="grid grid-cols-[1fr_100px_100px_40px] gap-2 text-xs font-medium text-gray-500">
                <span>Trade</span>
                <span>Workers</span>
                <span>Hours</span>
                <span />
              </div>
              {manpower.map((row, idx) => (
                <div key={idx} className="grid grid-cols-[1fr_100px_100px_40px] gap-2">
                  <select
                    value={row.trade}
                    onChange={(e) => updateManpower(idx, "trade", e.target.value)}
                    className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                  >
                    <option value="">Select trade...</option>
                    {TRADES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min={0}
                    value={row.workers || ""}
                    onChange={(e) => updateManpower(idx, "workers", Number(e.target.value))}
                    placeholder="0"
                    className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                  />
                  <input
                    type="number"
                    min={0}
                    value={row.hours || ""}
                    onChange={(e) => updateManpower(idx, "hours", Number(e.target.value))}
                    placeholder="0"
                    className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                  />
                  <button
                    onClick={() => removeManpower(idx)}
                    className="p-2 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <div className="grid grid-cols-[1fr_100px_100px_40px] gap-2 pt-2 border-t border-gray-200 text-xs font-medium text-gray-600">
                <span>Totals</span>
                <span>{totalWorkers}</span>
                <span>{totalHours}</span>
                <span />
              </div>
            </div>
          )}
        </Card>

        {/* Delays */}
        <Card>
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Delays & Issues</h2>
          <textarea
            value={delays}
            onChange={(e) => setDelays(e.target.value)}
            rows={3}
            placeholder="Describe any delays, weather impacts, or issues..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
          />
        </Card>

        {/* Schedule Impact */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CalendarClock className="h-4 w-4 text-[#2E75B6]" />
              <h2 className="text-sm font-semibold text-gray-900">Schedule Impact</h2>
            </div>
            <button
              onClick={addScheduleDelay}
              className="flex items-center gap-1 text-sm text-[#1B2A4A] hover:underline"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Delay
            </button>
          </div>

          {scheduleDelays.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">
              No schedule delays. Click &quot;Add Delay&quot; to log a schedule impact.
            </p>
          ) : (
            <div className="space-y-4">
              {scheduleDelays.map((entry, idx) => (
                <div key={idx} className="p-3 border border-gray-200 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-500 uppercase">Delay #{idx + 1}</span>
                    <button
                      onClick={() => removeScheduleDelay(idx)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Reason *</label>
                      <select
                        value={entry.reason_category}
                        onChange={(e) => updateScheduleDelay(idx, "reason_category", e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                      >
                        <option value="">Select reason...</option>
                        {DELAY_REASONS.map((r) => (
                          <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Responsible Party *</label>
                      <select
                        value={entry.responsible_party}
                        onChange={(e) => updateScheduleDelay(idx, "responsible_party", e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                      >
                        <option value="">Select...</option>
                        {RESPONSIBLE_PARTIES.map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Days Delayed *</label>
                      <input
                        type="number"
                        min={1}
                        value={entry.delay_days || ""}
                        onChange={(e) => updateScheduleDelay(idx, "delay_days", Number(e.target.value))}
                        placeholder="1"
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Description *</label>
                    <input
                      type="text"
                      value={entry.description}
                      onChange={(e) => updateScheduleDelay(idx, "description", e.target.value)}
                      placeholder="Describe the schedule impact..."
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                    />
                  </div>
                </div>
              ))}
              <p className="text-xs text-gray-400">
                Schedule delays will create pending delay records in the Schedule tool for approval.
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
