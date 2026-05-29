import streamlit as st
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re

st.set_page_config(page_title="RAG Video Chatbot", layout="wide")
st.title("🎬 RAG Video Analyzer")
st.markdown("Compare YouTube videos with AI")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key set")

if "videos" not in st.session_state:
    st.session_state.videos = {}

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
    except:
        return "No transcript available"

def get_metadata(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
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
    except:
        return {'error': 'Failed to get metadata'}

col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A")
    url_a = st.text_input("YouTube URL", key="a")

with col2:
    st.subheader("📹 Video B")
    url_b = st.text_input("YouTube URL", key="b")

if st.button("🚀 Analyze", use_container_width=True, type="primary"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("❌ Add API key in sidebar")
    else:
        with st.spinner("Processing..."):
            try:
                vid_a = extract_youtube_id(url_a)
                if vid_a:
                    trans_a = get_transcript(vid_a)
                    meta_a = get_metadata(url_a)
                    st.session_state.videos['A'] = {'transcript': trans_a, 'metadata': meta_a}

                vid_b = extract_youtube_id(url_b)
                if vid_b:
                    trans_b = get_transcript(vid_b)
                    meta_b = get_metadata(url_b)
                    st.session_state.videos['B'] = {'transcript': trans_b, 'metadata': meta_b}

                if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
                    from langchain_text_splitters import RecursiveCharacterTextSplitter
                    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
                    from langchain_community.vectorstores import Chroma
                    from langchain.chains import RetrievalQA
                    from langchain.prompts import PromptTemplate

                    texts = [trans_a, trans_b]
                    metadatas = [
                        {'video': 'A', 'title': meta_a.get('title', 'Video A')},
                        {'video': 'B', 'title': meta_b.get('title', 'Video B')}
                    ]

                    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                    all_texts = []
                    all_meta = []

                    for text, meta in zip(texts, metadatas):
                        chunks = splitter.split_text(text)
                        for chunk in chunks:
                            all_texts.append(chunk)
                            all_meta.append(meta)

                    embeddings = OpenAIEmbeddings()
                    vector_store = Chroma.from_texts(all_texts, embeddings, metadatas=all_meta, collection_name="videos")

                    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
                    prompt = PromptTemplate(
                        template="Answer about videos:\nVideo A: {meta_a}\nVideo B: {meta_b}\nContent: {context}\nQ: {question}",
                        input_variables=["meta_a", "meta_b", "context", "question"]
                    )

                    st.session_state.qa_chain = RetrievalQA.from_chain_type(
                        llm=llm, chain_type="stuff",
                        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
                        prompt=prompt
                    )
                    st.success("✅ Ready!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if st.session_state.videos:
    st.divider()
    col1, col2 = st.columns(2)

    if 'A' in st.session_state.videos:
        with col1:
            meta = st.session_state.videos['A']['metadata']
            if 'error' not in meta:
                st.metric("Video A Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"Views: {meta.get('views', 0):,}")

    if 'B' in st.session_state.videos:
        with col2:
            meta = st.session_state.videos['B']['metadata']
            if 'error' not in meta:
                st.metric("Video B Engagement", f"{meta.get('engagement_rate', 0):.2f}%")
                st.write(f"Views: {meta.get('views', 0):,}")

if hasattr(st.session_state, 'qa_chain') and st.session_state.qa_chain:
    st.divider()
    query = st.text_area("Ask about videos:", placeholder="Why did Video A perform better?")
    if st.button("Analyze", use_container_width=True):
        if query:
            with st.spinner("Thinking..."):
                try:
                    meta_a = str(st.session_state.videos['A']['metadata'])
                    meta_b = str(st.session_state.videos['B']['metadata'])
                    response = st.session_state.qa_chain.run(query=query, meta_a=meta_a, meta_b=meta_b)
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
