# Email Alert Setup Guide

## 📧 Get Notified When Worker is Down

When someone tries to use the app but your local worker is offline, you'll receive an instant email alert.

---

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" if not already enabled

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (custom name)"
3. Name it "FPL Leaderboard"
4. Click "Generate"
5. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 3: Configure Render Environment Variables

Go to your Render dashboard → Your service → Environment:

```
ALERT_EMAIL = your-email@gmail.com          # Where to receive alerts
SMTP_EMAIL = your-email@gmail.com           # Gmail account to send from
SMTP_PASSWORD = abcd efgh ijkl mnop         # App password from Step 2
SMTP_SERVER = smtp.gmail.com                # Gmail SMTP server
SMTP_PORT = 587                             # Gmail SMTP port
```

---

## Alternative: Outlook/Hotmail

```
SMTP_SERVER = smtp-mail.outlook.com
SMTP_PORT = 587
SMTP_EMAIL = your-email@outlook.com
SMTP_PASSWORD = your-password
```

---

## Alternative: Custom SMTP Server

```
SMTP_SERVER = smtp.your-domain.com
SMTP_PORT = 587 (or 465 for SSL)
SMTP_EMAIL = alerts@your-domain.com
SMTP_PASSWORD = your-password
```

---

## What Alerts You'll Get

### Alert Type 1: Connection Failed
```
Subject: 🚨 FPL Worker Alert - Connection Failed

Error Type: Connection Failed
Error Message: Cannot connect to worker at https://xyz.ngrok-free.app
Time: 2025-12-25 23:45:12

Action Required:
1. Check if worker.py is running on your local machine
2. Check if ngrok tunnel is active
3. Verify WORKER_URL environment variable matches ngrok URL
```

### Alert Type 2: Timeout
```
Subject: 🚨 FPL Worker Alert - Timeout

Error Type: Timeout
Error Message: Processing timeout after 5 minutes
Time: 2025-12-25 23:50:00
```

---

## Testing Alerts

### Option 1: Stop Worker
1. Stop your local `worker.py`
2. Try to use the app
3. You should receive an email within seconds

### Option 2: Use Wrong URL
1. Set `WORKER_URL` to a fake URL in Render
2. Try to use the app
3. Receive alert email

---

## Skip Email Setup (Optional)

If you don't want email alerts:
- Just don't set the email environment variables
- The app will log errors to Render console instead
- Check Render logs at: Dashboard → Your Service → Logs

---

## Security Notes

✅ **App Password is Safe**: It only works for email, not full Google account access  
✅ **Can Revoke**: Delete app password anytime at https://myaccount.google.com/apppasswords  
✅ **Render is Secure**: Environment variables are encrypted  
⚠️ **Don't Commit**: Never put passwords in code or git

---

## Multiple Recipients

Want to alert multiple people?

```python
ALERT_EMAIL = email1@gmail.com,email2@gmail.com,email3@gmail.com
```

Or set in Render as comma-separated:
```
ALERT_EMAIL = admin@company.com,dev@company.com
```

---

## Troubleshooting

### "Authentication failed"
- Double-check app password (no spaces)
- Ensure 2FA is enabled
- Generate new app password

### "Not receiving emails"
- Check spam folder
- Verify ALERT_EMAIL is correct
- Check Render logs for email errors

### "SMTP connection failed"
- Verify SMTP_SERVER and SMTP_PORT
- Some networks block port 587 - try port 465 with SSL

---

## Pro Tip: Uptime Monitoring

For 24/7 monitoring, use a free service like:

**UptimeRobot** (https://uptimerobot.com)
- Monitor: `https://your-app.onrender.com/health`
- Alert when worker is down
- 5-minute intervals
- Free for 50 monitors

**Better Stack** (https://betterstack.com)
- More advanced monitoring
- Slack/Discord integration
- Free tier available
