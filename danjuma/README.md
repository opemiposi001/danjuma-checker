# Danjuma Malicious Attachment Checker

A Flask-based backend system that periodically checks registered Gmail addresses for new emails with attachments, scans them using the VirusTotal API, and replies with a verdict.

## Project Structure
- `app.py`: Application entry point.
- `config.py`: Configuration settings and environment variables.
- `models/database.py`: SQLite setup and database models.
- `services/gmail_service.py`: Gmail API integration for reading and sending emails.
- `services/virustotal_service.py`: VirusTotal API integration for scanning files.
- `services/scanner.py`: The orchestrator for the scanning process.
- `routes/api.py`: Flask REST API endpoints.
- `scheduler.py`: Background job to run scans every 2 minutes.

## Setup Instructions

### 1. Prerequisite: Gmail OAuth Setup
To use the Gmail API, you need to create a project in the Google Cloud Console and enable the Gmail API.
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Gmail API** for your project.
4.  Configure the **OAuth consent screen** and add your Gmail address as a test user.
5.  Create **OAuth 2.0 Client IDs** (Desktop app) and download the JSON file as `credentials.json`.
6.  Place the `credentials.json` file in the `danjuma-checker/` directory.

### 2. Prerequisite: VirusTotal API Key
1.  Create a free account on [VirusTotal](https://www.virustotal.com/).
2.  Copy your API key from the API Key section of your profile settings.

### 3. Environment Configuration
1.  Create a `.env` file in the root of the project (using `.env.example` as a template):
    ```env
    VIRUSTOTAL_API_KEY=your_virustotal_api_key
    SECRET_KEY=your_secret_key
    DATABASE_URL=sqlite:///danjuma.db
    ```

### 4. Installation
1.  Navigate to the project directory:
    ```bash
    cd danjuma-checker
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 5. Running the Application
1.  Start the Flask app:
    ```bash
    python app.py
    ```
2.  The application will start on `http://localhost:5000`.
3.  On the first run, it will open a browser window for Google OAuth authentication. Follow the steps to authorize the app. A `token.json` file will be created to store the credentials.

## API Endpoints

- `POST /api/register`: Accepts `{ "email": "user@gmail.com" }`.
- `GET /api/scans?email=user@gmail.com`: Returns scan history for the email.
- `GET /api/status?email=user@gmail.com`: Returns whether protection is active.
- `GET /api/gmail/auth-url?email=user@gmail.com`: Returns a Gmail OAuth authorization URL.
- `POST /api/gmail/authorize`: Accepts `{ "email": "user@gmail.com", "code": "<oauth_code>" }` to exchange an auth code and save Gmail tokens.
- `DELETE /api/unregister`: Deactivates protection for the email.

## Deployment on Render

This application can be deployed on Render as a web service.

### Prerequisites
1. Create a Render account at https://render.com
2. Set up Google Cloud Project and VirusTotal API key as described in setup instructions

### Deployment Steps
1. Push your code to a GitHub repository
2. Connect your GitHub repo to Render
3. Create a new Web Service
4. Configure the following environment variables in Render:
   - `VIRUSTOTAL_API_KEY`: Your VirusTotal API key
   - `SECRET_KEY`: A random secret key for Flask sessions
   - `DATABASE_URL`: `sqlite:///danjuma.db` (or use a PostgreSQL database for persistence)
   - `GOOGLE_CREDENTIALS_PATH`: Path to your Google credentials JSON (upload as a secret file or use service account)
   - `GOOGLE_TOKEN_PATH`: Path to token file (may need to be generated locally first)

### Notes
- The OAuth flow for Gmail requires user interaction, so you may need to authenticate locally first and upload the token.json
- For production, consider using Google Service Accounts instead of OAuth
- SQLite database will reset on redeploys; use PostgreSQL for persistent data
- The background scheduler runs every 5 minutes to scan emails

