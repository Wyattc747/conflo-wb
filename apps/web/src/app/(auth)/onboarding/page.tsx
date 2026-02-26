"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CompanyData {
  name: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  zip_code: string;
  phone: string;
  license_number: string;
}

interface ProfileData {
  name: string;
  phone: string;
  title: string;
}

interface ProjectData {
  name: string;
  project_number: string;
  address: string;
  project_type: string;
  contract_value: string;
  phase: string;
}

interface TeamMember {
  email: string;
  permission_level: string;
}

interface SubInvite {
  company_name: string;
  contact_email: string;
  trade: string;
}

const STEP_LABELS = [
  "Welcome",
  "Company",
  "Profile",
  "Cost Codes",
  "Project",
  "Team",
  "Subs",
  "All Set!",
];

const PROJECT_TYPES = [
  "COMMERCIAL",
  "INSTITUTIONAL",
  "HEALTHCARE",
  "EDUCATION",
  "INDUSTRIAL",
  "RESIDENTIAL_MULTI",
  "MIXED_USE",
  "OTHER",
];

const PERMISSION_LEVELS = [
  "OWNER_ADMIN",
  "PRE_CONSTRUCTION",
  "MANAGEMENT",
  "USER",
];

const TRADES = [
  "General Conditions",
  "Demolition",
  "Earthwork",
  "Paving",
  "Landscaping",
  "Utilities",
  "Concrete",
  "Masonry",
  "Metals",
  "Carpentry",
  "Thermal/Moisture Protection",
  "Doors/Windows",
  "Finishes",
  "Specialties",
  "Equipment",
  "Furnishings",
  "Special Construction",
  "Conveying Systems",
  "Fire Protection",
  "Plumbing",
  "HVAC",
  "Electrical",
  "Low Voltage",
  "Electronic Safety/Security",
  "Other",
];

// ---------------------------------------------------------------------------
// Shared UI helpers
// ---------------------------------------------------------------------------

function InputField({
  label,
  id,
  type = "text",
  required = false,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  id: string;
  type?: string;
  required?: boolean;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        required={required}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
      />
    </div>
  );
}

function StepShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-primary mb-1">{title}</h2>
      {subtitle && <p className="text-gray-600 mb-6">{subtitle}</p>}
      {!subtitle && <div className="mb-6" />}
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step components
// ---------------------------------------------------------------------------

function StepWelcome({ onNext }: { onNext: () => void }) {
  return (
    <StepShell title="Welcome to Conflo!">
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-accent mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.745 3.745 0 011.043 3.296A3.745 3.745 0 0121 12z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-primary mb-2">
          Your plan is active.
        </h3>
        <p className="text-gray-600 mb-8">
          Let&apos;s set up your account in a few quick steps so you can hit the ground running.
        </p>
        <button
          onClick={onNext}
          className="bg-accent hover:bg-accent/90 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Let&apos;s Set Up Your Account
        </button>
      </div>
    </StepShell>
  );
}

function StepCompany({
  data,
  setData,
  onNext,
  loading,
}: {
  data: CompanyData;
  setData: (d: CompanyData) => void;
  onNext: () => void;
  loading: boolean;
}) {
  const update = (field: keyof CompanyData) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setData({ ...data, [field]: e.target.value });

  return (
    <StepShell title="Company Profile" subtitle="Tell us about your company.">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onNext();
        }}
        className="space-y-4"
      >
        <InputField label="Company Name" id="company_name" required value={data.name} onChange={update("name")} />
        <InputField label="Address Line 1" id="address_line1" required value={data.address_line1} onChange={update("address_line1")} />
        <InputField label="Address Line 2" id="address_line2" value={data.address_line2} onChange={update("address_line2")} />
        <div className="grid grid-cols-3 gap-4">
          <InputField label="City" id="city" required value={data.city} onChange={update("city")} />
          <InputField label="State" id="state" required value={data.state} onChange={update("state")} />
          <InputField label="ZIP Code" id="zip_code" required value={data.zip_code} onChange={update("zip_code")} />
        </div>
        <InputField label="Phone" id="phone" type="tel" value={data.phone} onChange={update("phone")} />
        <InputField label="License Number (optional)" id="license_number" value={data.license_number} onChange={update("license_number")} />
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Saving..." : "Next"}
          </button>
        </div>
      </form>
    </StepShell>
  );
}

