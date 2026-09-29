import logging
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from django.utils.formats import date_format, time_format

from .models import DatePlan, ACTIVITY_CHOICES

logger = logging.getLogger(__name__)

ACTIVITY_LABELS = dict(ACTIVITY_CHOICES)

ACTIVITY_EMOJIS = {
    "walk":   "🌸",
    "movie":  "🎬",
    "meal":   "🍽️",
    "game":   "🎮",
    "other":  "✨",
    "photos": "📸",
}

def _excitement_label(val: int) -> str:
    if val < 25:  return "Plutôt calme 😌"
    if val < 50:  return "Un peu excité 🙂"
    if val < 75:  return "Assez excité 😊"
    if val < 90:  return "Très excité 🥰"
    return "Absolument fou d'excitation 🤩"


def build_invitation_html(plan: DatePlan, recipient_name: str) -> str:
    user     = plan.user
    acts     = plan.activities.all()
    act_list = "".join(
        f'<li style="margin:6px 0;">{ACTIVITY_EMOJIS.get(a.activity,"💗")} {ACTIVITY_LABELS.get(a.activity, a.activity)}</li>'
        for a in acts
    ) or "<li>À définir ensemble 💕</li>"

    date_str = date_format(plan.date, "l j F Y").capitalize()
    time_str = time_format(plan.time, "H:i") if plan.time else "Heure à confirmer"
    loc_str  = escape(plan.location) if plan.location else "Lieu surprise 🗺️"
    username = escape(user.username)
    recipient_name = escape(recipient_name)
    exc_str  = f"{plan.excitement}% — {_excitement_label(plan.excitement)}"

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital@0;1&family=DM+Sans:wght@300;400&display=swap');
    body {{ margin:0; padding:0; background:#fff0f3; font-family:'DM Sans',sans-serif; }}
    .wrapper {{ max-width:560px; margin:40px auto; background:#fff; border-radius:24px; overflow:hidden; box-shadow:0 8px 40px rgba(255,42,78,.12); }}
    .header {{ background:linear-gradient(135deg,#ff2a4e,#ff94b0); padding:48px 40px 36px; text-align:center; }}
    .header h1 {{ font-family:'Playfair Display',serif; color:#fff; font-size:36px; margin:0; letter-spacing:-.5px; }}
    .header p {{ color:rgba(255,255,255,.85); font-size:15px; margin:8px 0 0; }}
    .heart {{ font-size:52px; display:block; margin-bottom:12px; }}
    .body {{ padding:40px; }}
    .greeting {{ font-family:'Playfair Display',serif; font-size:22px; color:#ff2a4e; font-style:italic; margin-bottom:20px; }}
    .card {{ background:#fff0f3; border-radius:16px; padding:24px 28px; margin-bottom:20px; }}
    .card-title {{ font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#ffb3c1; font-weight:600; margin-bottom:8px; }}
    .card-value {{ font-family:'Playfair Display',serif; font-size:20px; color:#cc0033; }}
    .activities {{ list-style:none; padding:0; margin:8px 0 0; }}
    .activities li {{ font-size:15px; color:#cc0033; }}
    .excitement-bar {{ height:8px; border-radius:999px; background:linear-gradient(to right,#ff2a4e,#ff94b0); margin-top:8px; }}
    .footer {{ background:#fff8f9; padding:24px 40px; text-align:center; border-top:1px solid #ffe0e8; }}
    .footer p {{ font-size:13px; color:#ffb3c1; margin:4px 0; }}
    .badge {{ display:inline-block; background:#ff2a4e; color:#fff; border-radius:999px; padding:4px 14px; font-size:12px; margin-top:12px; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <span class="heart">💗</span>
      <h1>Sweet Date</h1>
      <p>Une invitation romantique rien que pour vous</p>
    </div>
    <div class="body">
      <p class="greeting">Bonjour {recipient_name} !</p>
      <p style="color:#666;font-size:15px;line-height:1.6;margin-bottom:28px;">
        {username} vous invite à un rendez-vous romantique. Voici tous les détails établis ensemble 💕
      </p>

      <div class="card">
        <div class="card-title">📅 Date &amp; Heure</div>
        <div class="card-value">{date_str}</div>
        <div style="color:#ff6b8a;font-size:16px;margin-top:4px;">🕐 {time_str}</div>
      </div>

      <div class="card">
        <div class="card-title">📍 Lieu</div>
        <div class="card-value">{loc_str}</div>
      </div>

      <div class="card">
        <div class="card-title">🎯 Au programme</div>
        <ul class="activities">{act_list}</ul>
      </div>

      <div class="card">
        <div class="card-title">💗 Niveau d'excitation</div>
        <div class="card-value">{exc_str}</div>
        <div class="excitement-bar" style="width:{plan.excitement}%;"></div>
      </div>
    </div>
    <div class="footer">
      <p>Ce rendez-vous a été planifié avec amour via <strong>Sweet Date</strong> 💗</p>
      <p style="font-size:11px;color:#ffc2d4;margin-top:8px;">Partenaires : {user.email_partner1} &amp; {user.email_partner2}</p>
      <span class="badge">Avec tout notre amour 💕</span>
    </div>
  </div>
</body>
</html>
"""


def send_invitation_emails(plan: DatePlan) -> bool:
    """
    Envoie l'invitation romantique aux 2 partenaires.
    Retourne True si envoi réussi.
    """
    user = plan.user
    subject = f"💗 Sweet Date — Votre rendez-vous du {date_format(plan.date, 'd/m/Y')}"
    date_str = date_format(plan.date, "l j F Y")
    time_str = time_format(plan.time, "H:i") if plan.time else "heure à confirmer"

    messages = []
    for email_addr in (user.email_partner1, user.email_partner2):
        name = email_addr.split("@")[0].capitalize()
        text_content = (
            f"Sweet Date — Invitation romantique\n\n"
            f"Bonjour {name} !\n"
            f"{user.username} vous invite à un rendez-vous le {date_str} à {time_str}.\n"
            f"Lieu : {plan.location or 'Surprise'}\n"
            f"Niveau d'excitation : {plan.excitement}%\n"
        )
        msg = EmailMultiAlternatives(subject=subject, body=text_content,
                                     from_email=settings.DEFAULT_FROM_EMAIL, to=[email_addr])
        msg.attach_alternative(build_invitation_html(plan, name), "text/html")
        messages.append(msg)

    try:
        with get_connection() as connection:
            connection.send_messages(messages)
    except Exception:
        logger.exception("Échec de l'envoi de l'invitation pour le plan %s", plan.pk)
        return False

    plan.email_sent = True
    plan.email_sent_at = timezone.now()
    plan.save(update_fields=["email_sent", "email_sent_at"])
    return True
