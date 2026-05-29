import streamlit as st
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import Chroma
    from langchain_community.chains.retrieval_qa.base import RetrievalQA
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

st.set_page_config(page_title="RAG Video Chatbot", layout="wide")
st.title("🎬 RAG Video Analyzer")
st.markdown("Compare YouTube videos with AI")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key set")
    else:
        st.warning("⚠️ Enter OpenAI API key above")

if "videos" not in st.session_state:
    st.session_state.videos = {}
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

def extract_youtube_id(url):
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        return f"Error: {str(e)}"

def get_metadata(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        views = info.get('view_count', 0)
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
        }
    except Exception as e:
        return {'error': str(e)}

col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A")
    url_a = st.text_input("YouTube URL", key="url_a", placeholder="https://youtube.com/watch?v=...")

with col2:
    st.subheader("📹 Video B")
    url_b = st.text_input("YouTube URL", key="url_b", placeholder="https://youtube.com/watch?v=...")

if st.button("🚀 Analyze Videos", use_container_width=True, type="primary"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("❌ Please enter OpenAI API key in sidebar")
    elif not url_a or not url_b:
        st.error("❌ Please enter both video URLs")
    else:
        with st.spinner("📊 Processing videos..."):
            try:
                st.info("Extracting Video A...")
                vid_a = extract_youtube_id(url_a)
                if vid_a:
                    trans_a = get_transcript(vid_a)
                    meta_a = get_metadata(url_a)
                    st.session_state.videos['A'] = {
                        'transcript': trans_a,
                        'metadata': meta_a,
                        'id': vid_a
                    }
                    st.success("✅ Video A extracted")

                st.info("Extracting Video B...")
                vid_b = extract_youtube_id(url_b)
                if vid_b:
                    trans_b = get_transcript(vid_b)
                    meta_b = get_metadata(url_b)
                    st.session_state.videos['B'] = {
                        'transcript': trans_b,
                        'metadata': meta_b,
                        'id': vid_b
                    }
                    st.success("✅ Video B extracted")

                if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
                    if not LANGCHAIN_AVAILABLE:
                        st.error("❌ LangChain modules not available")
                    else:
                        st.info("Creating embeddings...")

                        trans_a = st.session_state.videos['A']['transcript']
                        trans_b = st.session_state.videos['B']['transcript']

                        texts = [trans_a, trans_b]
                        metadatas = [
                            {'video': 'A', 'title': st.session_state.videos['A']['metadata'].get('title', 'Video A')},
                            {'video': 'B', 'title': st.session_state.videos['B']['metadata'].get('title', 'Video B')}
                        ]

                        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                        all_texts = []
                        all_meta = []

                        for text, meta in zip(texts, metadatas):
                            chunks = splitter.split_text(text)
                            for chunk in chunks:
                                all_texts.append(chunk)
                                all_meta.append(meta)

                        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                        vector_store = Chroma.from_texts(
                            all_texts,
                            embeddings,
                            metadatas=all_meta,
                            collection_name="videos"
                        )

                        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)

                        prompt = PromptTemplate(
                            template="""You are a video analyst. Answer questions about these videos.

Video A: {meta_a}
Video B: {meta_b}

Content: {context}

Question: {question}

Answer with specific references to which video.""",
                            input_variables=["meta_a", "meta_b", "context", "question"]
                        )

                        st.session_state.qa_chain = RetrievalQA.from_chain_type(
                            llm=llm,
                            chain_type="stuff",
                            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
                            prompt=prompt
                        )

                        st.success("✅ Ready for analysis!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if st.session_state.videos:
    st.divider()
    st.subheader("📊 Metrics")

    col1, col2 = st.columns(2)

    if 'A' in st.session_state.videos:
        with col1:
            meta = st.session_state.videos['A']['metadata']
            if 'error' not in meta:
                st.metric("Video A - Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"**Views:** {meta.get('views', 0):,}")
                st.write(f"**Likes:** {meta.get('likes', 0):,}")
                st.write(f"**Comments:** {meta.get('comments', 0):,}")

    if 'B' in st.session_state.videos:
        with col2:
            meta = st.session_state.videos['B']['metadata']
            if 'error' not in meta:
                st.metric("Video B - Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"**Views:** {meta.get('views', 0):,}")
                st.write(f"**Likes:** {meta.get('likes', 0):,}")
                st.write(f"**Comments:** {meta.get('comments', 0):,}")

if st.session_state.qa_chain:
    st.divider()
    st.subheader("💬 Ask Questions")

    query = st.text_area("Ask about your videos:", placeholder="Why did Video A perform better?")

    if st.button("Get Analysis", use_container_width=True, type="primary"):
        if query:
            with st.spinner("🤖 Analyzing..."):
                try:
                    meta_a = str(st.session_state.videos['A']['metadata'])
                    meta_b = str(st.session_state.videos['B']['metadata'])
                    response = st.session_state.qa_chain.run(query=query, meta_a=meta_a, meta_b=meta_b)
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.divider()
st.markdown("Built with Streamlit + LangChain + OpenAI")
