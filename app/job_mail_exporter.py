import os
import requests
from msal import PublicClientApplication
import base64
from datetime import datetime, timezone

class JobMailExporter:
    def __init__(self, client_id: str, authority: str, scopes: list, attachments_dir: str = "attachments", init: bool = False):
        self.client_id = client_id
        self.authority = authority
        self.scopes = scopes
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        self.attachments_dir = os.path.join(base_dir, attachments_dir)
        os.makedirs(self.attachments_dir, exist_ok=True)
        self.access_token = None
        self.headers = {}
        self.init = init

    def authenticate(self):
        app = PublicClientApplication(self.client_id, authority=self.authority)
        result = app.acquire_token_interactive(scopes=self.scopes)

        if "access_token" not in result:
            raise RuntimeError(f"Erreur d'authentification: {result.get('error_description')}")
        
        self.access_token = result["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        print("[OK] Authentification réussie.")

    def get_filtered_emails(self, subject_prefix="[JOB EXPORT]", max_emails=250):
        if not self.init:
            url = f"https://graph.microsoft.com/v1.0/me/messages?$top={max_emails}&$select=id,subject,hasAttachments,receivedDateTime"
        else:
            url = f"https://graph.microsoft.com/v1.0/me/messages?$top={max_emails}&$select=id,subject,hasAttachments"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            emails = response.json().get("value", [])
        except Exception as e:
            print(f"[ERROR] Error fetching emails: {e}")
            return []
        
        today = datetime.now(timezone.utc).date()
        filtered = [
            mail for mail in emails
            if mail.get("subject", "").startswith(subject_prefix)
            and (self.init or datetime.fromisoformat(mail.get("receivedDateTime")).date() == today)
        ]
        print(f"[MAIL] Total emails found: {len(emails)}, Filtered by '{subject_prefix}': {len(filtered)}")
        return filtered

    def save_attachments(self, mail):
        mail_id = mail["id"]
        subject = mail.get("subject", "No_Subject")
        has_attachments = mail.get("hasAttachments", False)
        print(f"\n[SUBJECT] Sujet : {subject}")
        print(f"[ATTACHMENTS] Pièces jointes : {'Oui' if has_attachments else 'Non'}")

        if not has_attachments:
            print(f"[SKIP] No attachments for this email")
            return

        try:
            attachments_url = f"https://graph.microsoft.com/v1.0/me/messages/{mail_id}/attachments"
            response = requests.get(attachments_url, headers=self.headers)
            response.raise_for_status()
            attachments = response.json().get("value", [])
        except Exception as e:
            print(f"[ERROR] Error fetching attachments: {e}")
            return

        if not attachments:
            print(f"[WARN] No attachments returned from API for {mail_id}")
            return

        for att in attachments:
            att_name = att.get("name", "unknown_file")
            att_content_bytes = att.get("contentBytes")

            # Vérifie que c’est un JSON
            if not att_name.lower().endswith(".json"):
                print(f"[SKIP] Fichier ignoré (pas un JSON) : {att_name}")
                continue
            
            # Vérifie qu’on a bien le contenu
            if not att_content_bytes:
                print(f"[WARN] Impossible de récupérer la pièce jointe : {att_name}")
                continue
            
            # Enregistrement du fichier JSON
            file_path = os.path.join(self.attachments_dir, att_name)
            try:
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(att_content_bytes))
                print(f"[OK] Pièce jointe JSON enregistrée : {file_path}")
            except Exception as e:
                print(f"[ERROR] Error saving file {att_name}: {e}")

    def process_emails(self):
        filtered_emails = self.get_filtered_emails()
        print(f"[EMAIL] Processing {len(filtered_emails)} emails...")
        for mail in filtered_emails:
            self.save_attachments(mail)
        print("[OK] Tous les mails filtrés et pièces jointes traités.")



