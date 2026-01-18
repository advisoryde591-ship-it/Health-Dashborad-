# Health Dashboard

A comprehensive health tracking dashboard that analyzes screenshots from Whoop, Apple Watch, and smart scales using AI to provide insights into your health journey.

## Features

- **Screenshot Analysis**: Automatically extract health metrics from Whoop, Apple Watch, and scale screenshots using Claude AI
- **Daily Summaries**: Receive morning Telegram notifications with your health summary
- **Food Logging**: Log meals via Telegram or web app with AI-powered calorie estimation
- **Trend Visualization**: Track weight, recovery, sleep, and activity trends over time
- **Goal Tracking**: Set and monitor progress toward your target weight
- **Web Dashboard**: Beautiful dark-themed dashboard with authentication

## Screenshots Supported

| App | Metrics Extracted |
|-----|-------------------|
| **Whoop Recovery** | Recovery %, HRV, Resting HR, Respiratory Rate, Sleep Performance |
| **Whoop Sleep** | Sleep Duration, Sleep Stages (Awake/Light/Deep/REM), Sleep Times |
| **Whoop Dashboard** | Steps, Calories, VO2 Max, HR Zones |
| **Smart Scale** | Weight, Body Fat %, Muscle Mass, BMI, Bone Mass, Body Water % |
| **Apple Watch** | Workout Type, Duration, Calories, Heart Rate, Effort |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Google Drive   │────▶│   Backend API   │────▶│   Dashboard     │
│  (Screenshots)  │     │   (FastAPI)     │     │   (React)       │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Claude AI     │
                        │ (Image Analysis │
                        │  + Chatbot)     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Telegram Bot   │
                        │ (Notifications  │
                        │  + Food Log)    │
                        └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key (Claude)
- Google Cloud account (for Drive API)
- Telegram account (for bot)

### 1. Clone and Setup

```bash
cd Health-Dashborad-

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=your-chat-id
GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Optional (defaults shown)
TARGET_WEIGHT_KG=76.0
DAILY_CALORIE_TARGET=2000
TIMEZONE=Asia/Nicosia
```

### 3. Setup Google Drive

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the JSON and save as `backend/credentials.json`
6. Run the setup script:

```bash
cd backend
python -c "from app.services.google_drive import setup_google_drive_credentials; setup_google_drive_credentials()"
```

7. Create a folder in Google Drive for your screenshots and copy the folder ID from the URL

### 4. Setup Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token to your `.env` file
4. Message your new bot to start it
5. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
6. Add the chat ID to your `.env` file

### 5. Run the Application

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate
python run_server.py
```

**Terminal 2 - Telegram Bot:**
```bash
cd backend
source venv/bin/activate
python run_bot.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### 6. Access the Dashboard

1. Open http://localhost:3000
2. Create an account
3. Start uploading screenshots or drop them in your Google Drive folder!

## Usage

### Daily Workflow

1. **Morning**: Take screenshots from Whoop, Apple Watch, and your scale
2. **Upload**: Either:
   - Drop screenshots into your Google Drive folder (auto-processed every 30 minutes)
   - Upload directly through the web dashboard
3. **Log Food**: Tell your Telegram bot what you ate throughout the day
4. **Review**: Check your dashboard for insights and trends

### Telegram Bot Commands

- `/start` - Start the bot
- `/log <food>` - Log what you ate
- `/today` - Get today's summary
- `/weight` - See weight progress
- `/help` - Show help

Or just send a message describing what you ate - the bot will automatically log it!

### Example Food Logging

```
User: Had 2 eggs, toast with avocado, and black coffee for breakfast
Bot: Breakfast logged!
     Estimated: 450 kcal
     P: 18g | C: 25g | F: 32g
     Great protein start to your day!
```

## Deployment

### Option A: Railway (Recommended)

1. Push your code to GitHub
2. Connect to [Railway](https://railway.app)
3. Add environment variables
4. Deploy!

### Option B: Docker

```bash
docker-compose up -d
```

### Option C: QNAP NAS

1. Install Container Station
2. Pull the Docker images
3. Configure environment variables
4. Set up port forwarding

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get token |
| `/api/metrics/today` | GET | Get today's metrics |
| `/api/metrics/trends` | GET | Get trend data |
| `/api/food/log` | POST | Log food entry |
| `/api/screenshots/upload` | POST | Upload screenshot |
| `/api/screenshots/process-drive` | POST | Process Google Drive screenshots |

## Tech Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy + SQLite
- Anthropic Claude API
- Google Drive API
- python-telegram-bot

**Frontend:**
- React 18
- Vite
- Tailwind CSS
- Recharts
- React Router

## Estimated Costs

| Service | Monthly Cost |
|---------|-------------|
| Claude API | ~$10-20 (depends on usage) |
| Railway hosting | ~$5-10 |
| **Total** | **~$15-30** |

## Troubleshooting

### Screenshots not processing?
- Check that images are PNG or JPEG
- Verify Google Drive folder ID is correct
- Check backend logs for errors

### Telegram bot not responding?
- Verify bot token is correct
- Make sure you've messaged the bot at least once
- Check that the bot process is running

### Login not working?
- Clear browser cache
- Check that backend is running on port 8000
- Verify database is initialized

## Contributing

Pull requests welcome! Please read our contributing guidelines first.

## License

MIT License - see LICENSE file for details.

---

Made with health in mind
