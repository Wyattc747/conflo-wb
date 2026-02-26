"use client";

import { CheckCircle2, Circle, Clock } from "lucide-react";

interface TimelineEvent {
  label: string;
  date?: string | null;
  status: "completed" | "current" | "upcoming";
}

interface DateTimelineProps {
  events: TimelineEvent[];
}

export function DateTimeline({ events }: DateTimelineProps) {
  return (
    <div className="space-y-0">
      {events.map((event, i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            {event.status === "completed" ? (
              <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
            ) : event.status === "current" ? (
              <Clock className="h-5 w-5 text-[#2E75B6] shrink-0" />
            ) : (
              <Circle className="h-5 w-5 text-gray-300 shrink-0" />
            )}
            {i < events.length - 1 && (
              <div className={`w-0.5 flex-1 min-h-[24px] ${event.status === "completed" ? "bg-green-300" : "bg-gray-200"}`} />
            )}
          </div>
          <div className="pb-4">
            <p className={`text-sm font-medium ${event.status === "completed" ? "text-gray-700" : event.status === "current" ? "text-[#2E75B6]" : "text-gray-400"}`}>
              {event.label}
            </p>
            {event.date && (
              <p className="text-xs text-gray-400 mt-0.5">
                {new Date(event.date).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
