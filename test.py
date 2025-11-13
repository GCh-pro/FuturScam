import requests
import json

# URL du endpoint OAuth (environnement UAT)
url = "https://api.littlebigconnection.com/oauth/token"


payload = json.dumps({
    "grant_type": "client_credentials",
    "client_id": "286050",        
    "client_secret": "*****",
    "audience": "external-client-api-v2"
})


headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer <token>'
}


response = requests.post(url, data=payload, headers=headers)

# Vérification de la réponse
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    print("✅ Token récupéré avec succès :")
    print(access_token)
else:
    print(f"❌ Erreur {response.status_code}: {response.text}")
