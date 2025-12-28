# 🏆 FPL Gameweek Leaderboard

A **split-architecture** Fantasy Premier League leaderboard app that bypasses Render's free-tier limitations by running heavy processing on your local machine while keeping the UI hosted 24/7.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://fpl-minileague-runnerv2.onrender.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🎯 Features

- ✅ **Handle 1000+ manager leagues** - No size limits
- ✅ **Real-time processing** - 20 parallel workers on your hardware
- ✅ **3-way sorting** - By GW Points, Total Points, or Net Points
- ✅ **Top 3 highlighting** - Gold/Silver/Bronze medals
- ✅ **Email alerts** - Get notified when worker is offline
- ✅ **Status monitoring** - Real-time server health dashboard
- ✅ **Cyberpunk UI** - Beautiful neon-themed interface
- ✅ **100% free** - Render free tier + ngrok free tier

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER BROWSER                         │
│              (Accessible 24/7 anywhere)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              RENDER.COM (Free Tier)                      │
│  ┌────────────────────────────────────────────┐         │
│  │  Flask UI App (Lightweight)                │         │
│  │  • Displays leaderboard                    │         │
│  │  • Forwards processing requests            │         │
│  │  • Sends email alerts                      │         │
│  └────────────────────┬───────────────────────┘         │
└────────────────────────┼────────────────────────────────┘
                         │
                         │ HTTPS via ngrok
                         ▼
┌─────────────────────────────────────────────────────────┐
│              YOUR LOCAL MACHINE                          │
│  ┌────────────────────────────────────────────┐         │
│  │  ngrok Tunnel                              │         │
│  │  https://xyz.ngrok-free.app                │         │
│  └────────────────────┬───────────────────────┘         │
│                       │                                  │
│                       ▼                                  │
│  ┌────────────────────────────────────────────┐         │
│  │  Worker Server (Flask)                     │         │
│  │  • Fetches FPL API data                    │         │
│  │  • 20 parallel workers                     │         │
│  │  • Processes unlimited managers            │         │
│  │  • Returns JSON results                    │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**Why this approach?**
- Render free tier has 512MB RAM + 30s timeout limits
- Processing 500+ managers exceeds these limits
- Solution: Render hosts UI (lightweight), your PC does processing (unlimited)

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Clone Repository**
```bash
git clone https://github.com/yourusername/fpl-leaderboard.git
cd fpl-leaderboard
```

### **Step 2: Start Local Worker**
```bash
cd local-worker
pip install -r requirements.txt
python worker.py
```

### **Step 3: Expose with ngrok**
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5001
```
Copy the HTTPS URL (e.g., `https://abc-123.ngrok-free.app`)

### **Step 4: Deploy UI to Render**
1. Fork this repository on GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml`
5. Add environment variable:
   - `WORKER_URL` = Your ngrok URL from Step 3
6. Click "Create Web Service"

### **Step 5: Use the App! 🎉**
Visit: `https://your-app.onrender.com`

---

## 📁 Project Structure

```
fpl-leaderboard/            # Deploy to Render (UI only)
│   ├── app.py              # Flask app - forwards requests
│   ├── templates/
│   │   ├── index.html      # Main leaderboard page
│   │   └── status.html     # Server status monitor
│   ├── requirements.txt    # Python dependencies
│   └── render.yaml         # Render configuration
│
├── local-worker/           # Run on your machine (processing)
│   ├── worker.py          # Heavy FPL data processing
│   ├── requirements.txt   # Python dependencies
│
├── test_email.py          # Test email configuration
├── SETUP_GUIDE.md         # Detailed setup instructions
├── EMAIL_SETUP.md         # Email alerts configuration
└── README.md              # This file
```

---

## ⚙️ Configuration

### **Required Environment Variables (Render)**

| Variable | Description | Example |
|----------|-------------|---------|
| `WORKER_URL` | ngrok tunnel URL | `https://abc.ngrok-free.app` |

### **Optional: Email Alerts**

Get notified when worker goes offline:

| Variable | Description | Example |
|----------|-------------|---------|
| `ALERT_EMAIL` | Where to send alerts | `your-email@gmail.com` |
| `SMTP_EMAIL` | Gmail account to send from | `smtp-account@gmail.com` |
| `SMTP_PASSWORD` | Gmail app password | See [EMAIL_SETUP.md](EMAIL_SETUP.md) |
| `SMTP_SERVER` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |

