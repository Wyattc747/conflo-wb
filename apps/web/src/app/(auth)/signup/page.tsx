"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, Suspense } from "react";
import Link from "next/link";

const pricingTiers = [
  {
    name: "Starter",
    price: "$349",
    period: "/mo",
    projects: "3 major projects",
    billing: "Month-to-month",
    tier: "STARTER",
    popular: false,
  },
  {
    name: "Professional",
    price: "$2,500",
    period: "/mo",
    projects: "10 major projects",
    billing: "Annual billing available",
    tier: "PROFESSIONAL",
    popular: true,
  },
  {
    name: "Scale",
    price: "$4,500",
    period: "/mo",
    projects: "25 major projects",
    billing: "Annual billing available",
    tier: "SCALE",
    popular: false,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    projects: "Unlimited projects",
    billing: "Custom terms",
    tier: "ENTERPRISE",
    popular: false,
  },
];

function SignupForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTier = searchParams.get("tier") || "";

  const [selectedTier, setSelectedTier] = useState(initialTier);
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    company_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/signup`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...formData,
            tier: selectedTier,
          }),
        }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(
          errData?.detail || errData?.error?.message || "Signup failed"
        );
      }

      const data = await res.json();

      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        router.push("/onboarding");
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Select a tier
  if (!selectedTier) {
    return (
      <div className="w-full max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-primary text-center mb-2">
          Choose Your Plan
        </h1>
        <p className="text-gray-600 text-center mb-10">
          Select a plan to get started with Conflo.
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {pricingTiers.map((tier) => (
            <button
              key={tier.tier}
              onClick={() => setSelectedTier(tier.tier)}
              className={`rounded-xl p-6 border text-left flex flex-col transition-all hover:shadow-md ${
                tier.popular
                  ? "border-accent ring-2 ring-accent/20 shadow-lg relative"
                  : "border-gray-200 shadow-sm hover:border-accent/50"
              }`}
            >
              {tier.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-white text-xs font-semibold px-3 py-1 rounded-full">
                  Most Popular
                </span>
              )}
              <h3 className="text-lg font-semibold text-primary mb-2">
                {tier.name}
              </h3>
              <div className="mb-4">
                <span className="text-3xl font-bold text-primary">
                  {tier.price}
                </span>
                <span className="text-gray-500">{tier.period}</span>
              </div>
              <p className="text-sm text-gray-700 font-medium mb-1">
                {tier.projects}
              </p>
              <p className="text-sm text-gray-500 mb-4">{tier.billing}</p>
              <span className="mt-auto block text-center bg-primary text-white font-medium py-2 px-4 rounded-lg">
                Select {tier.name}
              </span>
            </button>
          ))}
        </div>
        <p className="text-center mt-8 text-sm text-gray-500">
          Already have an account?{" "}
          <Link href="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  // Step 2: Signup form
  const selectedTierInfo = pricingTiers.find((t) => t.tier === selectedTier);

  return (
    <div className="w-full max-w-md mx-auto">
      <h1 className="text-3xl font-bold text-primary text-center mb-2">
        Create Your Account
      </h1>
      {selectedTierInfo && (
        <p className="text-center text-gray-600 mb-8">
          {selectedTierInfo.name} Plan &mdash; {selectedTierInfo.price}
          {selectedTierInfo.period}
          <button
            onClick={() => setSelectedTier("")}
            className="ml-2 text-accent hover:underline text-sm"
          >
            Change plan
          </button>
        </p>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-6 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            placeholder="you@company.com"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="first_name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              First Name
            </label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              required
              value={formData.first_name}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            />
          </div>
          <div>
            <label
              htmlFor="last_name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Last Name
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              required
              value={formData.last_name}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="company_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Company Name
          </label>
          <input
            id="company_name"
            name="company_name"
            type="text"
            required
            value={formData.company_name}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating account..." : "Create Account"}
        </button>
      </form>

      <p className="text-center mt-6 text-sm text-gray-500">
        Already have an account?{" "}
        <Link href="/login" className="text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
        </div>
      }
    >
      <SignupForm />
    </Suspense>
  );
}
