import streamlit as st
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import re
from datetime import datetime

st.set_page_config(page_title="RAG Video Chatbot", layout="wide", initial_sidebar_state="expanded")

# Styling
st.markdown("""
<style>
    .main { max-width: 1200px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 8px; }
    .video-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.title("🎬 RAG Video Analyzer")
st.markdown("Compare YouTube & Instagram videos using AI-powered analysis")

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Get from https://platform.openai.com/api-keys")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ Please enter your OpenAI API key to continue")

# Initialize session state
if "videos" not in st.session_state:
    st.session_state.videos = {}
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_id):
    """Get transcript from YouTube"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        return f"Error getting transcript: {str(e)}"

def get_youtube_metadata(url):
    """Get YouTube video metadata"""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        views = info.get('view_count', 0)
        likes = info.get('like_count', 0) or 0
        comments = info.get('comment_count', 0) or 0
        engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0

        return {
            'title': info.get('title', 'Unknown'),
            'creator': info.get('uploader', 'Unknown'),
            'views': views,
            'likes': likes,
            'comments': comments,
            'engagement_rate': engagement_rate,
            'duration': info.get('duration', 0),
            'upload_date': info.get('upload_date', 'Unknown'),
        }
    except Exception as e:
        return {'error': str(e)}

def get_instagram_metadata():
    """Return placeholder for Instagram (API limited)"""
    return {
        'title': 'Instagram Reel',
        'creator': 'Creator',
        'views': 0,
        'likes': 0,
        'comments': 0,
        'engagement_rate': 0,
    }

# Main interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A (Required)")
    video_a_url = st.text_input("Video A URL", placeholder="https://youtube.com/watch?v=...", key="video_a")

with col2:
    st.subheader("📹 Video B (Required)")
    video_b_url = st.text_input("Video B URL", placeholder="https://youtube.com/watch?v=...", key="video_b")

if st.button("🚀 Analyze Videos", use_container_width=True, type="primary"):
    if not api_key:
        st.error("❌ Please enter OpenAI API key in the sidebar")
    elif not video_a_url or not video_b_url:
        st.error("❌ Please enter both video URLs")
    else:
        with st.spinner("📊 Processing videos..."):
            try:
                # Process Video A
                st.status("Extracting Video A...", state="running")
                video_a_id = extract_youtube_id(video_a_url)
                if video_a_id:
                    transcript_a = get_youtube_transcript(video_a_id)
                    metadata_a = get_youtube_metadata(video_a_url)
                    st.session_state.videos['A'] = {
                        'url': video_a_url,
                        'transcript': transcript_a,
                        'metadata': metadata_a,
                        'id': video_a_id
                    }
                    st.success("✅ Video A extracted")
                else:
                    st.warning("⚠️ Could not extract Video A ID")

                # Process Video B
                st.status("Extracting Video B...", state="running")
                video_b_id = extract_youtube_id(video_b_url)
                if video_b_id:
                    transcript_b = get_youtube_transcript(video_b_id)
                    metadata_b = get_youtube_metadata(video_b_url)
                    st.session_state.videos['B'] = {
                        'url': video_b_url,
                        'transcript': transcript_b,
                        'metadata': metadata_b,
                        'id': video_b_id
                    }
                    st.success("✅ Video B extracted")
                else:
                    st.warning("⚠️ Could not extract Video B ID")

                # Create embeddings and vector store
                if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
                    st.status("Creating embeddings...", state="running")

                    # Combine transcripts
                    documents = [
                        {"content": st.session_state.videos['A']['transcript'], "video": "A", "title": st.session_state.videos['A']['metadata'].get('title', 'Video A')},
                        {"content": st.session_state.videos['B']['transcript'], "video": "B", "title": st.session_state.videos['B']['metadata'].get('title', 'Video B')}
                    ]

                    # Split text
                    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                    texts = []
                    metadatas = []
                    for doc in documents:
                        chunks = splitter.split_text(doc['content'])
                        for chunk in chunks:
                            texts.append(chunk)
                            metadatas.append({'video': doc['video'], 'title': doc['title']})

                    # Create vector store
                    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                    st.session_state.vector_store = Chroma.from_texts(
                        texts,
                        embeddings,
                        metadatas=metadatas,
                        collection_name="videos"
                    )

                    # Create RAG chain
                    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
                    prompt_template = """You are an expert video analyst. Use the provided video transcripts to answer questions about the videos.

Video Metadata:
Video A: {metadata_a}
Video B: {metadata_b}

Context from videos: {context}

Question: {question}

Provide a detailed answer with specific references to which video (A or B) you're discussing. Include timestamps or specific content when relevant."""

                    prompt = PromptTemplate(
                        template=prompt_template,
                        input_variables=["metadata_a", "metadata_b", "context", "question"]
                    )

                    st.session_state.qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=st.session_state.vector_store.as_retriever(search_kwargs={"k": 5}),
                        prompt=prompt
                    )

                    st.success("✅ Videos processed and ready for analysis!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Display video metrics if available
if st.session_state.videos:
    st.divider()
    st.subheader("📊 Video Metrics")

    col1, col2 = st.columns(2)

    if 'A' in st.session_state.videos:
        with col1:
            meta = st.session_state.videos['A']['metadata']
            if 'error' not in meta:
                st.markdown(f"""
                <div class='video-card'>
                <h3>Video A</h3>
                <p><b>Creator:</b> {meta.get('creator', 'N/A')}</p>
                <p><b>Views:</b> {meta.get('views', 0):,}</p>
                <p><b>Likes:</b> {meta.get('likes', 0):,}</p>
                <p><b>Comments:</b> {meta.get('comments', 0):,}</p>
                <p><b>Engagement Rate:</b> {meta.get('engagement_rate', 0):.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

    if 'B' in st.session_state.videos:
        with col2:
            meta = st.session_state.videos['B']['metadata']
            if 'error' not in meta:
                st.markdown(f"""
                <div class='video-card'>
                <h3>Video B</h3>
                <p><b>Creator:</b> {meta.get('creator', 'N/A')}</p>
                <p><b>Views:</b> {meta.get('views', 0):,}</p>
                <p><b>Likes:</b> {meta.get('likes', 0):,}</p>
                <p><b>Comments:</b> {meta.get('comments', 0):,}</p>
                <p><b>Engagement Rate:</b> {meta.get('engagement_rate', 0):.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

# Chat interface
if st.session_state.qa_chain:
    st.divider()
    st.subheader("💬 Ask Questions About Your Videos")

    # Example questions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Why did Video A get more engagement?"):
            st.session_state.query = "Why did Video A get more engagement than Video B? Analyze the differences in content, pacing, and engagement strategies."
    with col2:
        if st.button("Compare the hooks in first 5 seconds"):
            st.session_state.query = "Compare the hooks and opening strategies used in the first 5 seconds of both videos. What makes them effective?"

    # Custom question input
    query = st.text_area("Or ask your own question:", key="custom_query", placeholder="e.g., What content strategies work best in these videos?")

    if st.button("Get AI Analysis", use_container_width=True, type="primary"):
        if query:
            with st.spinner("🤖 Analyzing..."):
                try:
                    metadata_a = st.session_state.videos['A']['metadata']
                    metadata_b = st.session_state.videos['B']['metadata']

                    response = st.session_state.qa_chain.run(
                        query=query,
                        metadata_a=str(metadata_a),
                        metadata_b=str(metadata_b)
                    )

                    st.markdown("### 📝 Analysis")
                    st.write(response)

                    # Save to chat history
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    st.session_state.messages.append({"role": "user", "content": query})
                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
### 🚀 How It Works
1. **Input Videos**: Paste YouTube URLs (Instagram limited support)
2. **Extract**: Transcripts and metadata are extracted automatically
3. **Embed**: Content is vectorized using OpenAI embeddings
4. **Analyze**: Ask questions and get AI-powered insights with source citations

### 💡 Tips
- YouTube videos with transcripts work best
- Ask specific questions for better analysis
- The AI references content from both videos

**Built with:** Streamlit + LangChain + OpenAI + ChromaDB
""")
