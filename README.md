# Financial AI Analyst 🤖📊

A multi-modal RAG (Retrieval Augmented Generation) system for analyzing financial documents. Upload 10-K reports, annual reports, or any financial PDF and get intelligent insights through a conversational interface.

![Financial AI Analyst](https://img.shields.io/badge/AI-Powered-blue) ![Python 3.11](https://img.shields.io/badge/Python-3.11-green) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal) ![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **📊 Chart Analysis**: AI-powered understanding of graphs, charts, and visualizations
- **📋 Table Extraction**: Accurate parsing of financial tables
- **💬 Conversational Interface**: Natural follow-up questions with context awareness
- **🎨 Modern UI**: Premium design with dark/light themes and responsive layout
- **🔒 Session-based**: Each upload creates an isolated session for privacy

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│   FastAPI       │────▶│   Google        │
│  (GitHub Pages) │     │   Backend       │     │   Gemini API    │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  PDF     │ │ ChromaDB │ │HuggingFace│
              │ Parser   │ │ Vector DB│ │Embeddings │
              └──────────┘ └──────────┘ └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google API Key (for Gemini)
- Docker (optional, for containerized deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/financial-analyst.git
cd financial-analyst
```

### 2. Set Up Environment

```bash
# Create .env file with your API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### 3. Run with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 4. Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
python -m http.server 3000
# Or use any static file server like Live Server in VS Code
```

## 📁 Project Structure

```
financial-analyst/
├── frontend/                    # Static frontend (GitHub Pages)
│   ├── index.html              # Main HTML file
│   ├── css/styles.css          # Premium design system
│   ├── js/app.js               # Client-side application
│   └── assets/                 # Icons and images
├── backend/                     # FastAPI backend
│   ├── main.py                 # FastAPI application
│   ├── routers/                # API route handlers
│   │   ├── upload.py           # PDF upload endpoints
│   │   └── chat.py             # Chat endpoints
│   ├── services/               # Core business logic
│   │   ├── ingest.py           # PDF parsing
│   │   ├── summarize.py        # Image summarization
│   │   └── rag.py              # RAG pipeline
│   └── requirements.txt        # Python dependencies
├── .github/workflows/           # CI/CD
│   └── deploy-frontend.yml     # GitHub Pages deployment
├── Dockerfile                   # Container image
├── docker-compose.yml          # Multi-service setup
└── README.md
```

## 🌐 Deployment

### Frontend (GitHub Pages)

1. Push code to GitHub
2. Go to **Settings** → **Pages**
3. Set source to **GitHub Actions**
4. Set repository variable `API_BASE_URL` to your backend URL
5. The workflow will auto-deploy on push to `main`

### Backend Options

#### Option A: Railway (Recommended - Free Tier)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Option B: Render
1. Create new Web Service on [render.com](https://render.com)
2. Connect GitHub repository
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

#### Option C: Hugging Face Spaces
1. Create new Space with Docker SDK
2. Copy `Dockerfile` and `backend/` to the Space
3. Add `GOOGLE_API_KEY` secret

## 📡 API Reference

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF file>
```

### Check Status
```http
GET /api/status/{session_id}
```

### Send Message
```http
POST /api/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "What was the revenue last year?"
}
```

### Get History
```http
GET /api/history/{session_id}
```

### Delete Session
```http
DELETE /api/session/{session_id}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |

### Frontend Configuration

Edit `frontend/js/app.js`:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',  // Update for production
    POLLING_INTERVAL: 2000,
    MAX_POLL_ATTEMPTS: 150,
};
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - LLM framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI model
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
