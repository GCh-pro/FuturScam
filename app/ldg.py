import os
import requests
from msal import PublicClientApplication
import base64
from datetime import datetime, timezone

# ---------------- Configuration ----------------
CLIENT_ID = "297b61f0-61d8-43d1-bfa4-dd00eb6557a2"
AUTHORITY = "https://login.microsoftonline.com/47f7bd00-80c3-41fe-afc2-654138069f08"
SCOPES = ["Mail.Read"]

# ---------------- Authentification ----------------
app = PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY
)

result = app.acquire_token_interactive(scopes=SCOPES)

if "access_token" not in result:
    print("Erreur d'authentification:", result.get("error_description"))
    exit(1)

access_token = result["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# ---------------- Dossier de sauvegarde ----------------
ATTACHMENTS_DIR = os.path.join(os.path.dirname(__file__), "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# ---------------- Récupération des mails ----------------
url = "https://graph.microsoft.com/v1.0/me/messages?$top=50&$select=id,subject,hasAttachments,receivedDateTime"
response = requests.get(url, headers=headers)
emails = response.json().get("value", [])

# Filtrer pour aujourd'hui et sujet commençant par [JOB EXPORT]
today = datetime.now(timezone.utc).date()
filtered_emails = [
    mail for mail in emails
    if mail.get("subject", "").startswith("[JOB EXPORT]") and
       datetime.fromisoformat(mail.get("receivedDateTime")).date() == today
]

print(f"Nombre de mails filtrés : {len(filtered_emails)}")

for mail in filtered_emails:
    mail_id = mail["id"]
    subject = mail.get("subject", "No_Subject")
    has_attachments = mail.get("hasAttachments", False)

    print(f"\n📨 Sujet : {subject}")
    print(f"📎 Pièces jointes : {'Oui' if has_attachments else 'Non'}")

    # ---------------- Récupération du corps ----------------
    mail_detail_url = f"https://graph.microsoft.com/v1.0/me/messages/{mail_id}?$select=body"
    mail_detail = requests.get(mail_detail_url, headers=headers).json()
    body_content = mail_detail.get("body", {}).get("content", "")
    # optionnel : afficher le body ou le sauvegarder dans un fichier

    # ---------------- Récupération des pièces jointes ----------------
    if has_attachments:
        attachments_url = f"https://graph.microsoft.com/v1.0/me/messages/{mail_id}/attachments"
        attachments = requests.get(attachments_url, headers=headers).json().get("value", [])

        for att in attachments:
            att_name = att.get("name", "unknown_file")
            att_content_bytes = att.get("contentBytes")

            if att_content_bytes:
                file_path = os.path.join(ATTACHMENTS_DIR, att_name)
                # Décodage Base64 correct
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(att_content_bytes))
                print(f"✅ Pièce jointe enregistrée : {file_path}")
            else:
                print(f"⚠️ Impossible de récupérer la pièce jointe : {att_name}")

print("\n🎉 Tous les mails filtrés et pièces jointes traités.")
