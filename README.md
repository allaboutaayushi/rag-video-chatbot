# 🎬 RAG Video Chatbot

Compare YouTube & Instagram videos using AI-powered analysis. Ask questions and get insights powered by GPT-4 Turbo with source citations.

## ✨ Features

✅ **Multi-platform Analysis**: YouTube + Instagram Reels support
✅ **Engagement Metrics**: Auto-calculate (likes + comments) / views × 100
✅ **RAG Chat**: Ask questions, get AI responses with sources
✅ **Streaming Responses**: Real-time answer generation
✅ **Conversation Memory**: Context across multiple turns
✅ **Zero Terminal**: Web-based interface, no coding required
✅ **Free Hosting**: Deploy to Streamlit Cloud for free

## 🚀 Quick Start

### Option 1: Deploy to Streamlit Cloud (Easiest)

1. Fork/upload to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app", select your repo
4. Add your OpenAI API key
5. **Done!** 🎉

See `DEPLOY.md` for step-by-step instructions.

### Option 2: Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Visit: http://localhost:8501

### Option 3: Deploy to Render

See `DEPLOY.md` for full instructions.

## 🎯 How to Use

1. **Paste Video URLs**: YouTube links for both videos
2. **Click "Analyze Videos"**: Wait 20 seconds for processing
3. **View Metrics**: Engagement rates, views, likes, comments
4. **Ask Questions**:
   - "Why did Video A get more engagement?"
   - "Compare the hooks in the first 5 seconds"
   - "What's the engagement rate of each?"
   - "Suggest improvements for Video B"
5. **Get AI Insights** with source citations!

## 📊 What It Analyzes

- **Engagement Rate**: Formula: (likes + comments) / views × 100
- **Metadata**: Views, likes, comments, creator, upload date
- **Transcripts**: Full video transcripts extracted automatically
- **Content**: AI analyzes hooks, structure, pacing, strategy

## 🛠️ Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **LLM**: OpenAI GPT-4 Turbo
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: ChromaDB (in-memory)
- **Transcript**: youtube-transcript-api
- **Metadata**: yt-dlp

## 💰 Costs

| Service | Cost |
|---------|------|
| Streamlit Cloud | FREE |
| Render (free tier) | FREE |
| OpenAI API | ~$0.01 per analysis |
| YouTube Transcripts | FREE |

**Total for 100 analyses: ~$1.10**

## 📁 Files

- `app.py` - Main Streamlit application (all code in one file)
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `DEPLOY.md` - Deployment instructions
- `README.md` - This file

## 🔑 API Keys

Get free OpenAI API key with $5 credit:
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up (free account)
3. Create API key
4. Add to your deployed app

## 🎓 Example Questions

- "Why did Video A get more engagement than Video B?"
- "Compare the content hooks in the first 5 seconds"
- "What's the engagement rate of each video?"
- "Who are the creators and what are their follower counts?"
- "Suggest 3 improvements for Video B based on Video A's success"
- "Analyze the pacing and structure differences"
- "What hashtags worked best?"

## ⚡ Performance

- **Video Processing**: 15-20 seconds (extraction + embedding)
- **Chat Responses**: 1-3 seconds
- **First API Call**: 5-10 seconds (initialization)

## 🚀 Deployment Options

### 1. Streamlit Cloud (Recommended) ⭐
- **Easiest**: 2-minute setup
- **Cost**: FREE forever
- **URL**: share.streamlit.io/yourname/rag-video-chatbot

### 2. Render
- **Easy**: 5-minute setup
- **Cost**: FREE tier or $7+/month
- **Customizable**: More control

### 3. Local Development
- **Run anywhere**: Just need Python
- **Cost**: FREE
- **Usage**: Testing before deployment

See `DEPLOY.md` for detailed instructions.

## 🐛 Troubleshooting

### "API key not recognized"
- Make sure key is correctly pasted
- Check you have OpenAI credits
- Verify no extra spaces

### "Video not processing"
- YouTube must have captions/transcripts enabled
- Instagram Reels have limited API support
- Try a different video

### "Slow responses"
- First API call is slower (normal)
- Subsequent calls are faster
- OpenAI's API has rate limits

### "Module not found"
```bash
pip install -r requirements.txt
```

## 📚 Learn More

- [Streamlit Docs](https://docs.streamlit.io)
- [LangChain Docs](https://docs.langchain.com)
- [OpenAI API Docs](https://platform.openai.com/docs)

## 📄 License

Free to use and modify

## 🎉 Ready to Deploy?

1. **Get API Key**: https://platform.openai.com/api-keys
2. **Read DEPLOY.md**: Choose your hosting platform
3. **Deploy**: Takes 2-5 minutes
4. **Start Analyzing**: Compare videos instantly!

---

**Questions?** See `DEPLOY.md` for deployment help.

Built with ❤️ | Zero Terminal | Production Ready