function StepProfile({
  data,
  setData,
  onNext,
  loading,
}: {
  data: ProfileData;
  setData: (d: ProfileData) => void;
  onNext: () => void;
  loading: boolean;
}) {
  const update = (field: keyof ProfileData) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setData({ ...data, [field]: e.target.value });

  return (
    <StepShell title="Your Profile" subtitle="Set up your personal info.">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onNext();
        }}
        className="space-y-4"
      >
        <InputField label="Full Name" id="profile_name" required value={data.name} onChange={update("name")} />
        <InputField label="Phone" id="profile_phone" type="tel" value={data.phone} onChange={update("phone")} />
        <InputField label="Title" id="profile_title" value={data.title} onChange={update("title")} placeholder="e.g. Project Manager" />
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Saving..." : "Next"}
          </button>
        </div>
      </form>
    </StepShell>
  );
}

function StepCostCodes({
  onNext,
  loading,
}: {
  onNext: (choice: string) => void;
  loading: boolean;
}) {
  return (
    <StepShell title="Cost Codes" subtitle="How would you like to organize your cost codes?">
      <div className="space-y-4">
        <button
          onClick={() => onNext("CSI_MASTERFORMAT")}
          disabled={loading}
          className="w-full text-left bg-white border-2 border-accent rounded-xl p-5 hover:bg-accent/5 transition-colors disabled:opacity-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-primary">CSI MasterFormat</h3>
              <p className="text-sm text-gray-600 mt-1">Industry-standard 50-division system. Recommended for most GCs.</p>
            </div>
            <span className="text-xs bg-accent/10 text-accent font-medium px-2.5 py-1 rounded-full">Recommended</span>
          </div>
        </button>
        <button
          onClick={() => onNext("CUSTOM")}
          disabled={loading}
          className="w-full text-left bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-300 transition-colors disabled:opacity-50"
        >
          <h3 className="font-semibold text-primary">Custom Cost Codes</h3>
          <p className="text-sm text-gray-600 mt-1">Set up your own cost code structure later in settings.</p>
        </button>
        <button
          onClick={() => onNext("SKIP")}
          disabled={loading}
          className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-2 transition-colors disabled:opacity-50"
        >
          Skip for now
        </button>
      </div>
    </StepShell>
  );
}

