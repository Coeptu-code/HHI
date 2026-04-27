# Hutchins Health Insurance - Monorepo

This repo contains two fully separated deployables:

- `marketing/`: static marketing website (deploy on Vercel with Root Directory = `marketing`)
- `api/`: Django API backend (deploy on Render with Root Directory = `api`)

## Local setup (API)

From `api`:

1. Create/activate a virtualenv
2. Install deps: `pip install -r requirements.txt`
3. Run: `python manage.py runserver`
