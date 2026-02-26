"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface InvitationData {
  org_name: string;
  role: string;
  invite_type: string;
  projects?: { id: string; name: string }[];
  email: string;
}

export default function InviteAcceptPage() {
  const params = useParams();
  const token = params.token as string;

  const [invitation, setInvitation] = useState<InvitationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchInvitation() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/invitations/${token}`
        );

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(
            errData?.detail || "This invitation is invalid or has expired."
          );
        }

        const data = await res.json();
        setInvitation(data);
      } catch (err: any) {
        setError(
          err.message || "Unable to load invitation. It may have expired."
        );
      } finally {
        setLoading(false);
      }
    }

    fetchInvitation();
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-md mx-auto text-center">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="text-red-500 mb-4">
            <svg
              className="w-12 h-12 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-primary mb-2">
            Invalid Invitation
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            href="/"
            className="inline-block bg-primary text-white font-medium py-2 px-6 rounded-lg hover:bg-primary/90 transition-colors"
          >
            Go to Homepage
          </Link>
        </div>
      </div>
    );
  }

  if (!invitation) return null;

  const roleLabel = invitation.role
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="text-accent mb-4">
          <svg
            className="w-12 h-12 mx-auto"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-primary mb-2">
          You&apos;ve Been Invited!
        </h1>
        <p className="text-gray-600 mb-6">
          <span className="font-semibold text-primary">
            {invitation.org_name}
          </span>{" "}
          has invited you to join Conflo as a{" "}
          <span className="font-semibold text-primary">{roleLabel}</span>.
        </p>

        {invitation.projects && invitation.projects.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm font-medium text-gray-700 mb-2">
              You&apos;ll have access to:
            </p>
            <ul className="space-y-1">
              {invitation.projects.map((project) => (
                <li
                  key={project.id}
                  className="text-sm text-gray-600 flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />
                  {project.name}
                </li>
              ))}
            </ul>
          </div>
        )}

        <Link
          href={`/signup?invitation=${token}&email=${encodeURIComponent(invitation.email)}`}
          className="block w-full bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-4 rounded-lg transition-colors text-center"
        >
          Accept &amp; Sign Up
        </Link>

        <p className="text-sm text-gray-500 mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-accent hover:underline">
            Sign in
          </Link>{" "}
          to accept this invitation.
        </p>
      </div>
    </div>
  );
}
