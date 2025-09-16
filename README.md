# 🛡️ SEC-COPILOT  
*A Multi-Agent LLM-based Cybersecurity Copilot for SOC Teams*

---

## 📌 Overview
SEC-COPILOT integrates LLMs with real-time threat intelligence and role-specific multi-agent reasoning (Attacker, Defender, Intel Analyst, Decider, Toolsmith).  
It helps SOC teams **reduce alert fatigue**, investigate incidents, and generate step-by-step defense strategies — inside a **ChatGPT-style web UI**.

---

<details>
<summary>✨ Features</summary>

- 🔐 **JWT Authentication** (signup, login, logout)  
- 💬 **Chat Conversations** (saved in MongoDB, organized by folders/history)  
- 🧑‍🤝‍🧑 **Multi-Agent System**:
  - **Attacker** → simulates adversary behavior  
  - **Defender** → mitigations and response  
  - **Intel Analyst** → gathers context (Reddit, StackOverflow, APIs)  
  - **Toolsmith** → suggests tools/scripts  
  - **Decider** → final recommendations  
- 📑 **Trace Mode** → shows agent reasoning (step logs, tool calls)  
- 🎨 **Modern Web UI** → bubble chat, typing indicators, folders/history sidebar  
- 🗄️ **MongoDB Storage** → users, conversations, messages, traces  
- 🐳 **Dockerized Deployment** → run API + MongoDB + UI in one command  

</details>

---

<details>
<summary>🛠️ Tech Stack</summary>

- **Frontend**:  
  - HTML, CSS, Vanilla JS  
  - LocalStorage for session/token  
  - ChatGPT-like UI with folders & trace panel  

- **Backend**:  
  - FastAPI (Python 3.12)  
  - JWT Auth (python-jose, passlib/bcrypt)  
  - Orchestrator for multi-agent reasoning  

- **Database**:  
  - MongoDB (async with Motor driver)  

- **Deployment**:  
  - Docker + Docker Compose  
  - uv (dependency manager)  

</details>

---

<details>
<summary>📂 Project Structure</summary>

```bash
sec-copilot/
├── app/
│   ├── api/routers/       # FastAPI routers (auth, chat, data)
│   ├── orchestrator/      # Agents: planner, defender, attacker, etc.
│   ├── security/          # JWT, password hashing
│   ├── ui/web/            # Frontend (HTML, CSS, JS)
│   ├── db.py              # MongoDB connection + init_db
│   ├── main.py            # FastAPI entrypoint
│   └── models.py          # Data models (user, conversation, message, trace)
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies (if not using uv)
├── docker-compose.yml     # Dev environment (API + Mongo)
└── README.md              # Documentation
````

</details>

---

<details>
<summary>⚙️ Setup Instructions</summary>

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/sec-copilot.git
cd sec-copilot
uv sync   # or pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in project root:

```ini
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DB=sec_copilot
JWT_SECRET=super_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
```

### 3. Run with Docker

```bash
docker-compose up --build
```

### 4. Run API locally

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Visit UI → [http://localhost:8000](http://localhost:8000)

</details>

---

<details>
<summary>🧪 Testing</summary>

* ✅ Unit tests for agents & policies
* ✅ API contract tests with FastAPI `TestClient`
* ✅ End-to-end: login → chat → save trace → reload conversation

Run:

```bash
pytest -v
```

</details>

---

<details>
<summary>🚀 Roadmap</summary>

* [x] JWT auth system
* [x] Multi-agent orchestration skeleton
* [x] MongoDB persistence for conversations
* [x] UI with folders/history + trace toggle
* [ ] Threat intel API connectors (Reddit, StackOverflow)
* [ ] Simulation mode (attacker vs defender "game")
* [ ] Cloud deployment (Kubernetes + Mongo replicaset)
* [ ] Role-based access control (admin vs analyst)

</details>

---

<details>
<summary>👥 Contributors</summary>

* **Harshith B** — Project Lead (BE CSE @ BMSCE)
* *Aashirvaad Kumar S*
* *Govind Jairam Rathod*

</details>

---

<details>
<summary>📜 License</summary>

This project is licensed under the --- License — see [LICENSE](LICENSE) for details.

</details>

---