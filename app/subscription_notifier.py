import requests
from typing import List, Dict
from datetime import datetime, timezone


class SubscriptionNotifier:
    """
    Classe pour envoyer des emails personnalisés aux utilisateurs abonnés
    avec les nouvelles offres correspondant à leurs abonnements.
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Initialise le notificateur d'abonnements.
        
        Args:
            api_url: URL de l'API backend
        """
        self.api_url = api_url
        print(f"[INIT] SubscriptionNotifier initialized with API: {self.api_url}")

    def get_users_with_subscriptions(self) -> List[Dict]:
        """
        Récupère tous les utilisateurs ayant des abonnements (metadata avec role='abonnements').
        
        Returns:
            Liste des utilisateurs avec leurs abonnements
        """
        try:
            response = requests.get(f"{self.api_url}/users", timeout=30)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch users: status {response.status_code}")
                return []
            
            all_users = response.json() if isinstance(response.json(), list) else response.json().get("data", [])
            
            # Filtrer les utilisateurs avec des abonnements
            users_with_subs = []
            for user in all_users:
                metadata = user.get("metadata", [])
                subscriptions = [m for m in metadata if m.get("role") == "abonnements"]
                
                if subscriptions:
                    user["subscriptions"] = subscriptions
                    users_with_subs.append(user)
            
            print(f"[OK] Found {len(users_with_subs)} users with subscriptions")
            return users_with_subs
            
        except requests.RequestException as e:
            print(f"[ERROR] Error fetching users: {e}")
            return []

    def get_new_rfps_for_subscription(self, subscription_name: str, all_new_rfps: List[Dict]) -> List[Dict]:
        """
        Filtre les RFPs correspondant à un abonnement spécifique.
        
        Args:
            subscription_name: Nom de l'abonnement (ex: "Data, AI, BI")
            all_new_rfps: Liste de toutes les nouvelles RFPs du run actuel
            
        Returns:
            Liste des RFPs correspondant à l'abonnement
        """
        matching_rfps = []
        
        print(f"[DEBUG] Looking for subscription: '{subscription_name}'")
        print(f"[DEBUG] Checking {len(all_new_rfps)} new RFPs from this run")
        
        for rfp in all_new_rfps:
            rfp_type = rfp.get("RFP_type", "")
            job_id = rfp.get("job_id", "N/A")
            
            # Vérifier si le RFP_type correspond à l'abonnement
            if rfp_type and subscription_name and subscription_name.lower() in rfp_type.lower():
                matching_rfps.append(rfp)
                print(f"[DEBUG] ✓ RFP {job_id} matches: RFP_type='{rfp_type}'")
        
        print(f"[DEBUG] Found {len(matching_rfps)} RFPs matching '{subscription_name}'")
        return matching_rfps

    def generate_email_body(self, user_name: str, subscriptions_rfps: Dict[str, List[Dict]]) -> str:
        """
        Génère le corps de l'email HTML personnalisé avec toutes les RFPs de tous les abonnements.
        
        Args:
            user_name: Nom de l'utilisateur
            subscriptions_rfps: Dict {nom_abonnement: [liste_rfps]}
            
        Returns:
            HTML du corps de l'email
        """
        # Compter le total de RFPs
        total_rfps = sum(len(rfps) for rfps in subscriptions_rfps.values())
        
        # Générer le contenu pour chaque abonnement
        subscriptions_html = ""
        for subscription_name, rfps in subscriptions_rfps.items():
            if not rfps:
                continue
                
            subscriptions_html += f"""
            <div style="margin-bottom: 30px;">
                <h2 style="color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    {subscription_name} ({len(rfps)} offre(s))
                </h2>
            """
            
            for rfp in rfps:
                title = rfp.get("title", "Sans titre")
                job_id = rfp.get("job_id", "")
                job_desc = rfp.get("job_desc", "Pas de description disponible")
                deadline = rfp.get("deadlineAt", "Non spécifiée")
                
                # Extraire le texte de job_desc s'il contient du HTML
                import re
                clean_desc = re.sub('<[^<]+?>', '', job_desc)
                clean_desc = clean_desc.strip()
                preview = clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc
                
                subscriptions_html += f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9;">
                    <h3 style="color: #2c3e50; margin-top: 0;">{title}</h3>
                    <p><strong>Référence:</strong> {job_id}</p>
                    <p><strong>Date limite:</strong> {deadline}</p>
                    <div style="margin-top: 10px; color: #555;">
                        {preview}
                    </div>
                </div>
                """
            
            subscriptions_html += "</div>"
        
        email_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3498db; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: white; padding: 20px; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📬 Vos Nouvelles Offres</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{user_name}</strong>,</p>
                    <p>Vous avez <strong>{total_rfps} nouvelle(s) offre(s)</strong> correspondant à vos abonnements :</p>
                    
                    {subscriptions_html}
                    
                    <p style="margin-top: 30px;">Connectez-vous à votre espace pour voir tous les détails et postuler.</p>
                </div>
                <div class="footer">
                    <p style="margin: 0; color: #7f8c8d;">Cet email est envoyé automatiquement par FuturScam</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #95a5a6;">
                        © {datetime.now().year} FuturWork - Tous droits réservés
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return email_body

    def send_email(self, to_email: str, subject: str, body_html: str) -> bool:
        """
        Envoie un email via l'endpoint API /mail.
        
        Args:
            to_email: Email du destinataire
            subject: Sujet de l'email
            body_html: Corps de l'email en HTML
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Préparer les données pour l'endpoint /mail
            data = {
                "to_addresses": to_email,
                "subject": subject,
                "body": body_html,
                "is_html": True
            }
            
            response = requests.post(
                f"{self.api_url}/mail",
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"[OK] Email sent successfully to {to_email}")
                return True
            else:
                print(f"[ERROR] Failed to send email: status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"[ERROR] Error sending email: {e}")
            return False

    def notify_all_subscribers(self, new_rfps: List[Dict]):
        """
        Envoie des notifications à tous les utilisateurs abonnés avec les nouvelles offres.
        Envoie 1 seul email par utilisateur avec toutes les RFPs de tous ses abonnements.
        
        Args:
            new_rfps: Liste des RFPs ajoutées/modifiées dans le run actuel
        """
        if not new_rfps:
            print("[INFO] No new RFPs to notify about")
            return
        
        print(f"[INFO] Processing {len(new_rfps)} new RFPs for subscription notifications")
        
        # Récupérer les utilisateurs avec abonnements
        users = self.get_users_with_subscriptions()
        
        if not users:
            print("[INFO] No users with subscriptions found")
            return
        
        total_emails_sent = 0
        
        # Pour chaque utilisateur
        for user in users:
            user_name = user.get("name", "Utilisateur")
            user_email = user.get("mail", "")
            
            if not user_email:
                print(f"[WARN] Skipping user {user_name} - no email address")
                continue
            
            # Dictionnaire pour stocker toutes les RFPs par abonnement pour cet utilisateur
            subscriptions_rfps = {}
            total_user_rfps = 0
            
            # Pour chaque abonnement de l'utilisateur
            for subscription in user.get("subscriptions", []):
                subscription_name = subscription.get("full_name") or subscription.get("name", "")
                
                if not subscription_name:
                    print(f"[WARN] Skipping subscription without name for user {user_name}")
                    continue
                
                # Filtrer les nouvelles RFPs pour cet abonnement
                matching_rfps = self.get_new_rfps_for_subscription(subscription_name, new_rfps)
                
                if matching_rfps:
                    subscriptions_rfps[subscription_name] = matching_rfps
                    total_user_rfps += len(matching_rfps)
                    print(f"[INFO] Found {len(matching_rfps)} new RFPs for {user_name} ({subscription_name})")
            
            # Si l'utilisateur a des nouvelles offres, envoyer UN SEUL email avec tout
            if subscriptions_rfps and total_user_rfps > 0:
                print(f"[MAIL] Sending 1 email to {user_name} with {total_user_rfps} RFPs from {len(subscriptions_rfps)} subscription(s)")
                
                subject = f"[FuturScam] {total_user_rfps} nouvelle(s) offre(s) pour vous"
                body = self.generate_email_body(user_name, subscriptions_rfps)
                
                if self.send_email(user_email, subject, body):
                    total_emails_sent += 1
            else:
                print(f"[INFO] No new RFPs for {user_name}")
        
        print(f"[SUMMARY] Sent {total_emails_sent} subscription notification email(s) to {total_emails_sent} user(s)")
