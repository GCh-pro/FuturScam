import json
import re 
from openai import OpenAI

class JobDescriptionEnhancer:
    """
    Classe pour enrichir et traduire un JSON d'offre d'emploi
    à l'aide de l'API ChatGPT (GPT-4).
    """
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_skills_and_languages(self, criteria: str, description: str = "") -> dict:
        """
        Extrait les compétences techniques et les langues d'un texte de mission.
        
        Args:
            criteria: Le texte des critères de la mission
            description: La description complète de la mission (optionnel)
            
        Returns:
            dict avec:
                - skills: Liste des compétences techniques extraites
                - languages: Liste des langues extraites
        """
        combined_text = f"{criteria}\n{description}".strip()
        
        prompt = f"""Tu es un expert en extraction d'informations pour des missions IT.

À partir du texte ci-dessous, tu dois extraire :

1. **skills** : Liste des compétences techniques, technologies, frameworks, outils mentionnés
   - Sois précis (ex: "Python", "React", "AWS", "Docker", "Kubernetes")
   - Ne mets que les compétences techniques, pas les soft skills
   - Maximum 20 compétences les plus pertinentes
   - Format: liste de mots-clés courts

2. **languages** : Liste des langues requises
   - Format: ["Français", "Anglais", "Néerlandais", etc.]
   - Uniquement les langues explicitement mentionnées

Réponds **uniquement** sous ce format JSON :

{{
  "skills": ["skill1", "skill2", ...],
  "languages": ["Français", "Anglais", ...]
}}

---

TEXTE À ANALYSER :

{combined_text}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "skills": result.get("skills", []),
                "languages": result.get("languages", [])
            }
        except Exception as e:
            print(f"[ERROR] Error extracting skills and languages: {e}")
            return {
                "skills": [],
                "languages": []
            }

    def enhance_job_description_html(self, job_description: str) -> dict:
        """
        Enrichit une job description brute et retourne un HTML structuré + RFP_type.
        
        Args:
            job_description: La description de poste brute
            
        Returns:
            dict avec:
                - RFP_type: Catégorie du RFP
                - enhanced_job_description_html: HTML structuré et enrichi
        """
        prompt = f"""Tu es un expert RH spécialisé dans la rédaction d'offres de mission pour freelances IT.

À partir de la job_description ci-dessous, tu dois produire une version :
1. **Améliorée, enrichie et structurée**  
2. **En HTML propre**, compatible avec un front React  
3. **Utilisant le canevas fourni ci-dessous**  
4. **Catégorisée automatiquement via un champ "RFP_type"**

---

## 🎯 1. CANEVAS À UTILISER POUR LA JOB DESCRIPTION (HTML)

Le texte final doit suivre cette structure HTML :

<section>
  <h2>Contexte de la mission</h2>
  <p>…</p>
</section>

<section>
  <h2>Responsabilités principales</h2>
  <ul>
    <li>…</li>
  </ul>
</section>

<section>
  <h2>Profil recherché</h2>
  <ul>
    <li>…</li>
  </ul>
</section>

<section>
  <h2>Compétences techniques</h2>
  <ul>
    <li>…</li>
  </ul>
</section>

<section>
  <h2>Soft Skills</h2>
  <ul>
    <li>…</li>
  </ul>
</section>

Tu peux adapter les sections uniquement si absolument nécessaire, mais garde cette structure dès que possible.

---

## 🎯 2. RFP_type

Déduis automatiquement la catégorie "RFP_type" la plus pertinente parmi :

- Go-To-Market, Sales B2B  
- Data, AI, BI  
- Integration, API, Architecture
- Cybersecurity  
- Cloud, Infrastructure  
- Software Engineering  
- PMO, Project Management  
- Business Analysis  
- Support & Operations  
- Autre

Retourne **uniquement** celle qui correspond le mieux.

---

## 🎯 3. FORMAT DE SORTIE

Réponds **uniquement** sous ce format JSON :

{{
  "RFP_type": "<catégorie>",
  "job_description": "<section>…</section>"
}}

Le HTML doit être safe, bien indenté, sans script, sans style inline.

---

## 🎯 4. CONTENU ENTRANT

Voici la job_description brute dont tu dois t'inspirer :

{job_description}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"[ERROR] Error while enhancing job description: {e}")
            return {
                "RFP_type": "Autre",
                "job_description": f"<section><p>{job_description}</p></section>"
            }

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
