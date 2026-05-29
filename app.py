import streamlit as st
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import openai
from openai import OpenAI

st.set_page_config(page_title="Video Engagement Analyzer", layout="wide")
st.title("📊 Video Engagement Analyzer")

# Sidebar - API Key
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key set")

# Initialize session state
if "videos" not in st.session_state:
    st.session_state.videos = {}
if "analysis" not in st.session_state:
    st.session_state.analysis = None

def extract_youtube_id(url):
    if not url:
        return None
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    try:
        ts = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in ts])
    except:
        return None

def get_metadata(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        views = info.get('view_count', 0) or 0
        likes = info.get('like_count', 0) or 0
        comments = info.get('comment_count', 0) or 0
        engagement = ((likes + comments) / views * 100) if views > 0 else 0

        return {
            'title': info.get('title', 'Unknown'),
            'creator': info.get('uploader', 'Unknown'),
            'views': views,
            'likes': likes,
            'comments': comments,
            'engagement_rate': engagement,
            'duration': info.get('duration', 0),
        }
    except:
        return None

def analyze_videos(meta_a, meta_b, trans_a, trans_b):
    """Simple direct analysis with OpenAI"""
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        engagement_a = meta_a.get('engagement_rate', 0)
        engagement_b = meta_b.get('engagement_rate', 0)

        if engagement_a > engagement_b:
            higher = 'A'
            diff = engagement_a - engagement_b
        else:
            higher = 'B'
            diff = engagement_b - engagement_a

        prompt = f"""Compare these two YouTube videos and explain in 2-3 sentences WHY Video {higher} has {diff:.2f}% higher engagement.

VIDEO A:
- Title: {meta_a['title']}
- Views: {meta_a['views']:,}
- Likes: {meta_a['likes']:,} | Comments: {meta_a['comments']:,}
- Engagement: {engagement_a:.2f}%
- First 300 chars: {trans_a[:300]}...

VIDEO B:
- Title: {meta_b['title']}
- Views: {meta_b['views']:,}
- Likes: {meta_b['likes']:,} | Comments: {meta_b['comments']:,}
- Engagement: {engagement_b:.2f}%
- First 300 chars: {trans_b[:300]}...

Be concise. Focus on: hooks, content style, pacing differences."""

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

# Two columns for video input
col1, col2 = st.columns(2)

with col1:
    st.subheader("Video A")
    url_a = st.text_input("YouTube URL", key="a", placeholder="https://youtube.com/watch?v=...")

with col2:
    st.subheader("Video B")
    url_b = st.text_input("YouTube URL", key="b", placeholder="https://youtube.com/watch?v=...")

# Analyze button
if st.button("🚀 Analyze", use_container_width=True, type="primary"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("❌ Enter OpenAI API key in sidebar")
    elif not url_a or not url_b:
        st.error("❌ Enter both URLs")
    else:
        st.session_state.analysis = None

        with st.spinner("📥 Extracting videos..."):
            # Video A
            vid_a = extract_youtube_id(url_a)
            trans_a = get_transcript(vid_a) if vid_a else None
            meta_a = get_metadata(url_a)

            # Video B
            vid_b = extract_youtube_id(url_b)
            trans_b = get_transcript(vid_b) if vid_b else None
            meta_b = get_metadata(url_b)

            if not (trans_a and meta_a and trans_b and meta_b):
                st.error("❌ Extraction failed")
                if not vid_a or not meta_a:
                    st.error(f"Video A: ID extraction: {'✓' if vid_a else '✗'}, Metadata: {'✓' if meta_a else '✗'}")
                if not vid_b or not meta_b:
                    st.error(f"Video B: ID extraction: {'✓' if vid_b else '✗'}, Metadata: {'✓' if meta_b else '✗'}")
                if trans_a is None:
                    st.error("Video A: No captions/transcript found")
                if trans_b is None:
                    st.error("Video B: No captions/transcript found")
                st.info("💡 Try videos from: TED-Ed, Vsauce, MrBeast, Kurzgesagt (all have captions)")
            else:
                st.session_state.videos = {
                    'A': {'meta': meta_a, 'trans': trans_a},
                    'B': {'meta': meta_b, 'trans': trans_b}
                }

        # Analyze if extraction succeeded
        if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
            with st.spinner("🤖 Analyzing..."):
                analysis = analyze_videos(
                    st.session_state.videos['A']['meta'],
                    st.session_state.videos['B']['meta'],
                    st.session_state.videos['A']['trans'],
                    st.session_state.videos['B']['trans']
                )
                st.session_state.analysis = analysis

# Display results
if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        meta_a = st.session_state.videos['A']['meta']
        st.subheader("📊 Video A")
        st.metric("Title", meta_a['title'][:40] + "..." if len(meta_a['title']) > 40 else meta_a['title'])
        st.metric("Creator", meta_a['creator'])
        st.metric("Views", f"{meta_a['views']:,}")
        st.metric("Likes", f"{meta_a['likes']:,}")
        st.metric("Comments", f"{meta_a['comments']:,}")
        st.metric("Engagement Rate", f"{meta_a['engagement_rate']:.2f}%")

    with col2:
        meta_b = st.session_state.videos['B']['meta']
        st.subheader("📊 Video B")
        st.metric("Title", meta_b['title'][:40] + "..." if len(meta_b['title']) > 40 else meta_b['title'])
        st.metric("Creator", meta_b['creator'])
        st.metric("Views", f"{meta_b['views']:,}")
        st.metric("Likes", f"{meta_b['likes']:,}")
        st.metric("Comments", f"{meta_b['comments']:,}")
        st.metric("Engagement Rate", f"{meta_b['engagement_rate']:.2f}%")

    st.divider()

    st.subheader("🎯 Why One Performs Better")
    if st.session_state.analysis:
        st.info(st.session_state.analysis)
