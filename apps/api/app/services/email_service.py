from app.config import settings


async def send_invite_email(
    invitation, inviter_name: str, organization_name: str
):
    """Send invitation email using Resend API."""
    import resend

    resend.api_key = settings.RESEND_API_KEY

    invite_url = f"{settings.FRONTEND_URL}/invite/{invitation.token}"

    subject_map = {
        "gc_user": f"You've been invited to join {organization_name} on Conflo",
        "sub_user": f"{organization_name} has invited you to Conflo",
        "owner_user": f"{organization_name} has shared project access on Conflo",
    }

    html = render_invite_html(
        invitation.invite_type, inviter_name, organization_name, invite_url
    )

    if not settings.RESEND_API_KEY:
        return  # Skip in dev/test

    resend.Emails.send(
        {
            "from": "Conflo <noreply@conflo.app>",
            "to": invitation.email,
            "subject": subject_map.get(
                invitation.invite_type, "You've been invited to Conflo"
            ),
            "html": html,
        }
    )


def render_invite_html(
    invite_type: str,
    inviter_name: str,
    organization_name: str,
    invite_url: str,
) -> str:
    """Render invitation email HTML."""
    body_map = {
        "gc_user": (
            f"<strong>{inviter_name}</strong> has invited you to join "
            f"<strong>{organization_name}</strong> on Conflo, a construction "
            f"management platform built for general contractors."
        ),
        "sub_user": (
            f"<strong>{organization_name}</strong> has invited you to collaborate "
            f"on Conflo as a subcontractor partner. Accept the invitation below "
            f"to get started."
        ),
        "owner_user": (
            f"<strong>{organization_name}</strong> has shared project access with "
            f"you on Conflo. Accept the invitation below to view project details "
            f"and stay up to date."
        ),
    }

    body_text = body_map.get(
        invite_type,
        f"<strong>{inviter_name}</strong> has invited you to join Conflo.",
    )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Conflo Invitation</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="padding:32px 40px 24px 40px;border-bottom:1px solid #e5e7eb;">
              <span style="font-size:28px;font-weight:700;color:#1B2A4A;letter-spacing:-0.5px;">Conflo</span>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              <p style="margin:0 0 16px 0;font-size:16px;line-height:1.5;color:#374151;">
                Hi there,
              </p>
              <p style="margin:0 0 24px 0;font-size:16px;line-height:1.5;color:#374151;">
                {body_text}
              </p>
              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px 0;">
                <tr>
                  <td style="border-radius:6px;background-color:#2563EB;">
                    <a href="{invite_url}"
                       target="_blank"
                       style="display:inline-block;padding:14px 32px;font-size:16px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:6px;">
                      Accept Invitation
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 8px 0;font-size:14px;line-height:1.5;color:#6b7280;">
                This invitation expires in 14 days.
              </p>
              <p style="margin:0;font-size:14px;line-height:1.5;color:#6b7280;">
                If you didn't expect this invitation, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;border-top:1px solid #e5e7eb;background-color:#f9fafb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                &copy; 2026 Conflo. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
