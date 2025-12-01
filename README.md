# AI Chatbot Project

A comprehensive AI-powered chatbot solution featuring a Python backend, React-based frontend consoles, and n8n automation workflows. This system is designed to handle customer support queries, escalate to human agents when necessary, and provide analytics for business owners.

## 📂 Project Structure

The project is organized into the following main components:

- **`server/`**: The backend API built with Python (FastAPI). Handles authentication, database interactions, and websocket connections.
- **`frontend/`**: Contains the user interfaces.
  - **`agent-console/`**: A React application for human agents to handle escalated chats.
  - **`owner-dashboard/`**: A React application for business owners to view analytics and chat history.
  - **`demo-website/`**: A simple HTML demo page to showcase the chat widget.
- **`ai-support-n8n/`**: Contains n8n workflow JSON files for AI logic, routing, and message handling.
- **`query.sql`**: SQL scripts for setting up the Supabase database schema and Row Level Security (RLS) policies.
- **`render.yaml`**: Configuration file for deploying the backend to Render.

## 🚀 Prerequisites

Before you begin, ensure you have the following installed/configured:

- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended) & **Poetry** (for dependency management)
- **n8n** (Self-hosted or Cloud version)
- **Supabase** Account (for PostgreSQL database)
- **OpenAI API Key** (for LLM features)

## 🛠️ Setup & Installation

### 1. Database Setup (Supabase)

1. Create a new project in Supabase.
2. Go to the SQL Editor in Supabase.
3. Copy the contents of `query.sql` and run it to set up the tables and security policies.
4. Note down your `SUPABASE_URL` and `SUPABASE_KEY` (service role key is recommended for the backend).

### 2. Backend Setup (`server/`)

1. Navigate to the server directory:
   ```bash
   cd server
   ```
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
3. Create a `.env` file based on the example (or required variables):
   ```ini
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OPENAI_API_KEY=your_openai_key
   N8N_WEBHOOK_BASE_URL=your_n8n_webhook_url
   # Add other variables as found in server/config.py
   ```
4. Run the server:
   ```bash
   poetry run uvicorn main:app --reload
   ```

### 3. Frontend Setup (`frontend/`)

#### Agent Console
1. Navigate to the directory:
   ```bash
   cd frontend/agent-console
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

#### Owner Dashboard
1. Navigate to the directory:
   ```bash
   cd frontend/owner-dashboard
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

### 4. n8n Workflows (`ai-support-n8n/`)

1. Open your n8n instance.
2. Import the JSON files from the `ai-support-n8n/` directory.
   - `inbound_handler.json`: Entry point for messages.
   - `llm_brain.json`: Core AI logic.
   - `router.json`: Routes messages to appropriate handlers.
   - `escalation_handler.json`: Manages handoffs to human agents.
   - And others...
3. Configure the n8n credentials for OpenAI and Supabase within the n8n UI.
4. Update the webhook URLs in your `server/.env` file to match your active n8n workflow URLs.

## 📦 Deployment

### Backend
The project includes a `render.yaml` file for easy deployment to [Render](https://render.com).
1. Connect your repository to Render.
2. Create a new Blueprint instance using `render.yaml`.
3. Set the required environment variables in the Render dashboard.

### Frontend
The React apps (`agent-console`, `owner-dashboard`) can be deployed to any static site host (Vercel, Netlify, Render Static Sites).
- Build command: `npm run build`
- Output directory: `dist`

### n8n
Ensure your n8n instance is publicly accessible if you are using webhooks that need to be reached by external services (like WhatsApp or this backend).

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.
