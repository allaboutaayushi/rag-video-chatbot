import streamlit as st
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re

st.set_page_config(page_title="RAG Video Chatbot", layout="wide")
st.title("🎬 RAG Video Analyzer")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key set")

if "videos" not in st.session_state:
    st.session_state.videos = {}

def extract_id(url):
    patterns = [r'watch\?v=([a-zA-Z0-9_-]+)', r'youtu\.be/([a-zA-Z0-9_-]+)']
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def get_transcript(vid_id):
    try:
        ts = YouTubeTranscriptApi.get_transcript(vid_id)
        return " ".join([t['text'] for t in ts])
    except:
        return "No transcript"

def get_metadata(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        v = info.get('view_count', 0)
        l = info.get('like_count', 0) or 0
        c = info.get('comment_count', 0) or 0
        eng = ((l + c) / v * 100) if v > 0 else 0
        return {
            'title': info.get('title', 'Unknown'),
            'creator': info.get('uploader', 'Unknown'),
            'views': v,
            'likes': l,
            'comments': c,
            'engagement_rate': eng,
        }
    except:
        return {'error': 'Failed'}

col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A")
    url_a = st.text_input("YouTube URL", key="a")

with col2:
    st.subheader("📹 Video B")
    url_b = st.text_input("YouTube URL", key="b")

if st.button("🚀 Analyze", use_container_width=True, type="primary"):
    if not url_a or not url_b:
        st.error("Enter both URLs")
    else:
        with st.spinner("Processing..."):
            vid_a = extract_id(url_a)
            if vid_a:
                st.info("Extracting Video A...")
                trans_a = get_transcript(vid_a)
                meta_a = get_metadata(url_a)
                st.session_state.videos['A'] = {'transcript': trans_a, 'metadata': meta_a}
                st.success("✅ Video A extracted")

            vid_b = extract_id(url_b)
            if vid_b:
                st.info("Extracting Video B...")
                trans_b = get_transcript(vid_b)
                meta_b = get_metadata(url_b)
                st.session_state.videos['B'] = {'transcript': trans_b, 'metadata': meta_b}
                st.success("✅ Video B extracted")

            if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
                st.success("✅ Videos processed!")

if st.session_state.videos:
    st.divider()
    st.subheader("📊 Metrics")
    
    col1, col2 = st.columns(2)
    
    if 'A' in st.session_state.videos:
        with col1:
            meta = st.session_state.videos['A']['metadata']
            if 'error' not in meta:
                st.metric("Video A Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"Views: {meta.get('views', 0):,}")
                st.write(f"Likes: {meta.get('likes', 0):,}")

    if 'B' in st.session_state.videos:
        with col2:
            meta = st.session_state.videos['B']['metadata']
            if 'error' not in meta:
                st.metric("Video B Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"Views: {meta.get('views', 0):,}")
                st.write(f"Likes: {meta.get('likes', 0):,}")

st.divider()
st.markdown("RAG Video Analyzer")
