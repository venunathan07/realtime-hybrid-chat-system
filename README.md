ZapTalk
A Scalable Real-Time Messaging System with WebSocket-Based Delivery
---
1. Project Overview
ZapTalk is a high-performance real-time chat system designed to handle low-latency communication, message lifecycle consistency, and scalable group messaging.
The project focuses on backend engineering concepts such as real-time communication, reliability, and system scalability rather than just UI features.
---
2. Problem Statement
Real-time communication systems face multiple challenges:
High latency in polling-based architectures
Message duplication due to retries or unstable networks
Difficulty in tracking message lifecycle (sent → delivered → read)
Inefficient delivery in group messaging scenarios
Scalability issues with increasing concurrent users
---
3. Proposed Solution
ZapTalk addresses these challenges using:
WebSocket-based real-time communication
Message lifecycle tracking system
Deduplication using client-generated identifiers
Rate limiting to prevent abuse
Efficient group message fan-out architecture
---
4. Key Features
4.1 Real-Time Messaging
Instant message delivery using WebSockets
Typing indicators and live updates
Real-time communication between multiple users
4.2 Message Lifecycle
Sent, delivered, and read tracking
Synchronization across multiple clients
Lifecycle consistency across devices
4.3 Message Management
Edit messages with timestamps
Soft delete functionality
Emoji reactions support
4.4 Media Support
Image upload support (JPEG, PNG, GIF, WebP)
Image preview and storage handling
Media message delivery
4.5 Group Chat
Create and manage groups
Broadcast messages to multiple users
Efficient group communication
---
5. Engineering Highlights
WebSocket-based architecture eliminates polling overhead and enables real-time bidirectional communication
Deduplication system using client_message_id ensures idempotent message delivery
Rate limiting restricts users to prevent spam and backend abuse
Message lifecycle engine tracks message states and synchronizes them across clients
Group fan-out logic enables efficient delivery to multiple users
UUID-based database design supports distributed systems
---
6. Architecture Diagram

The following diagram represents the high-level backend architecture of ZapTalk.
![Architecture Diagram](output_screenshots/architecture-diagram.png)
---
7. Logging & Monitoring
ZapTalk includes backend logging mechanisms to monitor:
WebSocket connections
Authentication events
Message delivery lifecycle
API request failures
Rate limit violations
---
8. Rate Limiting
Current rule:
Maximum 20 messages per minute per user
---
9. Saturation Point
The current architecture is designed for moderate-scale real-time communication workloads.
Potential bottlenecks:
WebSocket connection limits
Database write throughput
Memory usage for active sessions
File upload bandwidth
---
10. Horizontal & Vertical Scaling
Vertical Scaling
More CPU
More RAM
Faster SSD storage
Horizontal Scaling
Multiple backend instances
Redis Pub/Sub
Load balancers
Kubernetes
---
11. How ZapTalk Works
User connects through WebSocket
JWT authentication validates the user
Messages are processed by backend services
Deduplication prevents duplicate delivery
Messages are stored in PostgreSQL
WebSocket manager broadcasts updates
Clients receive real-time updates instantly
---
12. Screenshots
Architecture Diagram
![Architecture](output_screenshots/architecture-diagram.png)
Chat Interface
![Chat UI](output_screenshots/chat-ui.png)
---
13. API Documentation
Authentication APIs
Method	Endpoint	Description
POST	/register	Register new user
POST	/login	User authentication
Chat APIs
Method	Endpoint	Description
GET	/messages	Fetch chat messages
POST	/messages	Send message
PUT	/messages/{id}	Edit message
DELETE	/messages/{id}	Soft delete message
WebSocket Endpoint
Protocol	Endpoint
WebSocket	/ws/chat
---
14. Known Issues / Limitations
No offline message synchronization
No push notification support
Media uploads are stored locally
Single-region deployment architecture
---
15. Future Improvements
Social Features
User followers and following system
Public user discovery
Global chat visibility for registered users
Improved user connection system
User Verification
Profile picture verification
Email and phone verification
Identity validation to reduce fake accounts
Safety Features
Advanced blocking system
Permanent block relationship tracking
Abuse prevention mechanisms
Content Features
Stories support
Short video reels
Media-rich messaging
Infrastructure Improvements
Redis-based distributed WebSocket scaling
Cloud deployment
Kubernetes orchestration
Distributed caching
Push notifications
End-to-end encryption
---
16. Folder Structure
```bash
project-root/
│
├── app/
│   ├── auth/
│   ├── chat/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── websocket/
│   └── uploads/
│
├── alembic/
├── output\_screenshots/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```
---
17. License
This project is developed for academic and learning purposes only.
---
18. Author
Venunathan
GitHub: https://github.com/venunathan07
