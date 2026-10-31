# Access Bank Ghana WhatsApp Chatbot

## Introduction

A WhatsApp customer-service assistant for Access Bank Ghana. Customers message the bank's WhatsApp number and get answers about accounts, loans, cards, interest rates, digital banking (`*901#`, Access More app) and branch services.

How it works:

1. Meta's WhatsApp Cloud API delivers each incoming message to the Flask webhook in `app.py`.
2. A LangChain agent (`rag_agent.py`, GPT-4o-mini) answers using retrieval-augmented generation (RAG). It searches an in-memory vector index built from the Access Bank Ghana website (`scraper.py`) and `knowledge/custom_bank_info.txt`.
3. The reply is sent back to the customer through the WhatsApp Cloud API.

If the answer is not in the retrieved context, the bot does not guess. It refers the customer to Customer Care (0800 004 400) or a branch.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Flask app: health check, webhook verification, message handling, WhatsApp replies |
| `rag_agent.py` | LangChain agent, embeddings, vector store and the retrieval tool |
| `scraper.py` | Scrapes the Access Bank Ghana website and builds the knowledge chunks (cached in `website_cache.pkl`) |
| `crm_db.py` | Optional helpers for querying the CRM SQL Server database |
| `test_crm_db.py` | Tests for `crm_db.py` |
| `knowledge/` | Extra bank information used by the bot |
| `Dockerfile`, `Procfile`, `azure-pipelines.yml` | Deployment and CI/CD |

## Getting Started

### Requirements

- Python 3.11
- An OpenAI API key
- A Meta WhatsApp Cloud API app (access token, phone number ID, verify token)
- (Optional) Access to the CRM SQL Server database
- ngrok, or any public HTTPS URL, so Meta can reach your local webhook

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Copy the template and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API key |
| `WHATSAPP_TOKEN` | WhatsApp Cloud API access token |
| `PHONE_NUMBER_ID` | WhatsApp phone number ID |
| `VERIFY_TOKEN` | Any string you choose; must match the one entered in the Meta webhook settings |
| `WHATSAPP_API_VERSION` | Graph API version (default `v21.0`) |
| `WHATSAPP_REQUEST_TIMEOUT` | Timeout in seconds for WhatsApp API calls (default `20`) |
| `CRM_DB_HOST`, `CRM_DB_PORT`, `CRM_DB_NAME`, `CRM_DB_USER`, `CRM_DB_PASSWORD` | Optional CRM database connection |

Never commit `.env`. It is already listed in `.gitignore`.

### Run locally

```bash
python app.py
```

The bot listens on port 5000 (or `PORT`). On Windows you can also double-click `start.bat`.

To receive WhatsApp messages locally, expose the port in a second terminal:

```bash
ngrok http 5000
```

In the Meta developer portal, set the webhook callback URL to `https://<your-ngrok-url>/webhook` and the verify token to your `VERIFY_TOKEN`.

### Endpoints

- `GET /` health check, returns `{"status": "online", ...}`
- `GET /webhook` Meta webhook verification
- `POST /webhook` incoming WhatsApp messages

## Build and Test

Build and run with Docker:

```bash
docker build -t abg-chatbot .
docker run --env-file .env -p 5000:5000 abg-chatbot
```

Run the tests:

```bash
python -m pytest test_crm_db.py
```

The Azure DevOps pipeline (`azure-pipelines.yml`) builds the Docker image on every push to `main` or `master`.

## Contribute

1. Create a branch from `main`.
2. Make your changes and test them locally.
3. Open a pull request for review.

Do not commit secrets or `.env` files.
