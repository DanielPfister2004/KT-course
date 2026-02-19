# Lokales Projekt in ein neues GitHub-Repo pushen

Kurzanleitung: Du hast einen lokalen Ordner und ein leeres Repository auf GitHub – so bringst du beides zusammen.

## Voraussetzungen

- Lokaler Ordner mit deinem Projekt
- Leeres Repository auf GitHub erstellt (ohne README, .gitignore oder License)

## Befehle (in dieser Reihenfolge)

```bash
cd c:\_Git\KT-course
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ChristianNetzberger-FHJOANNEUM/KT-course.git
git push -u origin main
```

## Erklärung

| Befehl | Bedeutung |
|--------|-----------|
| `git init` | Macht den aktuellen Ordner zu einem Git-Repository |
| `git add .` | Fügt alle Dateien zur Staging-Area hinzu (für den ersten Commit nötig) |
| `git commit -m "first commit"` | Erstellt den ersten Commit |
| `git branch -M main` | Benennt den Branch in `main` um |
| `git remote add origin <URL>` | Verknüpft das lokale Repo mit dem GitHub-Repo |
| `git push -u origin main` | Pusht alle Commits zu GitHub und setzt `main` als Standard-Branch |

## Optional: Nicht alles hochladen

Wenn bestimmte Ordner oder Dateien **nicht** ins Repo sollen, vor dem `git add .` eine `.gitignore` anlegen und z. B. eintragen:

- `node_modules/`
- `.env`
- Build-/Cache-Ordner

Dann wie oben weiter mit `git add .` und den restlichen Befehlen.
