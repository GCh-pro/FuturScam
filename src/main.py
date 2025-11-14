from app.job_mail_exporter import JobMailExporter  
import mappers.pro_unity_mappings as pum
import mappers.mapper_to_mongo as ftm
from app.connect_to_mongo import MongoJsonInserter
from app.job_completer import JobDescriptionEnhancer
from helpers import to_serializable
import os
import json
import params


def main():
    inserter = MongoJsonInserter(uri = params.MONGO_URI)
    exporter = JobMailExporter(
        client_id= params.AZURE_CLIENT,
        authority=params.AZURE_URI,
        scopes=["Mail.Read"],
        attachments_dir="attachments" ,
        init = False
    )

    completer = JobDescriptionEnhancer(api_key=params.OPENAI_KEY)
    exporter.authenticate()

    exporter.process_emails()

    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)  
    json_folder = os.path.join(parent_dir, "app", "attachments")


    if not os.path.exists(json_folder):
        print(f"Le dossier {json_folder} n'existe pas.")
        exit(1)


    for filename in os.listdir(json_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    
                    data2 = json.load(f)
                    mission = ftm.map_json(data2, pum.MAPPING, pum.LIST_MAPPINGS)
                    print(json.dumps(mission,default=to_serializable, indent=2, ensure_ascii=False))
                    inserter.insert_json(mission)
                
            except Exception as e:
                
                print(f"⚠️ Erreur en lisant {filename} :", e)
            finally:
                # 🧹 Supprimer seulement le fichier JSON traité
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"🗑️  Fichier '{filename}' supprimé")
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la suppression de '{filename}' : {e}")
    inserter.client.close()


if __name__ == "__main__":
    main()
