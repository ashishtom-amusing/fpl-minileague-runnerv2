# FPL Leaderboard - Split Architecture Setup

## Architecture Overview

```
User Browser
    ↓
Render (Flask UI) ──→ ngrok ──→ Your Local Machine (Worker)
    ↑                              ↓
    └──────────── Results ─────────┘
```

## Part 1: Local Worker Setup (Your Computer)

### 1. Install Python Dependencies
```bash
cd local-worker
pip install -r requirements.txt
```

### 2. Start Worker Server
```bash
python worker.py
```

You should see:
```
================================================================================
FPL Worker Server Starting...
Max parallel workers: 20
================================================================================

 * Running on http://0.0.0.0:5001
```

### 3. Expose via ngrok

**Install ngrok:**
- Download from https://ngrok.com/download
- Sign up for free account
- Get auth token from https://dashboard.ngrok.com/get-started/your-authtoken

**Setup ngrok:**
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

**Start ngrok tunnel:**
```bash
ngrok http 5001
```

You'll see:
```
Forwarding  https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5001
```

**Copy the https URL** (e.g., `https://1234-56-78-90-12.ngrok-free.app`)

---

## Part 2: Render Deployment

### 1. Update render.yaml

Edit `render-app/render.yaml`:
```yaml
envVars:
  - key: WORKER_URL
    value: https://YOUR-NGROK-URL.ngrok-free.app  # ← Paste your ngrok URL here
```

### 2. Push to GitHub

```bash
# Create new repo for render-app folder
cd render-app
git init
git add .
git commit -m "Initial commit - UI app"
git remote add origin https://github.com/YOUR_USERNAME/fpl-leaderboard-ui.git
git push -u origin main
```

### 3. Deploy to Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your `fpl-leaderboard-ui` repository
4. Render auto-detects `render.yaml`
5. Click "Create Web Service"
6. Wait for deployment (~2 mins)

### 4. Set Environment Variable (Alternative)

Instead of editing render.yaml, you can set in Render dashboard:
1. Go to your service → Environment
2. Add variables:
   - Key: `WORKER_URL`, Value: `https://your-ngrok-url.ngrok-free.app`
   
**Optional - Email Alerts (see EMAIL_SETUP.md):**
   - Key: `ALERT_EMAIL`, Value: `your-email@gmail.com`
   - Key: `SMTP_EMAIL`, Value: `your-email@gmail.com`
   - Key: `SMTP_PASSWORD`, Value: `your-gmail-app-password`

---

## Email Alerts (Optional but Recommended)

Get notified when worker is down! See **EMAIL_SETUP.md** for full guide.

**Quick setup:**
1. Enable Gmail 2FA
2. Generate app password at https://myaccount.google.com/apppasswords
3. Add to Render environment variables
4. Receive instant alerts when worker is offline

---

## Usage

### Keep Running:
1. **Worker**: Keep `python worker.py` running on your machine
2. **ngrok**: Keep `ngrok http 5001` running
3. **Render**: Automatically running

### Access:
- Visit: `https://fpl-leaderboard-ui.onrender.com`
- Enter gameweek + league ID
- Submit → Render calls your local worker → Results displayed

---

## Benefits

✅ **No Render limits** - Heavy processing on your machine  
✅ **Fast** - 20 parallel workers (vs 5 on Render)  
✅ **No timeouts** - Takes as long as needed  
✅ **Free** - Render free tier + free ngrok  
✅ **Real progress** - Can add progress tracking easily

---

## Troubleshooting

### "Worker server not available"
- Check if `worker.py` is running
- Check if ngrok is running
- Verify WORKER_URL in Render matches ngrok URL

### ngrok URL changes
- Free ngrok URLs change on restart
- Update WORKER_URL in Render environment variables
- Or use ngrok paid plan for static URL

### Worker crashes
- Check terminal for errors
- Worker will restart automatically (Ctrl+C then re-run)

---

## Advanced: Auto-restart Worker (Optional)

**Linux/Mac (using systemd or launchd):**
Create service to auto-start worker on boot

**Windows (using NSSM):**
```bash
# Install NSSM
# Create service
nssm install FPLWorker "python" "C:\path\to\worker.py"
```

---

## File Structure

```
├── render-app/              # Deploy to Render
│   ├── app.py              # Lightweight Flask (UI only)
│   ├── templates/
│   │   └── index.html      # Frontend
│   ├── requirements.txt
│   └── render.yaml
│
├── local-worker/           # Run on your machine
│   ├── worker.py          # Heavy processing
│   └── requirements.txt
```

---

## Notes

- **ngrok free tier**: URL changes on restart. Update WORKER_URL each time.
- **ngrok paid ($8/month)**: Get static URL, no need to update
- **Security**: ngrok provides HTTPS by default
- **Performance**: Local machine = unlimited CPU/RAM for processing

---

## Next Steps

1. ✅ Start worker locally
2. ✅ Expose with ngrok  
3. ✅ Deploy UI to Render
4. ✅ Set WORKER_URL
5. 🎉 Use the app!
