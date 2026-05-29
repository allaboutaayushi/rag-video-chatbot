# 🚀 Deploy RAG Video Chatbot (No Terminal Required)

Choose your deployment method below:

## Option 1: Streamlit Cloud (Easiest - FREE) ⭐

### Step 1: Upload to GitHub
1. Create account at [github.com](https://github.com) (if you don't have one)
2. Create new repository: `rag-video-chatbot`
3. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `rag-video-chatbot`
5. Main file path: `app.py`
6. Click "Deploy"

**That's it!** Your app is live in ~2 minutes.

### Step 3: Add Your OpenAI API Key
1. Click "Manage secrets" in the app (⋮ menu)
2. Add: `OPENAI_API_KEY = sk-...`
3. Save and refresh

**Your app is now live and ready to use!** 🎉

---

## Option 2: Render (Alternative - FREE Tier)

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com)
2. Sign up (free account)
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select `rag-video-chatbot` repository
6. Settings:
   - **Name**: `rag-video-chatbot`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT`
7. Add environment variable:
   - **OPENAI_API_KEY**: `sk-...` (your API key)
8. Click "Create Web Service"

**Deployed in ~3 minutes!** 🚀

---

## Option 3: Run Locally (macOS/Linux/Windows)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run App
```bash
streamlit run app.py
```

Opens at: http://localhost:8501

---

## What You Get

✅ Beautiful web interface (no code required)
✅ YouTube + Instagram video analysis
✅ RAG chat with GPT-4 Turbo
✅ Engagement rate calculations
✅ Source citations
✅ Conversation memory
✅ Fully hosted (no server management)

---

## Usage

1. **Enter API Key**: Add your OpenAI API key (get free $5 at openai.com)
2. **Paste URLs**: Add YouTube video URLs
3. **Click Analyze**: Wait 20 seconds
4. **Ask Questions**:
   - "Why did Video A get more engagement?"
   - "Compare the hooks in first 5 seconds"
   - "Suggest improvements for Video B"
5. **Get AI Insights** with source citations!

---

## Costs

**Streamlit Cloud**: FREE forever
**Render**: FREE tier (paid options available)
**OpenAI API**: ~$0.01 per video pair analysis

---

## Troubleshooting

### "OpenAI API key error"
- Ensure key is added correctly
- Check you have OpenAI credits at platform.openai.com

### "Video not processing"
- YouTube videos must have transcripts enabled
- Instagram Reels have limited support
- Check that URL is public

### "Slow response"
- First API call is slower (5-10 sec)
- Subsequent calls are faster (1-2 sec)
- Normal behavior!

---

## Next Steps

1. **Get OpenAI API Key**: https://platform.openai.com/api-keys
2. **Choose deployment** (Streamlit Cloud recommended)
3. **Deploy** (takes 2-5 minutes)
4. **Add API key** to your deployed app
5. **Start analyzing** videos! 🎬

---

**Questions?** See `README.md` for full documentation.
