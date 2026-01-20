# SecureOps: AI-Powered Construction Site Monitoring

![Status](https://img.shields.io/badge/Status-Beta-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-yellow)
![React](https://img.shields.io/badge/React-18-blue)

**SecureOps** is an enterprise-grade AI platform designed to enhance safety on construction sites. It leverages computer vision (YOLOv8) and Retrieval-Augmented Generation (RAG) to detect safety violations (PPE compliance, zone breaches) in real-time and provide intelligent answers to safety queries based on site reports.

---

## 🚀 Features

- **🛡️ Real-time PPE Detection**: Automatically detects missing helmets, vests, and unauthorized personnel using YOLOv8.
- **🚧 Proximity & Zone Monitoring**: Alerts when workers enter hazardous Red Zones or get too close to heavy machinery.
- **💬 AI Safety Assistant (RAG)**: Chat with your safety manuals and site reports. "What were the top violations yesterday?"
- **📊 Interactive Dashboard**: React-based UI for visualizing daily metrics, violation trends, and evidence snapshots.
- **🔐 Enterprise Security**: JWT Authentication with automatic rotation, Refresh Tokens (HTTP-Only cookies), and RBAC.

## 🏗️ System Architecture

### Backend (`secureops-backend`)
- **Framework**: FastAPI (High-performance Async I/O)
- **Database**: PostgreSQL (Relational Data) + `pgvector` (Vector Search for RAG)
- **AI/ML**: 
  - `Ultralytics YOLOv8` (Object Detection)
  - `LangChain` + `OpenAI` (RAG & Embeddings)
- **Security**: Argon2 Hashing, OAuth2/JWT

### Frontend (`secureops-frontend`)
- **Framework**: React + Vite
- **Styling**: TailwindCSS
- **State**: React Context API
- **Charts**: Recharts / Tremor

## 🛠️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker or local PostgreSQL instance with `pgvector` extension

### 1. clone the Repository
```bash
git clone https://github.com/KeshavSingh2703/AI-Powered-Construction-Site-Monitoring.git
cd AI-Powered-Construction-Site-Monitoring
```

### 2. Backend Setup
```bash
cd secureops-backend

# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Environment Setup
cp .env.example .env
# Edit .env with your DB credentials and OpenAI API Key

# Database Init
python -m src.main  # First run initializes DB tables
```

### 3. Frontend Setup
```bash
cd secureops-frontend

# Install Dependencies
npm install

# Start Dev Server
npm run dev
```

Visit `http://localhost:5173` to access the dashboard.

## 📂 Project Structure

```
├── secureops-backend/
│   ├── src/
│   │   ├── api/          # FastAPI Routes (Auth, Video, Chat)
│   │   ├── core/         # Config, Security, Logging
│   │   ├── db/           # SQLAlchemy Models & Sessions
│   │   ├── stages/       # Data Pipeline (Vision, RAG, Analytics)
│   │   └── utils/        # Helper functions
│   ├── alembic/          # DB Migrations
│   └── tests/            # Pytest suites
│
├── secureops-frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI Blocks
│   │   ├── context/      # Auth & Global State
│   │   ├── pages/        # Main Views (Dashboard, Login)
│   │   └── api.js        # Axios Setup
```

## 🔐 Security Considerations

- **Tokens**: Access Tokens are short-lived (30m) and stored **in-memory only**. Refresh Tokens are long-lived (7d) and stored in **HTTP-Only, Secure Cookies**.
- **Rotation**: Refresh tokens are rotated on every use to prevent replay attacks.
- **Validation**: All inputs are validated via Pydantic (Backend) and React Props (Frontend).

## 🗺️ Roadmap

- [x] Core PPE Detection
- [x] Basic RAG Implementation
- [x] Secure Authentication System
- [ ] Multi-camera Stream Support (RTSP)
- [ ] Edge Deployment (Jetson Nano)
- [ ] Advanced Incident Reporting (PDF Exports)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
