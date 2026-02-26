class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, data: any) {
    super(data?.error?.message || data?.detail || "API Error");
    this.status = status;
    this.data = data;
  }
}

/**
 * Fetch with authentication via Clerk token.
 * Use in client components where you have access to useAuth().getToken().
 */
async function fetchWithAuth(
  path: string,
  token: string,
  options: RequestInit = {}
) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new ApiError(res.status, error);
  }

  return res.json();
}

/**
 * Fetch without authentication.
 * Use for public endpoints like signup and invitation lookups.
 */
async function fetchPublic(path: string, options: RequestInit = {}) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new ApiError(res.status, error);
  }

  return res.json();
}

export { fetchWithAuth, fetchPublic, ApiError };
