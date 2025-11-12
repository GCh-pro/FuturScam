import os
import requests
from msal import PublicClientApplication
import base64
from datetime import datetime, timezone

class JobMailExporter:
    def __init__(self, client_id: str, authority: str, scopes: list, attachments_dir: str = "attachments"):
        self.client_id = client_id
        self.authority = authority
        self.scopes = scopes
        self.attachments_dir = os.path.abspath(attachments_dir)
        os.makedirs(self.attachments_dir, exist_ok=True)
        self.access_token = None
        self.headers = {}

    def authenticate(self):
        app = PublicClientApplication(self.client_id, authority=self.authority)
        result = app.acquire_token_interactive(scopes=self.scopes)

        if "access_token" not in result:
            raise RuntimeError(f"Erreur d'authentification: {result.get('error_description')}")
        
        self.access_token = result["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        print("✅ Authentification réussie.")

    def get_filtered_emails(self, subject_prefix="[JOB EXPORT]", max_emails=50):
        url = f"https://graph.microsoft.com/v1.0/me/messages?$top={max_emails}&$select=id,subject,hasAttachments,receivedDateTime"
        emails = requests.get(url, headers=self.headers).json().get("value", [])
        
        today = datetime.now(timezone.utc).date()
        filtered = [
            mail for mail in emails
            if mail.get("subject", "").startswith(subject_prefix) and
               datetime.fromisoformat(mail.get("receivedDateTime")).date() == today
        ]
        print(f"📬 Nombre de mails filtrés : {len(filtered)}")
        return filtered

    def save_attachments(self, mail):
        mail_id = mail["id"]
        subject = mail.get("subject", "No_Subject")
        has_attachments = mail.get("hasAttachments", False)
        print(f"\n📨 Sujet : {subject}")
        print(f"📎 Pièces jointes : {'Oui' if has_attachments else 'Non'}")

        if not has_attachments:
            return

        attachments_url = f"https://graph.microsoft.com/v1.0/me/messages/{mail_id}/attachments"
        attachments = requests.get(attachments_url, headers=self.headers).json().get("value", [])

        for att in attachments:
            att_name = att.get("name", "unknown_file")
            att_content_bytes = att.get("contentBytes")

            if att_content_bytes:
                file_path = os.path.join(self.attachments_dir, att_name)
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(att_content_bytes))
                print(f"✅ Pièce jointe enregistrée : {file_path}")
            else:
                print(f"⚠️ Impossible de récupérer la pièce jointe : {att_name}")

    def process_emails(self):
        filtered_emails = self.get_filtered_emails()
        for mail in filtered_emails:
            self.save_attachments(mail)
        print("\n🎉 Tous les mails filtrés et pièces jointes traités.")


# ------------------- Exemple d'utilisation depuis un main -------------------
if __name__ == "__main__":
    exporter = JobMailExporter(
        client_id="297b61f0-61d8-43d1-bfa4-dd00eb6557a2",
        authority="https://login.microsoftonline.com/47f7bd00-80c3-41fe-afc2-654138069f08",
        scopes=["Mail.Read"]
    )

    exporter.authenticate()
    exporter.process_emails()
