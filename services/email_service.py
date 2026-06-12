# backend/services/email_service.py
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from config.settings import Config


class EmailService:
    """Sends transactional emails via Brevo (formerly Sendinblue)."""

    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = Config.BREVO_API_KEY
        self._client = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        self._sender = {
            'name': Config.BREVO_SENDER_NAME,
            'email': Config.BREVO_SENDER_EMAIL,
        }

    def send_verification_email(self, to_email: str, to_name: str, otp: str) -> bool:
        subject = 'Verify your Talent Bridge account'
        html = self._otp_template(
            title='Email Verification',
            greeting=f'Welcome, {to_name}!',
            intro='Thank you for creating a Talent Bridge account. '
                  'Enter the code below to verify your email address.',
            otp=otp,
            footer="This code expires in 10 minutes. If you didn't create an account, you can safely ignore this email.",
        )
        return self._send(to_email, to_name, subject, html)

    def send_password_reset_email(self, to_email: str, to_name: str, otp: str) -> bool:
        subject = 'Reset your Talent Bridge password'
        html = self._otp_template(
            title='Password Reset',
            greeting=f'Hello, {to_name}!',
            intro='We received a request to reset your password. '
                  'Use the code below to set a new password.',
            otp=otp,
            footer="This code expires in 10 minutes. If you didn't request a password reset, please ignore this email.",
        )
        return self._send(to_email, to_name, subject, html)

    def send_welcome_email(self, to_email: str, to_name: str) -> bool:
        subject = f'Welcome to Talent Bridge, {to_name}!'
        html = (
            self._base_html_open()
            + f"""
            <h2 style="color:#1FA2FF;margin:0 0 16px;">Welcome aboard, {to_name}!</h2>
            <p style="color:#555;line-height:1.7;margin:0 0 20px;">
              Your account is now verified. You can now:
            </p>
            <ul style="color:#555;line-height:2;padding-left:20px;">
              <li>Chat with your <strong>AI Career Advisor</strong></li>
              <li>Browse <strong>job opportunities</strong></li>
              <li>Connect with the <strong>professional community</strong></li>
              <li>Explore <strong>startup ideas</strong></li>
            </ul>
            """
            + self._base_html_close()
        )
        return self._send(to_email, to_name, subject, html)

    def _send(self, to_email: str, to_name: str, subject: str, html: str) -> bool:
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=self._sender,
                to=[{'email': to_email, 'name': to_name}],
                subject=subject,
                html_content=html,
            )
            self._client.send_transac_email(send_smtp_email)
            return True
        except ApiException as e:
            print(f'[Brevo] Error sending email to {to_email}: {e}')
            return False
        except Exception as e:
            print(f'[Brevo] Unexpected error: {e}')
            return False

    @staticmethod
    def _otp_template(title, greeting, intro, otp, footer):
        digits = ''.join(
            f'<span style="display:inline-block;width:44px;height:52px;line-height:52px;'
            f'text-align:center;font-size:26px;font-weight:800;color:#1FA2FF;'
            f'background:#EEF6FF;border-radius:10px;margin:0 4px;">{d}</span>'
            for d in otp
        )
        return (
            EmailService._base_html_open()
            + f"""
            <h2 style="color:#1FA2FF;margin:0 0 8px;">{title}</h2>
            <p style="color:#333;font-weight:600;margin:0 0 12px;">{greeting}</p>
            <p style="color:#555;line-height:1.7;margin:0 0 28px;">{intro}</p>
            <div style="text-align:center;margin:0 0 28px;">{digits}</div>
            <p style="color:#999;font-size:13px;line-height:1.6;border-top:1px solid #eee;
               padding-top:20px;">{footer}</p>
            """
            + EmailService._base_html_close()
        )

    @staticmethod
    def _base_html_open():
        return """<!DOCTYPE html><html><body style="margin:0;padding:0;background:#F5F7FA;
        font-family:'Segoe UI',sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:20px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,.08);">
          <tr>
            <td style="background:linear-gradient(135deg,#1FA2FF,#12D8FA,#1FD1A5);
                        padding:32px;text-align:center;">
              <span style="font-size:28px;font-weight:800;color:#fff;
                            letter-spacing:-0.5px;">Talent Bridge</span>
            </td>
          </tr>
          <tr><td style="padding:40px 48px;">"""

    @staticmethod
    def _base_html_close():
        return """</td></tr>
          <tr><td style="background:#F5F7FA;padding:20px;text-align:center;">
            <p style="color:#bbb;font-size:12px;margin:0;">
              &copy; 2025 Talent Bridge &middot; All rights reserved
            </p>
          </td></tr>
        </table></td></tr></table></body></html>"""


email_service = EmailService()
