# Hutchins Onboarding + Gap Scoring (Django)

Server-rendered Django MVP for agents to:

- Create intake links (tokenized questionnaires)
- Collect client onboarding/intake information
- Generate deterministic gap findings and referral opportunities

## Local setup

From `hutchins-onboarding/`:

1. Create/activate a virtualenv
2. Install deps: `pip install -r requirements.txt`
3. Copy env: `copy .env.example .env` (Windows) and fill values as needed
4. Run migrations: `python manage.py migrate`
5. Create admin user: `python manage.py createsuperuser`
6. Run: `python manage.py runserver`