**Setup Gmail app password:**
1. Enable 2FA: https://myaccount.google.com/security
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use the 16-character password

**Test before deploying:**
```bash
# Edit test_email.py with your credentials
python test_email.py
```

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed guide.

---

## 🎮 Usage

### **1. Access the App**
Visit your Render URL: `https://your-app.onrender.com`

### **2. Enter Details**
- **Gameweek**: Current gameweek number (1-38)
- **League ID**: Find in your FPL league URL
  ```
  https://fantasy.premierleague.com/leagues/208271/standings/c
                                           ^^^^^^
                                         Your League ID
  ```

### **3. View Results**
- Leaderboard sorted by gameweek points
- Click sort buttons to reorder
- Top 3 highlighted with medals

### **4. Check Server Status**
Click "Check Server Status" button to see:
- UI server health
- Worker server health
- Connection status

---

## 🔧 Troubleshooting

### **"Worker server not available"**

**Cause:** Local worker isn't running or ngrok tunnel is down

**Fix:**
```bash
# Terminal 1: Start worker
cd local-worker
python worker.py

# Terminal 2: Start ngrok
ngrok http 5001
```

Update `WORKER_URL` in Render if ngrok URL changed.

---

### **No email alerts**

**Test locally first:**
```bash
python test_email.py
```

**Common issues:**
- Wrong Gmail app password (not regular password)
- 2FA not enabled on Gmail
- Spaces in app password (remove them)

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for solutions.

---

### **Timeout errors**

**Cause:** League too large or worker overloaded

**Fix:** Large leagues (500+ managers) may take 2-3 minutes. This is normal.

---

### **ngrok URL changes**

**Cause:** Free ngrok URLs change on restart

**Solutions:**
1. **Free:** Update `WORKER_URL` in Render each time
2. **Paid ($8/mo):** Get static ngrok URL - update once

---

## 💡 Tips & Best Practices

### **Keep Worker Running**
- Use terminal multiplexer (tmux/screen) on Linux
- Use Windows Task Scheduler for auto-start
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for auto-start setup

### **Monitor Uptime**
Use free monitoring services:
- [UptimeRobot](https://uptimerobot.com) - Monitor `/health` endpoint
- [Better Stack](https://betterstack.com) - Advanced monitoring
- Both offer free tiers with email/Slack alerts

### **Optimize Performance**
Worker uses 20 parallel requests by default. Adjust in `worker.py`:
```python
MAX_WORKERS = 20  # Increase for faster processing
```

### **Security**
- ✅ Never commit passwords to git
- ✅ Use Render environment variables for secrets
- ✅ ngrok provides HTTPS encryption automatically
- ✅ Worker only accepts requests from your Render app

---

## 📊 Performance

| League Size | Processing Time | Memory Used |
|-------------|-----------------|-------------|
| 50 managers | ~15 seconds | ~50 MB |
| 200 managers | ~45 seconds | ~150 MB |
| 500 managers | ~2 minutes | ~300 MB |
| 1000+ managers | ~4 minutes | ~500 MB |

**On Render free tier alone:** Max ~200 managers before timeout/OOM

**With this architecture:** Unlimited! Runs on your hardware.

---

## 🛠️ Development

### **Run UI locally**
```bash
cd render-app
pip install -r requirements.txt
export WORKER_URL=http://localhost:5001  # Linux/Mac
# OR
set WORKER_URL=http://localhost:5001     # Windows
python app.py
```

### **Run Worker locally**
```bash
cd local-worker
pip install -r requirements.txt
python worker.py
```

Visit: `http://localhost:5000`

---

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [EMAIL_SETUP.md](EMAIL_SETUP.md) - Email alerts configuration
- [test_email.py](test_email.py) - Test email before deploying

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Fantasy Premier League API](https://fantasy.premierleague.com/api/)
- [Render](https://render.com) - Free hosting
- [ngrok](https://ngrok.com) - Secure tunneling
- [Flask](https://flask.palletsprojects.com/) - Web framework

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/fpl-leaderboard/issues)
- **Email:** your-email@example.com
- **Status Page:** Check `/status` on your deployed app

---

**Made with ❤️ for Fantasy Premier League managers**