function StepProject({
  data,
  setData,
  onNext,
  onSkip,
  loading,
}: {
  data: ProjectData;
  setData: (d: ProjectData) => void;
  onNext: () => void;
  onSkip: () => void;
  loading: boolean;
}) {
  const update = (field: keyof ProjectData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setData({ ...data, [field]: e.target.value });

  return (
    <StepShell title="Your First Project" subtitle="Create your first project to get started.">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onNext();
        }}
        className="space-y-4"
      >
        <InputField label="Project Name" id="project_name" required value={data.name} onChange={update("name") as any} />
        <InputField label="Project Number (optional)" id="project_number" value={data.project_number} onChange={update("project_number") as any} />
        <InputField label="Address" id="project_address" value={data.address} onChange={update("address") as any} />

        <div>
          <label htmlFor="project_type" className="block text-sm font-medium text-gray-700 mb-1">
            Project Type
          </label>
          <select
            id="project_type"
            value={data.project_type}
            onChange={update("project_type") as any}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent bg-white"
          >
            <option value="">Select type...</option>
            {PROJECT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        <InputField
          label="Contract Value"
          id="contract_value"
          type="number"
          value={data.contract_value}
          onChange={update("contract_value") as any}
          placeholder="e.g. 1500000"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Phase</label>
          <div className="flex gap-4">
            {(["BIDDING", "ACTIVE"] as const).map((phase) => (
              <label key={phase} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="phase"
                  value={phase}
                  checked={data.phase === phase}
                  onChange={update("phase") as any}
                  className="text-accent focus:ring-accent"
                />
                <span className="text-sm text-gray-700">
                  {phase.charAt(0) + phase.slice(1).toLowerCase()}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-2 space-y-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Project & Continue"}
          </button>
          <button
            type="button"
            onClick={onSkip}
            className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-2 transition-colors"
          >
            I&apos;ll add a project later
          </button>
        </div>
      </form>
    </StepShell>
  );
}

function StepInviteTeam({
  members,
  setMembers,
  onNext,
  onSkip,
  loading,
}: {
  members: TeamMember[];
  setMembers: (m: TeamMember[]) => void;
  onNext: () => void;
  onSkip: () => void;
  loading: boolean;
}) {
  const addRow = () => setMembers([...members, { email: "", permission_level: "USER" }]);
  const updateRow = (idx: number, field: keyof TeamMember, value: string) => {
    const updated = [...members];
    updated[idx] = { ...updated[idx], [field]: value };
    setMembers(updated);
  };
  const removeRow = (idx: number) => setMembers(members.filter((_, i) => i !== idx));

  return (
    <StepShell title="Invite Your Team" subtitle="Add team members to your organization.">
      <div className="space-y-3 mb-4">
        {members.map((m, idx) => (
          <div key={idx} className="flex gap-3 items-start">
            <div className="flex-1">
              <input
                type="email"
                placeholder="email@company.com"
                value={m.email}
                onChange={(e) => updateRow(idx, "email", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>
            <div className="w-44">
              <select
                value={m.permission_level}
                onChange={(e) => updateRow(idx, "permission_level", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent bg-white"
              >
                {PERMISSION_LEVELS.map((p) => (
                  <option key={p} value={p}>
                    {p.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            {members.length > 1 && (
              <button
                type="button"
                onClick={() => removeRow(idx)}
                className="text-gray-400 hover:text-red-500 p-2 transition-colors"
                aria-label="Remove"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={addRow}
        className="text-sm text-accent hover:text-accent/80 font-medium mb-6 transition-colors"
      >
        + Add another
      </button>
      <div className="space-y-2">
        <button
          onClick={onNext}
          disabled={loading}
          className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Sending invites..." : "Send Invites & Continue"}
        </button>
        <button
          onClick={onSkip}
          className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-2 transition-colors"
        >
          I&apos;ll do this later
        </button>
      </div>
    </StepShell>
  );
}

function StepInviteSubs({
  subs,
  setSubs,
  onNext,
  onSkip,
  loading,
  projectCreated,
}: {
  subs: SubInvite[];
  setSubs: (s: SubInvite[]) => void;
  onNext: () => void;
  onSkip: () => void;
  loading: boolean;
  projectCreated: boolean;
}) {
  if (!projectCreated) {
    return (
      <StepShell title="Invite Subcontractors" subtitle="You can invite subs after creating a project.">
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <p className="text-gray-600 mb-6">
            Since you skipped creating a project, you can invite subcontractors later from your project settings.
          </p>
          <button
            onClick={onSkip}
            className="bg-accent hover:bg-accent/90 text-white font-semibold px-8 py-2.5 rounded-lg transition-colors"
          >
            Continue
          </button>
        </div>
      </StepShell>
    );
  }

  const addRow = () => setSubs([...subs, { company_name: "", contact_email: "", trade: "" }]);
  const updateRow = (idx: number, field: keyof SubInvite, value: string) => {
    const updated = [...subs];
    updated[idx] = { ...updated[idx], [field]: value };
    setSubs(updated);
  };
  const removeRow = (idx: number) => setSubs(subs.filter((_, i) => i !== idx));

  return (
    <StepShell title="Invite Subcontractors" subtitle="Invite subs to your first project.">
      <div className="space-y-3 mb-4">
        {subs.map((s, idx) => (
          <div key={idx} className="flex gap-3 items-start">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Company name"
                value={s.company_name}
                onChange={(e) => updateRow(idx, "company_name", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>
            <div className="flex-1">
              <input
                type="email"
                placeholder="contact@sub.com"
                value={s.contact_email}
                onChange={(e) => updateRow(idx, "contact_email", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>
            <div className="w-40">
              <select
                value={s.trade}
                onChange={(e) => updateRow(idx, "trade", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent bg-white"
              >
                <option value="">Trade...</option>
                {TRADES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            {subs.length > 1 && (
              <button
                type="button"
                onClick={() => removeRow(idx)}
                className="text-gray-400 hover:text-red-500 p-2 transition-colors"
                aria-label="Remove"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={addRow}
        className="text-sm text-accent hover:text-accent/80 font-medium mb-6 transition-colors"
      >
        + Add another
      </button>
      <div className="space-y-2">
        <button
          onClick={onNext}
          disabled={loading}
          className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Sending invites..." : "Send Invites & Continue"}
        </button>
        <button
          onClick={onSkip}
          className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-2 transition-colors"
        >
          I&apos;ll do this later
        </button>
      </div>
    </StepShell>
  );
}

function StepComplete({ onFinish }: { onFinish: () => void }) {
  return (
    <StepShell title="You're All Set!">
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-green-500 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-primary mb-2">
          Your account is ready!
        </h3>
        <p className="text-gray-600 mb-8">
          Your organization, profile, and settings have been configured. You can always update these in your settings later.
        </p>
        <button
          onClick={onFinish}
          className="bg-accent hover:bg-accent/90 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    </StepShell>
  );
}

// ---------------------------------------------------------------------------
// Progress bar
// ---------------------------------------------------------------------------

function ProgressBar({ currentStep }: { currentStep: number }) {
  return (
    <div className="max-w-3xl mx-auto mb-10">
      <div className="flex items-center justify-between mb-2">
        {STEP_LABELS.map((label, idx) => {
          const isActive = idx === currentStep;
          const isComplete = idx < currentStep;
          return (
            <div key={label} className="flex flex-col items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                  isComplete
                    ? "bg-accent text-white"
                    : isActive
                      ? "bg-accent text-white ring-4 ring-accent/20"
                      : "bg-gray-200 text-gray-500"
                }`}
              >
                {isComplete ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`text-xs mt-1 hidden sm:block ${
                  isActive ? "text-accent font-medium" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
      <div className="relative h-1 bg-gray-200 rounded-full mt-1">
        <div
          className="absolute top-0 left-0 h-1 bg-accent rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / (STEP_LABELS.length - 1)) * 100}%` }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main onboarding page
// ---------------------------------------------------------------------------

export default function OnboardingPage() {
  const { getToken } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projectCreated, setProjectCreated] = useState(false);

  // Step data
  const [company, setCompany] = useState<CompanyData>({
    name: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
    license_number: "",
  });
  const [profile, setProfile] = useState<ProfileData>({ name: "", phone: "", title: "" });
  const [project, setProject] = useState<ProjectData>({
    name: "",
    project_number: "",
    address: "",
    project_type: "",
    contract_value: "",
    phase: "ACTIVE",
  });
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { email: "", permission_level: "USER" },
  ]);
  const [subInvites, setSubInvites] = useState<SubInvite[]>([
    { company_name: "", contact_email: "", trade: "" },
  ]);

  const apiCall = useCallback(
    async (path: string, body: any) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return fetchWithAuth(path, token, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    [getToken]
  );

  const nextStep = () => {
    setError("");
    setStep((s) => s + 1);
  };

  // Step handlers
  const handleCompany = async () => {
    setLoading(true);
    setError("");
    try {
      await apiCall("/api/gc/onboarding/company", company);
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProfile = async () => {
    setLoading(true);
    setError("");
    try {
      await apiCall("/api/gc/onboarding/profile", profile);
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCostCodes = async (choice: string) => {
    setLoading(true);
    setError("");
    try {
      await apiCall("/api/gc/onboarding/cost-codes", { template: choice });
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProject = async () => {
    setLoading(true);
    setError("");
    try {
      const payload: any = { ...project };
      if (payload.contract_value) {
        payload.contract_value = parseFloat(payload.contract_value);
      } else {
        delete payload.contract_value;
      }
      await apiCall("/api/gc/onboarding/project", payload);
      setProjectCreated(true);
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipProject = () => {
    setProjectCreated(false);
    nextStep();
  };

  const handleInviteTeam = async () => {
    const validMembers = teamMembers.filter((m) => m.email.trim());
    if (validMembers.length === 0) {
      nextStep();
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiCall("/api/gc/onboarding/invite-team", { members: validMembers });
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteSubs = async () => {
    const validSubs = subInvites.filter((s) => s.contact_email.trim());
    if (validSubs.length === 0) {
      nextStep();
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiCall("/api/gc/onboarding/invite-subs", { subs: validSubs });
      nextStep();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Mark onboarding complete when reaching final step
  useEffect(() => {
    if (step === 7) {
      (async () => {
        try {
          const token = await getToken();
          if (token) {
            await fetchWithAuth("/api/gc/onboarding/complete", token, {
              method: "POST",
              body: JSON.stringify({}),
            });
          }
        } catch {
          // Non-blocking -- dashboard will still work
        }
      })();
    }
  }, [step, getToken]);

  const handleFinish = () => {
    router.push("/app/dashboard");
  };

  return (
    <div className="py-10 px-4">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-primary">Conflo</h1>
      </div>

      {/* Progress */}
      <ProgressBar currentStep={step} />

      {/* Error banner */}
      {error && (
        <div className="max-w-2xl mx-auto mb-6">
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
            {error}
          </div>
        </div>
      )}

      {/* Step content */}
      {step === 0 && <StepWelcome onNext={nextStep} />}
      {step === 1 && <StepCompany data={company} setData={setCompany} onNext={handleCompany} loading={loading} />}
      {step === 2 && <StepProfile data={profile} setData={setProfile} onNext={handleProfile} loading={loading} />}
      {step === 3 && <StepCostCodes onNext={handleCostCodes} loading={loading} />}
      {step === 4 && (
        <StepProject data={project} setData={setProject} onNext={handleProject} onSkip={handleSkipProject} loading={loading} />
      )}
      {step === 5 && (
        <StepInviteTeam members={teamMembers} setMembers={setTeamMembers} onNext={handleInviteTeam} onSkip={nextStep} loading={loading} />
      )}
      {step === 6 && (
        <StepInviteSubs
          subs={subInvites}
          setSubs={setSubInvites}
          onNext={handleInviteSubs}
          onSkip={nextStep}
          loading={loading}
          projectCreated={projectCreated}
        />
      )}
      {step === 7 && <StepComplete onFinish={handleFinish} />}
    </div>
  );
}
