import Link from "next/link";

const features = [
  {
    title: "Pre-Construction to Closeout",
    description:
      "Manage every phase from bidding through project closeout in one platform.",
  },
  {
    title: "Owner & Sub Portals",
    description:
      "Give owners and subs their own dedicated views with controlled access.",
  },
  {
    title: "Real-Time Financial Tracking",
    description:
      "Budget tracking, change orders, and pay applications with real-time visibility.",
  },
];

const pricingTiers = [
  {
    name: "Starter",
    price: "$349",
    period: "/mo",
    projects: "3 major projects",
    billing: "Month-to-month",
    cta: "Start with Starter",
    tier: "STARTER",
    popular: false,
  },
  {
    name: "Professional",
    price: "$2,500",
    period: "/mo",
    projects: "10 major projects",
    billing: "Annual billing available",
    cta: "Start with Professional",
    tier: "PROFESSIONAL",
    popular: true,
  },
  {
    name: "Scale",
    price: "$4,500",
    period: "/mo",
    projects: "25 major projects",
    billing: "Annual billing available",
    cta: "Start with Scale",
    tier: "SCALE",
    popular: false,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    projects: "Unlimited projects",
    billing: "Custom terms",
    cta: "Contact Sales",
    tier: "ENTERPRISE",
    popular: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Nav */}
      <nav className="border-b border-gray-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-primary">
            Conflo
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-gray-700 hover:text-primary transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-sm font-medium text-white bg-accent hover:bg-accent/90 px-4 py-2 rounded-lg transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="bg-primary text-white py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-6">
            Construction Project Management,
            <br />
            Built for General Contractors
          </h1>
          <p className="text-lg sm:text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
            Manage bids, budgets, daily logs, RFIs, and everything in between.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup"
              className="inline-block bg-accent hover:bg-accent/90 text-white font-semibold px-8 py-3 rounded-lg text-lg transition-colors"
            >
              Start Free Trial
            </Link>
            <Link
              href="/login"
              className="inline-block border border-white/30 hover:border-white/60 text-white font-semibold px-8 py-3 rounded-lg text-lg transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-primary text-center mb-12">
            Everything You Need to Run Your Projects
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <h3 className="text-xl font-semibold text-primary mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-primary text-center mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Choose the plan that fits your business. Scale up as you grow.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {pricingTiers.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-xl p-6 border flex flex-col ${
                  tier.popular
                    ? "border-accent ring-2 ring-accent/20 shadow-lg relative"
                    : "border-gray-200 shadow-sm"
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
                <p className="text-sm text-gray-500 mb-6">{tier.billing}</p>
                <div className="mt-auto">
                  <Link
                    href={`/signup?tier=${tier.tier}`}
                    className={`block text-center font-medium py-2.5 px-4 rounded-lg transition-colors ${
                      tier.popular
                        ? "bg-accent text-white hover:bg-accent/90"
                        : "bg-primary text-white hover:bg-primary/90"
                    }`}
                  >
                    {tier.cta}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8 px-4 bg-white">
        <p className="text-center text-sm text-gray-500">
          &copy; 2026 Conflo
        </p>
      </footer>
    </div>
  );
}
