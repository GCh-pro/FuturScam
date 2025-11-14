import json
import re 
from openai import OpenAI

class JobDescriptionEnhancer:
    """
    Classe pour enrichir et traduire un JSON d'offre d'emploi
    à l'aide de l'API ChatGPT (GPT-4).
    """
    def __init__(self, api_key: str, model: str = "gpt-5"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete_and_translate(self, job_json: dict) -> dict:
        """
        Complète les champs manquants du JSON et traduit en anglais.
        Retourne un dictionnaire mis à jour.
        """

        job_desc = job_json.get("description", "")
        prompt = f"""
                        You are an HR data assistant.
                        Given this job description, fill in or improve missing fields 
                        in the following job JSON (skills, languages, region, etc.) 
                        and then translate all text fields into English.
                        Return a valid JSON object only.
                        summarize skills if needed, if a skill is a sentence, convert it to keywords.
                        
                        Job description:
                        {job_desc}

                        Current job JSON:
                        {json.dumps(job_json, indent=2, ensure_ascii=False)}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}  
            )
            completed_json = json.loads(response.choices[0].message.content)
            return completed_json
        except Exception as e:
            print(f"⚠️ Error while completing job JSON: {e}")
            return job_json
