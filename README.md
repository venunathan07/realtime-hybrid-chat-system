<div align="center">

# ⚡ ZapTalk

### A Scalable Real-Time Messaging System with WebSocket-Based Delivery

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![WebSockets](https://img.shields.io/badge/WebSockets-E8900A?style=flat-square&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![License](https://img.shields.io/badge/License-Academic-green?style=flat-square)](#license)

*Built for backend engineering depth — real-time communication, message reliability, and scalable architecture*

</div>

---

## 📌 Overview

ZapTalk is a high-performance real-time chat system engineered to handle low-latency communication, message lifecycle consistency, and scalable group messaging.

The project focuses on **backend engineering concepts** — real-time communication, reliability, and system scalability — rather than just UI features.

---

## 🚀 Highlights

| What | Why It Matters |
|---|---|
| ⚡ WebSocket-based messaging | Eliminates polling overhead, enables true real-time bidirectional communication |
| 🔄 4-stage message lifecycle | Tracks every message from sent → delivered → read with full consistency |
| 🧠 Deduplication engine | `client_message_id` ensures idempotent delivery across retries and reconnects |
| 🛡️ Rate limiting | Per-user 20 msg/min cap prevents spam and protects WebSocket infrastructure |
| 👥 Group fan-out | Efficient broadcast architecture for multi-user delivery |
| 🔐 JWT + bcrypt security | Industry-standard auth on every REST and WebSocket endpoint |

---

## ❗ Problem Statement

Real-time communication systems face multiple challenges:

- High latency in polling-based architectures
- Message duplication due to retries or unstable networks
- Difficulty tracking message lifecycle (sent → delivered → read)
- Inefficient delivery in group messaging scenarios
- Scalability issues with increasing concurrent users

---

## ✅ Proposed Solution

ZapTalk addresses these challenges through:

- WebSocket-based real-time communication
- Message lifecycle tracking system
- Deduplication via client-generated identifiers
- Rate limiting to prevent abuse
- Efficient group message fan-out architecture

---

## ✨ Features

<details>
<summary><strong>⚡ Real-Time Messaging</strong></summary>

- Instant message delivery using WebSockets
- Typing indicators and live presence updates
- Real-time communication between multiple users

</details>

<details>
<summary><strong>📬 Message Lifecycle</strong></summary>

- Sent → Delivered → Read tracking
- Synchronization across multiple clients
- Lifecycle consistency across devices

</details>

<details>
<summary><strong>✏️ Message Management</strong></summary>

- Edit messages with timestamps and `(edited)` tag
- Soft delete functionality
- Emoji reactions support

</details>

<details>
<summary><strong>🖼️ Media Support</strong></summary>

- Image upload (JPEG, PNG, GIF, WebP)
- Image preview and storage handling
- Media message delivery

</details>

<details>
<summary><strong>👥 Group Chat</strong></summary>

- Create and manage groups
- Broadcast messages to multiple users
- Efficient group fan-out delivery

</details>

---

## 🏗️ Architecture

> Save your architecture image as `assets/architecture.png` in the repository root.

![ZapTalk Architecture](Architecture%20diagram.png)

### Architecture Highlights

| Component | Role |
|---|---|
| **Client** | Browser or mobile — sends/receives via WebSocket |
| **FastAPI Backend** | API routing, auth, message processing, WS handling |
| **Authentication Layer** | JWT validation on every request |
| **Message Processing Layer** | Rate limiting, deduplication, lifecycle tracking |
| **WebSocket Manager** | Connection pool, online tracking, event broadcast |
| **Media Upload Handler** | File validation, storage, delivery |
| **PostgreSQL Database** | Persistent storage for all messages, users, groups |

---

## 🔄 Data Flow

```
1.  User connects to FastAPI backend via WebSocket
2.  JWT authentication validates the sender
3.  Rate limiter checks request frequency (max 20/min)
4.  Deduplication engine checks client_message_id
5.  Message is stored in PostgreSQL
6.  ACK is sent back to the sender
7.  WebSocket Manager broadcasts to recipient(s)
8.  Message status updated: sent → delivered → read
9.  All connected clients receive updates in real time
```

---

## 🗂️ Project Structure

```
project-root/
│
├── app/
│   ├── auth/               # Authentication and JWT handling
│   ├── chat/               # Chat APIs and messaging logic
│   ├── core/               # Core backend utilities
│   ├── db/                 # Database configuration
│   ├── models/             # SQLAlchemy database models
│   ├── websocket/          # Real-time communication layer
│   └── uploads/            # Uploaded media storage
│
├── alembic/                # Database migrations
├── assets/                 # Architecture diagram and screenshots
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (async Python) |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy (async) |
| **Migrations** | Alembic |
| **Auth** | JWT (`python-jose`) + bcrypt (`passlib`) |
| **Real-time** | Starlette WebSockets |
| **Frontend** | Vanilla HTML, CSS, JavaScript |
| **Server** | Uvicorn (ASGI) |

---

## 🔌 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Register a new user |
| `POST` | `/login` | Authenticate and receive JWT token |

### Messaging

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/messages` | Fetch chat messages |
| `POST` | `/messages` | Send a message |
| `PUT` | `/messages/{id}` | Edit a message |
| `DELETE` | `/messages/{id}` | Soft delete a message |

### WebSocket

| Protocol | Endpoint | Description |
|---|---|---|
| `WebSocket` | `/ws/chat` | Real-time bidirectional messaging |

---

## 🔐 Security

- JWT-based stateless authentication
- Password hashing using bcrypt
- Protected REST and WebSocket endpoints
- Input validation and access control
- Per-user rate limiting (20 messages/minute)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+

### Setup

```bash
# 1. Clone
git clone https://github.com/venunathan07/realtime-chat-backend.git
cd realtime-chat-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Create .env file:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/zaptalk
# SECRET_KEY=your-secret-key

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn main:app --reload
```

**API Docs →** `http://localhost:8000/docs`

---

## 📈 Scalability

### Current Limitations

| Area | Limitation |
|---|---|
| WebSocket | Single-instance only |
| Media | Stored locally on server |
| Cache | No distributed layer |
| Deployment | Single-region |

### Scaling Roadmap

| Solution | Addresses |
|---|---|
| Redis Pub/Sub | Multi-server WebSocket sync |
| Load balancer | Horizontal backend scaling |
| CDN | Media delivery at scale |
| Kubernetes | Container orchestration |
| Database replication | Read throughput |

---

## 📋 Logging & Monitoring

ZapTalk logs the following backend events:

- WebSocket connections and disconnections
- Authentication successes and failures
- Message delivery lifecycle transitions
- API request failures
- Rate limit violations

**Future:** Prometheus metrics · Grafana dashboards · ELK Stack centralized logging

---

## ⚠️ Known Issues

| Issue | Planned Fix |
|---|---|
| WebSocket scaling is single-instance | Redis Pub/Sub |
| No offline message sync | Service Worker + IndexedDB |
| Media stored locally | S3 / Cloudflare R2 |
| No push notifications | Web Push API + VAPID |
| No distributed cache | Redis integration |

---

## 🗺️ Future Improvements

- [ ] Redis-based distributed WebSocket scaling
- [ ] Push notifications (Web Push API)
- [ ] End-to-end encryption
- [ ] Cloud deployment (AWS / GCP)
- [ ] Docker Compose setup
- [ ] Kubernetes orchestration
- [ ] Email and phone verification
- [ ] Stories and media-rich messaging
- [ ] Prometheus + Grafana monitoring
- [ ] ELK Stack centralized logging

---

## 📄 License

Developed for academic and learning purposes only.
Not intended for commercial use or redistribution without permission.

---

<div align="center">

Built by **[Venunathan](https://github.com/venunathan07)**


⭐ Star this repo if it helped you learn something

</div>
