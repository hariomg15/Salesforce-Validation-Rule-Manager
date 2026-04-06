# Salesforce Validation Rule Manager

This project is a full-stack assignment submission for managing Salesforce validation rules on the `Account` object.

The application includes:

- A `React` frontend for login, rule review, toggle updates, and deployment
- A `FastAPI` backend for OAuth, protected APIs, and Salesforce integration
- `PostgreSQL` for application session and deployment audit storage
- `JWT` based app sessions between the frontend and backend

## Implemented Features

- Salesforce OAuth login flow
- Local session flow for development and walkthroughs
- Protected backend session lookup
- Fetching Account validation rules from Salesforce Tooling API
- Toggling validation rule active/inactive state in the UI
- Deploying selected rule changes back to Salesforce
- Deployment audit logging in PostgreSQL

## Project Structure

- `app/` FastAPI backend
- `frontend/` React frontend

## Backend Flow

1. User starts authentication from the React app.
2. FastAPI redirects to Salesforce OAuth.
3. Salesforce returns an authorization code to the backend callback.
4. FastAPI exchanges the code for Salesforce tokens.
5. Backend stores the session data in PostgreSQL.
6. Backend returns a JWT for frontend API access.
7. Frontend uses the JWT to load validation rules and deploy updates.

## Local Setup

### 1. Configure environment variables

Create a `.env` file in the project root with values similar to:

```env
FRONTEND_ORIGIN=http://localhost:5173
API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/cv_assignment

JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=120

SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REDIRECT_URI=http://localhost:8000/api/auth/callback
SALESFORCE_LOGIN_URL=https://login.salesforce.com
```

### 2. Start PostgreSQL

Create a database named `cv_assignment`.

### 3. Install backend dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

## Notes

- The local session button is available for development and UI walkthroughs without live Salesforce authentication.
- Real Salesforce operations require valid OAuth credentials and an accessible PostgreSQL instance.
- Frontend production build has been verified successfully with `npm run build`.
