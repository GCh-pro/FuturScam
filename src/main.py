from app.job_mail_exporter import JobMailExporter  
from app.format_to_mongo import parse_mission_request, to_serializable
import os
import json

def main():
    # Création de l'objet avec la configuration
    exporter = JobMailExporter(
        client_id="297b61f0-61d8-43d1-bfa4-dd00eb6557a2",
        authority="https://login.microsoftonline.com/47f7bd00-80c3-41fe-afc2-654138069f08",
        scopes=["Mail.Read"],
        attachments_dir="attachments"  
    )


    exporter.authenticate()

    exporter.process_emails()

    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)  # remonter d’un niveau
    json_folder = os.path.join(parent_dir, "app", "attachments")


    if not os.path.exists(json_folder):
        print(f"Le dossier {json_folder} n'existe pas.")
        exit(1)


    for filename in os.listdir(json_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())  
                    mission = parse_mission_request(data)
                    print(json.dumps(mission, default=to_serializable, indent=2, ensure_ascii=False))


                break  
            except Exception as e:
                print(f"⚠️ Erreur en lisant {filename} :", e)


if __name__ == "__main__":
    main()
