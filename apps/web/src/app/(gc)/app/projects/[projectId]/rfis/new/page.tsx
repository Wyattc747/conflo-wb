"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Card } from "@/components/shared/Card";

export default function NewRFIPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [subject, setSubject] = useState("");
  const [question, setQuestion] = useState("");
  const [priority, setPriority] = useState("NORMAL");
  const [dueDate, setDueDate] = useState("");
  const [costImpact, setCostImpact] = useState(false);
  const [scheduleImpact, setScheduleImpact] = useState(false);
  const [assignedTo, setAssignedTo] = useState("");

  const handleSave = () => {
    // TODO: Wire to API via useCreateRFI hook
    console.log({
      subject,
      question,
      priority,
      due_date: dueDate || undefined,
      cost_impact: costImpact,
      schedule_impact: scheduleImpact,
      assigned_to: assignedTo || undefined,
    });
    router.push(`/app/projects/${projectId}/rfis`);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push(`/app/projects/${projectId}/rfis`)}
            className="p-1 rounded hover:bg-gray-200"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">New RFI</h1>
            <p className="text-sm text-gray-500">Submit a request for information</p>
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
            onClick={handleSave}
            disabled={!subject.trim() || !question.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-[#1B2A4A] rounded-lg hover:bg-[#243558] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Create RFI
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-4">RFI Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Subject *</label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Brief description of the request..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Question *</label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={6}
                  placeholder="Provide full detail of your question or request..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Settings</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Assigned To</label>
                <select
                  value={assignedTo}
                  onChange={(e) => setAssignedTo(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                >
                  <option value="">Select assignee...</option>
                  <option value="u1">John Smith</option>
                  <option value="u2">Sarah Johnson</option>
                  <option value="u3">Mike Chen</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Due Date</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20"
                />
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Impact</h2>
            <div className="space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={costImpact}
                  onChange={(e) => setCostImpact(e.target.checked)}
                  className="rounded border-gray-300 text-[#1B2A4A] focus:ring-[#1B2A4A]"
                />
                <span className="text-sm text-gray-700">Cost Impact</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={scheduleImpact}
                  onChange={(e) => setScheduleImpact(e.target.checked)}
                  className="rounded border-gray-300 text-[#1B2A4A] focus:ring-[#1B2A4A]"
                />
                <span className="text-sm text-gray-700">Schedule Impact</span>
              </label>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
