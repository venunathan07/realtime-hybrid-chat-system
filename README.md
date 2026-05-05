# ZapTalk

A Scalable Real-Time Messaging System with WebSocket-Based Delivery

---

## 1. Project Overview

ZapTalk is a high-performance real-time chat system designed to handle low-latency communication, message lifecycle consistency, and scalable group messaging.

The project focuses on backend engineering concepts such as real-time communication, reliability, and system scalability rather than just UI features.

---

## 2. Problem Statement

Real-time communication systems face multiple challenges:

* High latency in polling-based architectures
* Message duplication due to retries or unstable networks
* Difficulty in tracking message lifecycle (sent → delivered → read)
* Inefficient delivery in group messaging scenarios
* Scalability issues with increasing concurrent users

---

## 3. Proposed Solution

ZapTalk addresses these challenges using:

* WebSocket-based real-time communication
* Message lifecycle tracking system
* Deduplication using client-generated identifiers
* Rate limiting to prevent abuse
* Efficient group message fan-out architecture

---

## 4. Key Features

### 4.1 Real-Time Messaging

* Instant message delivery using WebSockets
* Typing indicators and live updates

### 4.2 Message Lifecycle

* Sent, delivered, and read tracking
* Synchronization across multiple clients

### 4.3 Message Management

* Edit messages with timestamps
* Soft delete (preserves history)
* Emoji reactions

### 4.4 Media Support

* Image upload (JPEG, PNG, GIF, WebP)
* Image preview and storage

### 4.5 Group Chat

* Create and manage groups
* Broadcast messages to multiple users

---

## 5. Engineering Highlights

* WebSocket-based architecture eliminates polling overhead and enables real-time bidirectional communication

* Deduplication system using client_message_id ensures idempotent message delivery

* Rate limiting restricts users to 20 messages per minute to prevent spam (implemented in )

* Message lifecycle engine tracks message states and synchronizes them across clients

* Group fan-out logic enables efficient delivery to multiple users

* UUID-based database design supports distributed systems

---

## 6. System Architecture Components

### 6.1 Client Application

* Chat interface
* Message input and media upload
* Real-time updates via WebSocket

### 6.2 Backend Server

* API routing (REST and WebSocket)
* Authentication and authorization
* Message processing pipeline

(Entry point defined in )

### 6.3 Database Layer

* Users
* Conversations (direct and group)
* Messages
* Group members

(Models defined in , , )

### 6.4 Real-Time Layer

* WebSocket connection management
* Online user tracking
* Event broadcasting

(Implemented in )

### 6.5 Message Processing Layer

* Deduplication
* Rate limiting
* Delivery and status updates

---

## 7. Data Flow

1. User sends a message through WebSocket
2. Backend validates input and checks rate limits
3. Message is stored in the database
4. Acknowledgement is sent to the sender
5. Message is delivered to receiver(s)
6. Message status is updated (delivered/read)
7. Client UI reflects updates in real time

---

## 8. Technology Stack

### 8.1 Backend

* FastAPI FastAPI
* SQLAlchemy SQLAlchemy
* PostgreSQL
* WebSockets
* JWT Authentication

### 8.2 Frontend

* HTML, CSS, JavaScript

### 8.3 Database and Migrations

* PostgreSQL
* Alembic

---

## 9. Scalability Considerations

* Stateless backend enables horizontal scaling
* WebSocket scaling can be achieved using Redis Pub/Sub
* UUID-based schema supports distributed environments
* Indexed queries improve performance for large datasets

---

## 10. Security

* JWT-based authentication
* Password hashing using bcrypt
* Protected REST and WebSocket endpoints
* Input validation and access control

---

## 11. Benefits

* Low-latency real-time communication
* Reliable message delivery
* Scalable architecture
* Efficient group messaging
* Real-time user presence tracking

---

## 12. Limitations

* WebSocket scaling requires additional infrastructure
* No offline message queueing
* Single-region deployment

---

## 13. Future Enhancements

* Redis-based WebSocket scaling
* Message pagination and caching
* Push notifications
* End-to-end encryption
* Containerization and cloud deployment

---

## 14. License

This project is developed for academic and learning purposes only.
Not intended for commercial use or redistribution without permission.

---

## 15. Author

Venunathan

---
