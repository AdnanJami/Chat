# GogleMeat — Real-Time Chat & Video Call App

A full-stack real-time communication platform built with Django, WebSockets, WebRTC, and JWT authentication.

## Features

- **JWT Authentication** — Register and login with 2-day token expiry
- **Real-Time Chat** — Instant messaging via WebSockets powered by Django Channels
- **Video Calling** — Peer-to-peer video calls using WebRTC
- **PIN-Protected Rooms** — Create or join rooms with a unique 6-digit PIN
- **Message History** — Messages persist in the database and reload on refresh
- **Join/Leave Notifications** — See when users enter or leave a room
- **Recent Rooms** — Quick rejoin from history without re-entering credentials
- **Redis Channel Layer** — Scalable WebSocket message broadcasting

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, Django Channels 4.3, Daphne |
| Real-Time | WebSockets, WebRTC |
| Auth | JWT (djangorestframework-simplejwt) |
| Cache/Broker | Redis (Redis Cloud) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Deployment | Docker, Render |

## Getting Started

### Prerequisites

- Python 3.13+
- Docker & Docker Compose
- Redis (or Redis Cloud account)

### Local Setup

```bash
# Clone the repo
git clone https://github.com/AdnanJami/Chat.git
cd Chat

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
python -m pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Redis credentials

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

### Docker Setup

```bash
# Build and run everything (Django + Redis)
docker-compose up --build

# Run in background
docker-compose up --build -d

# Stop
docker-compose down
```

### Environment Variables

Create a `.env` file in the project root:

```env
DJANGO_SETTINGS_MODULE=core.settings
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
```

## Project Structure

```
GOGLEMEAT/
├── core/
│   ├── settings.py
│   ├── asgi.py
│   └── urls.py
├── chat/
│   ├── consumers.py      # WebSocket consumers (chat + signaling)
│   ├── models.py         # ChatRoom, Message
│   ├── views.py          # Auth, room management
│   ├── routing.py        # WebSocket URL routing
│   ├── urls.py
│   └── templates/
│       └── chat/
│           ├── index.html
│           ├── room.html
│           ├── call.html
│           ├── login.html
│           └── register.html
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## How It Works

### Chat Flow
1. User registers/logs in → receives JWT stored in session
2. Create a room (generates unique PIN) or join with room name + PIN
3. WebSocket connects authenticated via JWT token
4. Messages broadcast via Redis channel layer to all room members
5. Messages saved to database — history loads on reconnect

### Video Call Flow
1. Click Video Call from chat room
2. WebRTC peer connection established via WebSocket signaling
3. STUN servers help peers discover public IPs
4. ICE candidates exchanged → direct P2P video stream established
5. Video/audio never passes through the server
