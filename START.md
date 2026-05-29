# 🎬 RAG Video Chatbot - No Terminal Required

Your AI-powered video analysis chatbot is ready to deploy. **Zero terminal involvement needed.**

## 🚀 Deploy in 5 Minutes

### Step 1: Get OpenAI API Key (2 min)
1. Visit: https://platform.openai.com/api-keys
2. Sign up (free account)
3. Create new API key
4. Copy it (you'll need this soon)

### Step 2: Upload to GitHub (2 min)
1. Visit: https://github.com
2. Create new repository named `rag-video-chatbot`
3. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `.gitignore`
   - `README.md`
   - `DEPLOY.md`

### Step 3: Deploy (1 min)
**Choose Option A or B below:**

#### Option A: Streamlit Cloud (Recommended) ⭐
1. Visit: https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository
4. Set main file to: `app.py`
5. Click "Deploy"
6. Wait 2 minutes (deploying...)
7. App opens automatically!

#### Option B: Render
1. Visit: https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub
4. Select your repository
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `streamlit run app.py --server.port=$PORT`
7. Add environment variable:
   - Key: `OPENAI_API_KEY`
   - Value: (paste your API key)
8. Deploy

### Step 4: Add Your API Key
1. In your deployed app (top right menu)
2. Click "Manage secrets"
3. Add: `OPENAI_API_KEY = sk-...`
4. Refresh

## ✅ You're Done!

Your chatbot is now LIVE and ready to use. 🎉

## 💡 How to Use

1. **Paste YouTube URLs** for two videos
2. **Click "Analyze Videos"**
3. **Wait 20 seconds** for processing
4. **See metrics**: Engagement rates, views, likes
5. **Ask questions**:
   - "Why did Video A get more engagement?"
   - "Compare the hooks"
   - "Suggest improvements"
6. **Get AI insights** with source citations!

## 📊 What You Get

✅ YouTube + Instagram video analysis
✅ Automatic engagement rate calculation
✅ RAG chat with GPT-4 Turbo
✅ Real-time streaming responses
✅ Source citations for every answer
✅ Conversation memory
✅ Beautiful web interface
✅ Zero server management
✅ FREE hosting (Streamlit Cloud)

## 💰 Costs

- **Hosting**: FREE (Streamlit Cloud)
- **API Usage**: ~$0.01 per video pair
- **100 analyses/month**: ~$1-2

## 🎯 Features

- 📹 Multi-platform video analysis
- 📊 Engagement metrics calculation
- 🤖 GPT-4 Turbo powered
- 💬 RAG chat interface
- 📌 Source citations
- 💾 Conversation memory
- 🎨 Beautiful UI
- ⚡ Fast processing

## 🆘 Need Help?

See `DEPLOY.md` for detailed step-by-step instructions for each platform.

---

## Quick Summary

| Step | Time | Action |
|------|------|--------|
| 1 | 2 min | Get OpenAI API key |
| 2 | 2 min | Upload to GitHub |
| 3 | 1 min | Deploy to Streamlit Cloud |
| 4 | 1 min | Add API key |
| **Total** | **6 min** | **Live!** 🎉 |

---

**All done!** Your RAG Video Chatbot is now live and ready to analyze videos. 🚀

Visit your app URL and start comparing videos with AI!
