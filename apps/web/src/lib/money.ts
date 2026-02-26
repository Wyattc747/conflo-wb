/**
 * All API amounts are in cents (integer). These utils format for display.
 */

/** Format cents to dollar string: 1234567 → "$12,345.67" */
export function formatMoney(cents: number | null | undefined): string {
  if (cents == null) return "$0.00";
  const dollars = cents / 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(dollars);
}

/** Format cents to compact: 1234567 → "$12.3K" */
export function formatMoneyCompact(cents: number | null | undefined): string {
  if (cents == null) return "$0";
  const dollars = cents / 100;
  if (Math.abs(dollars) >= 1_000_000) {
    return `$${(dollars / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(dollars) >= 1_000) {
    return `$${(dollars / 1_000).toFixed(1)}K`;
  }
  return formatMoney(cents);
}

/** Convert dollar input (string or number) to cents for API */
export function toCents(dollars: string | number): number {
  const num = typeof dollars === "string" ? parseFloat(dollars) : dollars;
  if (isNaN(num)) return 0;
  return Math.round(num * 100);
}

/** Convert cents to dollar number for form inputs */
export function toDollars(cents: number | null | undefined): number {
  if (cents == null) return 0;
  return cents / 100;
}

/** Format percentage: 10.5 → "10.50%" */
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return "0.00%";
  return `${value.toFixed(2)}%`;
}
