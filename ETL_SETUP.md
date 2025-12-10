# FuturScam ETL - Configuration du Planificateur

## Vue d'ensemble

Le système ETL FuturScam est maintenant configuré pour s'exécuter automatiquement de manière incrémentielle:

- **Suivi de la dernière exécution**: Le fichier `.last_execution` stocke le timestamp de la dernière exécution réussie
- **Traitement incrémentiel**: Seules les données modifiées depuis la dernière exécution sont traitées
- **Timestamp avec précision**: Ajout de 1 milliseconde au timestamp pour éviter les doublons

## Configuration du Planificateur de Tâches Windows

### Option 1: Interface graphique

1. Ouvrir le **Planificateur de tâches** Windows (Task Scheduler)
2. Cliquer sur **Créer une tâche...**
3. **Onglet Général**:
   - Nom: `FuturScam ETL`
   - Description: `Extraction et transformation automatique des RFPs`
   - Cocher: **Exécuter même si l'utilisateur n'est pas connecté**
   - Cocher: **Exécuter avec les autorisations maximales**

4. **Onglet Déclencheurs**:
   - Nouveau déclencheur
   - **Lancer la tâche**: Selon une planification
   - **Paramètres**: Quotidien
   - **Répéter la tâche toutes les**: 1 heure
   - **Pendant**: Indéfiniment

5. **Onglet Actions**:
   - Nouvelle action
   - **Action**: Démarrer un programme
   - **Programme/script**: `powershell.exe`
   - **Ajouter des arguments**: `-ExecutionPolicy Bypass -File "C:\Users\Guillaume_Chinzi\code\FuturScam\run_etl.ps1"`
   - **Commencer dans**: `C:\Users\Guillaume_Chinzi\code\FuturScam`

6. **Onglet Conditions**:
   - Décocher: **Démarrer la tâche uniquement si l'ordinateur est relié au secteur**

7. **Onglet Paramètres**:
   - Cocher: **Autoriser l'exécution de la tâche à la demande**
   - Cocher: **Exécuter la tâche dès que possible après le démarrage manqué**

### Option 2: PowerShell (automatique)

```powershell
# Créer la tâche planifiée
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -File "C:\Users\Guillaume_Chinzi\code\FuturScam\run_etl.ps1"' -WorkingDirectory "C:\Users\Guillaume_Chinzi\code\FuturScam"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "FuturScam ETL" -Action $action -Trigger $trigger -Settings $settings -Description "Extraction et transformation automatique des RFPs FuturScam" -User $env:USERNAME
```

### Option 3: Ligne de commande (schtasks)

```cmd
schtasks /create /tn "FuturScam ETL" /tr "powershell.exe -ExecutionPolicy Bypass -File C:\Users\Guillaume_Chinzi\code\FuturScam\run_etl.ps1" /sc hourly /st 00:00 /f
```

## Exécution manuelle

### Exécution unique

#### Windows (PowerShell)
```powershell
cd C:\Users\Guillaume_Chinzi\code\FuturScam
.\run_etl.ps1
```

#### Windows (Batch)
```cmd
cd C:\Users\Guillaume_Chinzi\code\FuturScam
run_etl.bat
```

#### Python direct
```cmd
cd C:\Users\Guillaume_Chinzi\code\FuturScam
python src\main.py
```

### Exécution en mode continu (Always Run)

#### Windows PowerShell (Recommandé)
```powershell
# Lancer avec l'intervalle par défaut (1 heure)
.\run_etl_continuous.ps1

# Lancer avec un intervalle personnalisé (exemple: toutes les 30 minutes)
.\run_etl_continuous.ps1 -IntervalMinutes 30

# Lancer toutes les 5 minutes (développement/test)
.\run_etl_continuous.ps1 -IntervalMinutes 5

# Afficher l'aide
.\run_etl_continuous.ps1 -Help
```

#### Windows Batch
```cmd
# Lancer avec l'intervalle par défaut (1 heure)
run_etl_continuous.bat

# Lancer avec un intervalle personnalisé (30 minutes)
run_etl_continuous.bat 30
```

**Note:** Le mode continu exécute l'ETL en boucle infinie. Pour arrêter, appuyez sur `Ctrl+C`.

### Exécution en arrière-plan (Windows)

Pour lancer l'ETL en arrière-plan sans garder la fenêtre ouverte:

#### PowerShell
```powershell
# Lancer en arrière-plan
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .\run_etl_continuous.ps1 -IntervalMinutes 60" -WindowStyle Hidden

# Ou avec redirection des logs
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -Command `"& {.\run_etl_continuous.ps1 -IntervalMinutes 60 *>&1 | Tee-Object -FilePath logs\etl_continuous.log}`"" -WindowStyle Hidden
```

#### Arrêter le processus en arrière-plan
```powershell
# Trouver le processus
Get-Process | Where-Object {$_.CommandLine -like "*run_etl_continuous*"}

# Arrêter le processus
Stop-Process -Name python -Force
# ou
Stop-Process -Id <ProcessID>
```

## Fonctionnement du système ETL

### Première exécution
- Le fichier `.last_execution` est créé avec un timestamp par défaut (1 heure en arrière)
- Tous les RFPs récents (dernière heure) sont traités
- Le timestamp actuel + 1ms est sauvegardé

### Exécutions suivantes
- Lecture du timestamp dans `.last_execution`
- Traitement uniquement des données modifiées depuis ce timestamp
- Mise à jour du timestamp après succès

### Gestion des erreurs
- Si l'exécution échoue, le timestamp n'est **PAS** mis à jour
- La prochaine exécution retraitera les mêmes données (idempotence)
- Les logs d'erreur sont affichés dans la console

## Monitoring

### Vérifier la dernière exécution
```powershell
Get-Content C:\Users\Guillaume_Chinzi\code\FuturScam\.last_execution
```

### Voir l'historique du planificateur
```powershell
Get-ScheduledTask -TaskName "FuturScam ETL" | Get-ScheduledTaskInfo
```

### Logs
Les logs sont affichés dans la console. Pour les capturer:
```powershell
.\run_etl.ps1 >> logs\etl_$(Get-Date -Format 'yyyyMMdd_HHmmss').log 2>&1
```

## Réinitialiser le système

Pour forcer le retraitement de toutes les données:
```powershell
# Supprimer le fichier de timestamp
Remove-Item .last_execution

# Ou le définir à une date spécifique
Set-Content .last_execution "2025-12-01T00:00:00.000000"
```

## Notes importantes

1. **Timezone**: Tous les timestamps sont en UTC
2. **Précision**: Les timestamps incluent les microsecondes
3. **Incrémentation**: +1ms ajouté automatiquement pour éviter les doublons
4. **Idempotence**: Le système peut être exécuté plusieurs fois sans créer de doublons (grâce à la gestion des duplicates dans MongoDB)
