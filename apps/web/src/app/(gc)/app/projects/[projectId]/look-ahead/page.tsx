"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Eye, Upload } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/shared/Card";

interface LookAheadTask {
  id: string;
  name: string;
  wbs_code?: string;
  assigned_to_sub_name?: string | null;
  start_date: string;
  end_date: string;
  percent_complete: number;
  is_critical: boolean;
  milestone: boolean;
}

const MOCK_TASKS: LookAheadTask[] = [
  {
    id: "2",
    name: "Foundation concrete pour",
    wbs_code: "1.2",
    assigned_to_sub_name: "ABC Concrete",
    start_date: "2026-02-24",
    end_date: "2026-03-07",
    percent_complete: 40,
    is_critical: true,
    milestone: false,
  },
  {
    id: "3",
    name: "Structural steel erection - Level 1",
    wbs_code: "2.1",
    assigned_to_sub_name: "Apex Steel Fabricators",
    start_date: "2026-03-10",
    end_date: "2026-03-28",
    percent_complete: 0,
    is_critical: true,
    milestone: false,
  },
  {
    id: "4",
    name: "Level 1 framing complete",
    wbs_code: "2.2",
    start_date: "2026-03-28",
    end_date: "2026-03-28",
    percent_complete: 0,
    is_critical: true,
    milestone: true,
  },
  {
    id: "5",
    name: "MEP rough-in - Level 1",
    wbs_code: "3.1",
    assigned_to_sub_name: "Summit Mechanical",
    start_date: "2026-03-17",
    end_date: "2026-04-07",
    percent_complete: 0,
    is_critical: false,
    milestone: false,
  },
];

function getWeekLabel(date: Date): string {
  const startOfWeek = new Date(date);
  startOfWeek.setDate(date.getDate() - date.getDay() + 1); // Monday
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 4); // Friday
  return `${startOfWeek.toLocaleDateString("en-US", { month: "short", day: "numeric" })} - ${endOfWeek.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
}

function getWeekNumber(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  const startOfWeek = new Date(date);
  startOfWeek.setDate(date.getDate() - date.getDay() + 1);
  return startOfWeek.toISOString().slice(0, 10);
}

function groupByWeek(tasks: LookAheadTask[]): Map<string, LookAheadTask[]> {
  const weeks = new Map<string, LookAheadTask[]>();

  tasks.forEach((task) => {
    const taskStart = new Date(task.start_date + "T00:00:00");
    const taskEnd = new Date(task.end_date + "T00:00:00");
    const now = new Date();

    // Find all weeks this task spans
    const current = new Date(taskStart);
    while (current <= taskEnd) {
      if (current >= now || getWeekNumber(current.toISOString().slice(0, 10)) >= getWeekNumber(now.toISOString().slice(0, 10))) {
        const weekKey = getWeekNumber(current.toISOString().slice(0, 10));
        if (!weeks.has(weekKey)) weeks.set(weekKey, []);
        const weekTasks = weeks.get(weekKey)!;
        if (!weekTasks.find((t) => t.id === task.id)) {
          weekTasks.push(task);
        }
      }
      current.setDate(current.getDate() + 7);
    }
  });

  return new Map([...weeks.entries()].sort());
}

export default function LookAheadPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const [weeks] = useState(3);

  const grouped = groupByWeek(MOCK_TASKS);
  const weekEntries = [...grouped.entries()].slice(0, weeks);
  const hasData = MOCK_TASKS.length > 0;

  return (
    <div>
      <PageHeader
        title="Look Ahead"
        subtitle="View upcoming tasks and milestones"
        action={
          <button
            onClick={() => console.log("publish look-ahead")}
            className="bg-[#2E75B6] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#256099] flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            Publish Look Ahead
          </button>
        }
      />

      {hasData ? (
        <div className="space-y-5">
          {weekEntries.map(([weekKey, tasks]) => {
            const weekDate = new Date(weekKey + "T00:00:00");
            return (
              <Card key={weekKey}>
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#2E75B6]" />
                  Week of {getWeekLabel(weekDate)}
                </h3>
                <div className="space-y-2">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className={`flex items-center gap-4 p-3 rounded-lg border ${
                        task.is_critical ? "border-red-100 bg-red-50/30" : "border-gray-100"
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {task.milestone && (
                            <span className="flex-shrink-0 w-2.5 h-2.5 bg-[#2E75B6] rotate-45" />
                          )}
                          {task.is_critical && !task.milestone && (
                            <span className="flex-shrink-0 w-1.5 h-4 bg-red-400 rounded-sm" />
                          )}
                          <span className="font-medium text-sm truncate">
                            {task.wbs_code && (
                              <span className="text-gray-400 font-mono mr-2">{task.wbs_code}</span>
                            )}
                            {task.name}
                          </span>
                        </div>
                        {task.assigned_to_sub_name && (
                          <span className="text-xs text-gray-400 ml-5">{task.assigned_to_sub_name}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 flex-shrink-0">
                        <span>
                          {new Date(task.start_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                          {" - "}
                          {new Date(task.end_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        </span>
                        <div className="w-16">
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${task.percent_complete === 100 ? "bg-green-500" : "bg-[#2E75B6]"}`}
                              style={{ width: `${task.percent_complete}%` }}
                            />
                          </div>
                        </div>
                        <span className="w-8 text-right">{task.percent_complete}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={Eye}
          title="No upcoming items"
          description="Upcoming tasks, deadlines, and milestones will appear here as you add project data."
        />
      )}
    </div>
  );
}
