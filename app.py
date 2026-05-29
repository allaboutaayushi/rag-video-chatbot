import streamlit as st
import os
import re
from openai import OpenAI

st.set_page_config(page_title="Video Engagement Analyzer", layout="wide")
st.title("📊 Video Engagement Analyzer")

# Sidebar
with st.sidebar:
    st.header("⚙️ Setup")
    api_choice = st.radio("Choose API:", ["Groq (FREE)", "OpenAI (Paid)"])

    if api_choice == "Groq (FREE)":
        st.write("**Get Groq API Key (FREE):**")
        st.write("1. https://console.groq.com/keys")
        st.write("2. Sign up (free)")
        st.write("3. Copy key → Paste below")

        api_key = st.text_input("Groq API Key", type="password", key="groq_input")
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
            st.success("✅ Groq API Key set")
    else:
        st.write("**Get OpenAI API Key (Paid):**")
        st.write("1. https://platform.openai.com/api-keys")
        st.write("2. Add payment → Create key")
        st.write("3. Paste below")

        api_key = st.text_input("OpenAI API Key", type="password", key="openai_input")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ OpenAI API Key set")

    st.divider()
    st.caption("🟢 **Groq:** FREE")
    st.caption("🔵 **OpenAI:** Paid")

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

def get_youtube_data(url, video_id):
    try:
        import yt_dlp
    except ImportError:
        st.error("yt-dlp not installed")
        return None, None

    metadata = None
    transcript = None

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            views = info.get('view_count', 0) or 0
            likes = info.get('like_count', 0) or 0
            comments = info.get('comment_count', 0) or 0
            engagement = ((likes + comments) / views * 100) if views > 0 else 0

            metadata = {
                'title': info.get('title', 'Unknown'),
                'creator': info.get('uploader', 'Unknown'),
                'views': views,
                'likes': likes,
                'comments': comments,
                'engagement_rate': engagement,
                'duration': info.get('duration', 0),
            }

            if 'subtitles' in info and info['subtitles']:
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in info['subtitles']:
                        subs = info['subtitles'][lang]
                        transcript = " ".join([s.get('text', '') for s in subs])
                        break

            if not transcript and 'automatic_captions' in info and info['automatic_captions']:
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in info['automatic_captions']:
                        subs = info['automatic_captions'][lang]
                        transcript = " ".join([s.get('text', '') for s in subs])
                        break

    except Exception as e:
        st.warning(f"Could not get YouTube data: {str(e)}")
        return None, None

    if not transcript:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            ts = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([t['text'] for t in ts])
        except:
            pass

    return metadata, transcript

def analyze_comparison(meta_a, meta_b, trans_a, trans_b):
    try:
        groq_key = os.environ.get("GROQ_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        if not groq_key and not openai_key:
            st.error("❌ No API key set")
            return None

        engagement_a = meta_a.get('engagement_rate', 0)
        engagement_b = meta_b.get('engagement_rate', 0)

        if engagement_a > engagement_b:
            higher = 'A'
            diff = engagement_a - engagement_b
        else:
            higher = 'B'
            diff = engagement_b - engagement_a

        prompt = f"""Compare these YouTube videos and explain in 3-4 sentences why Video {higher} has {diff:.2f}% higher engagement.

VIDEO A: {meta_a['title']} ({engagement_a:.2f}% engagement, {meta_a['views']:,} views)
Transcript: {trans_a[:300]}...

VIDEO B: {meta_b['title']} ({engagement_b:.2f}% engagement, {meta_b['views']:,} views)
Transcript: {trans_b[:300]}...

Focus on: hooks, pacing, call-to-action."""

        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)

                models_to_try = [
                    "mixtral-8x7b-32768",
                    "llama2-70b-4096",
                    "gemma-7b-it",
                    "llama-3.1-8b-instant"
                ]

                for model in models_to_try:
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7,
                            max_tokens=300
                        )
                        return response.choices[0].message.content
                    except Exception as e:
                        error_str = str(e).lower()
                        if "terms" in error_str or "decommissioned" in error_str:
                            continue
                        if model == models_to_try[-1]:
                            raise

            except Exception as groq_err:
                st.error(f"❌ Groq error: {str(groq_err)}")
                return None

        else:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

# Main UI
col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A")
    url_a = st.text_input("YouTube URL", key="a", placeholder="https://youtube.com/watch?v=...")

with col2:
    st.subheader("📹 Video B")
    url_b = st.text_input("YouTube URL", key="b", placeholder="https://youtube.com/watch?v=...")

if st.button("🚀 Analyze Videos", use_container_width=True, type="primary"):
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        st.error("❌ Enter API key in sidebar")
    elif not url_a or not url_b:
        st.error("❌ Enter both URLs")
    else:
        st.session_state.analysis = None

        with st.spinner("📥 Extracting videos..."):
            vid_a = extract_youtube_id(url_a)
            vid_b = extract_youtube_id(url_b)

            if not vid_a or not vid_b:
                st.error("❌ Invalid YouTube URLs")
            else:
                meta_a, trans_a = get_youtube_data(url_a, vid_a)
                meta_b, trans_b = get_youtube_data(url_b, vid_b)

                if not (meta_a and trans_a and meta_b and trans_b):
                    st.error("❌ Could not extract both videos:")
                    st.info("✓ Valid YouTube URLs")
                    st.info("✓ Videos have captions")
                    st.info("✓ Videos are public")
                else:
                    st.session_state.videos = {
                        'A': {'meta': meta_a, 'trans': trans_a},
                        'B': {'meta': meta_b, 'trans': trans_b}
                    }

                    with st.spinner("🤖 Analyzing..."):
                        analysis = analyze_comparison(meta_a, meta_b, trans_a, trans_b)
                        if analysis:
                            st.session_state.analysis = analysis

# Display results
if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        meta_a = st.session_state.videos['A']['meta']
        st.subheader("📊 Video A")
        st.metric("Engagement", f"{meta_a['engagement_rate']:.2f}%")
        st.write(f"**{meta_a['title']}**")
        st.write(f"Creator: {meta_a['creator']}")
        st.write(f"Views: {meta_a['views']:,} | Likes: {meta_a['likes']:,} | Comments: {meta_a['comments']:,}")

    with col2:
        meta_b = st.session_state.videos['B']['meta']
        st.subheader("📊 Video B")
        st.metric("Engagement", f"{meta_b['engagement_rate']:.2f}%")
        st.write(f"**{meta_b['title']}**")
        st.write(f"Creator: {meta_b['creator']}")
        st.write(f"Views: {meta_b['views']:,} | Likes: {meta_b['likes']:,} | Comments: {meta_b['comments']:,}")

    st.divider()

    if st.session_state.analysis:
        st.subheader("🎯 Why One Performs Better")
        st.info(st.session_state.analysis)
