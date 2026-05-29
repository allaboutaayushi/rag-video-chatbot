import streamlit as st
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import openai

# LangChain imports
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import Chroma
    from langchain.prompts import PromptTemplate
    try:
        from langchain_core.messages import HumanMessage, AIMessage
    except ImportError:
        from langchain.schema import HumanMessage, AIMessage
    LANGCHAIN_OK = True
except ImportError:
    LANGCHAIN_OK = False

# Page config
st.set_page_config(page_title="RAG Video Analyzer", layout="wide")

st.title("🎬 RAG Video Analyzer")
st.markdown("Compare YouTube videos & analyze why one has more engagement")

# Sidebar - API Key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        openai.api_key = api_key
        st.success("✅ API Key set")

# Initialize session state
if "videos" not in st.session_state:
    st.session_state.videos = {}
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "comparison_analysis" not in st.session_state:
    st.session_state.comparison_analysis = None

# ==================== HELPER FUNCTIONS ====================

def extract_youtube_id(url):
    """Extract YouTube video ID"""
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

def get_youtube_transcript(video_id):
    """Get YouTube transcript"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except:
        return None

def get_youtube_metadata(url):
    """Get YouTube metadata"""
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

def analyze_engagement_difference(video_a_data, video_b_data):
    """Analyze WHY one video has more engagement than the other"""
    try:
        meta_a = video_a_data['metadata']
        meta_b = video_b_data['metadata']
        trans_a = video_a_data['transcript']
        trans_b = video_b_data['transcript']

        engagement_a = meta_a.get('engagement_rate', 0)
        engagement_b = meta_b.get('engagement_rate', 0)

        # Determine which has more engagement
        if engagement_a > engagement_b:
            higher_video = 'A'
            higher_engagement = engagement_a
            lower_engagement = engagement_b
            diff = engagement_a - engagement_b
        else:
            higher_video = 'B'
            higher_engagement = engagement_b
            lower_engagement = engagement_a
            diff = engagement_b - engagement_a

        # Create detailed analysis prompt
        analysis_prompt = f"""You are a video content expert. Analyze these two YouTube videos and explain WHY Video {higher_video} has {diff:.2f}% higher engagement rate than Video {'B' if higher_video == 'A' else 'A'}.

VIDEO A METRICS:
- Title: {meta_a.get('title', 'Unknown')}
- Creator: {meta_a.get('creator', 'Unknown')}
- Views: {meta_a.get('views', 0):,}
- Likes: {meta_a.get('likes', 0):,}
- Comments: {meta_a.get('comments', 0):,}
- Engagement Rate: {engagement_a:.2f}%
- Duration: {meta_a.get('duration', 0)} seconds

VIDEO B METRICS:
- Title: {meta_b.get('title', 'Unknown')}
- Creator: {meta_b.get('creator', 'Unknown')}
- Views: {meta_b.get('views', 0):,}
- Likes: {meta_b.get('likes', 0):,}
- Comments: {meta_b.get('comments', 0):,}
- Engagement Rate: {engagement_b:.2f}%
- Duration: {meta_b.get('duration', 0)} seconds

VIDEO A TRANSCRIPT (first 1500 chars):
{trans_a[:1500]}...

VIDEO B TRANSCRIPT (first 1500 chars):
{trans_b[:1500]}...

ANALYSIS REQUIREMENTS:
1. Compare the OPENING HOOKS - Which grabs attention better in first 10 seconds?
2. Compare CONTENT STRUCTURE - How is information organized in each?
3. Compare CALL-TO-ACTION - Are there differences in engagement prompts?
4. Compare PACING AND TONE - Is one more energetic, conversational, or professional?
5. Compare KEY DIFFERENCES - What specific content/strategy makes Video {higher_video} more engaging?
6. List TOP 3 REASONS why Video {higher_video} gets {diff:.2f}% more engagement
7. Suggest SPECIFIC IMPROVEMENTS for Video {'B' if higher_video == 'A' else 'A'} based on what works in Video {higher_video}

Be SPECIFIC with examples from the transcripts. Reference exact phrases or strategies."""

        # Call OpenAI with streaming
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)

        response_text = ""
        placeholder = st.empty()

        try:
            for chunk in llm.stream([HumanMessage(content=analysis_prompt)]):
                if hasattr(chunk, 'content'):
                    response_text += chunk.content
                    placeholder.markdown(response_text + " ▌")
        except Exception as stream_err:
            st.error(f"Streaming error: {str(stream_err)}")
            return None

        placeholder.markdown(response_text)
        return response_text

    except Exception as e:
        st.error(f"Error analyzing: {str(e)}")
        return None

def create_vector_store(videos_data):
    """Create vector store for RAG"""
    try:
        if not LANGCHAIN_OK:
            return None

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

        all_texts = []
        all_metadatas = []

        for video_id, video_data in videos_data.items():
            transcript = video_data.get('transcript', '')
            if not transcript:
                continue

            chunks = splitter.split_text(transcript)

            for idx, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadatas.append({
                    'video_id': video_id,
                    'creator': video_data['metadata'].get('creator', 'Unknown'),
                    'title': video_data['metadata'].get('title', 'Unknown'),
                    'chunk_index': idx
                })

        if not all_texts:
            return None

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma.from_texts(
            texts=all_texts,
            embedding=embeddings,
            metadatas=all_metadatas,
            collection_name="videos"
        )

        return vector_store

    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None

def query_rag(query, vector_store, videos_data):
    """Query with RAG and citations"""
    try:
        if not LANGCHAIN_OK:
            return None, []

        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        relevant_docs = retriever.get_relevant_documents(query)

        context = "VIDEO INFORMATION:\n"
        for video_id, video_data in videos_data.items():
            meta = video_data['metadata']
            context += f"\nVideo {video_id}: {meta.get('title', 'Unknown')}\n"
            context += f"Creator: {meta.get('creator', 'Unknown')}\n"
            context += f"Views: {meta.get('views', 0):,} | Engagement: {meta.get('engagement_rate', 0):.2f}%\n"

        context += "\n\nRELEVANT TRANSCRIPT CONTENT:\n"
        citations = []

        for doc in relevant_docs:
            video_id = doc.metadata.get('video_id', 'Unknown')
            title = doc.metadata.get('title', 'Unknown')
            creator = doc.metadata.get('creator', 'Unknown')

            context += f"\n[Video {video_id}] {doc.page_content}\n"

            citations.append({
                'video': video_id,
                'title': title,
                'creator': creator
            })

        prompt = PromptTemplate(
            template="""You are a video analyst. Answer questions about these videos.

{context}

Question: {question}

Reference specific videos and content from transcripts.""",
            input_variables=["context", "question"]
        )

        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
        formatted_prompt = prompt.format(context=context, question=query)

        response_text = ""
        placeholder = st.empty()

        try:
            for chunk in llm.stream([HumanMessage(content=formatted_prompt)]):
                if hasattr(chunk, 'content'):
                    response_text += chunk.content
                    placeholder.markdown(response_text + " ▌")
        except Exception as stream_err:
            st.error(f"Streaming error: {str(stream_err)}")
            return None, citations

        placeholder.markdown(response_text)
        return response_text, citations

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, []

# ==================== MAIN APP ====================

# Video input
col1, col2 = st.columns(2)

with col1:
    st.subheader("📹 Video A")
    url_a = st.text_input("YouTube URL", key="a", placeholder="https://youtube.com/watch?v=...")

with col2:
    st.subheader("📹 Video B")
    url_b = st.text_input("YouTube URL", key="b", placeholder="https://youtube.com/watch?v=...")

# Analyze button
if st.button("🚀 Analyze & Compare", use_container_width=True, type="primary"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("❌ Enter OpenAI API key in sidebar")
    elif not url_a or not url_b:
        st.error("❌ Enter both URLs")
    else:
        with st.spinner("📊 Extracting videos..."):
            try:
                # Video A
                vid_a = extract_youtube_id(url_a)
                if vid_a:
                    trans_a = get_youtube_transcript(vid_a)
                    meta_a = get_youtube_metadata(url_a)
                    if trans_a and meta_a:
                        st.session_state.videos['A'] = {'transcript': trans_a, 'metadata': meta_a}
                        st.success("✅ Video A extracted")

                # Video B
                vid_b = extract_youtube_id(url_b)
                if vid_b:
                    trans_b = get_youtube_transcript(vid_b)
                    meta_b = get_youtube_metadata(url_b)
                    if trans_b and meta_b:
                        st.session_state.videos['B'] = {'transcript': trans_b, 'metadata': meta_b}
                        st.success("✅ Video B extracted")

                # Both loaded
                if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
                    st.session_state.vector_store = create_vector_store(st.session_state.videos)
                    st.session_state.chat_history = []
                    st.success("✅ Ready! Scroll down for analysis.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Display if both loaded
if 'A' in st.session_state.videos and 'B' in st.session_state.videos:
    st.divider()

    # Metrics
    st.subheader("📊 Video Metrics")
    col1, col2 = st.columns(2)

    with col1:
        meta_a = st.session_state.videos['A']['metadata']
        st.metric("Video A - Engagement", f"{meta_a.get('engagement_rate', 0):.2f}%")
        st.write(f"Views: {meta_a.get('views', 0):,}")
        st.write(f"Likes: {meta_a.get('likes', 0):,} | Comments: {meta_a.get('comments', 0):,}")

    with col2:
        meta_b = st.session_state.videos['B']['metadata']
        st.metric("Video B - Engagement", f"{meta_b.get('engagement_rate', 0):.2f}%")
        st.write(f"Views: {meta_b.get('views', 0):,}")
        st.write(f"Likes: {meta_b.get('likes', 0):,} | Comments: {meta_b.get('comments', 0):,}")

    st.divider()

    # AUTO ANALYSIS
    st.subheader("🎯 Why One Video Has More Engagement")

    if st.button("📊 Generate Detailed Analysis", use_container_width=True, type="primary"):
        with st.spinner("🤖 Analyzing both videos..."):
            analysis = analyze_engagement_difference(
                st.session_state.videos['A'],
                st.session_state.videos['B']
            )
            if analysis:
                st.session_state.comparison_analysis = analysis

    if st.session_state.comparison_analysis:
        st.markdown(st.session_state.comparison_analysis)

    st.divider()

    # Chat
    if st.session_state.vector_store:
        st.subheader("💬 Ask Follow-up Questions")

        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])

        # Quick buttons
        col1, col2, col3 = st.columns(3)

        question = None
        with col1:
            if st.button("Get exact differences", use_container_width=True):
                question = "What are the exact content differences between Video A and B that explain the engagement gap?"

        with col2:
            if st.button("Hook comparison", use_container_width=True):
                question = "Compare the opening 10 seconds of both videos. What hook works better?"

        with col3:
            if st.button("Improvement tips", use_container_width=True):
                question = "Give 5 specific changes for the lower-engagement video based on what works in the higher-engagement one."

        # Chat input
        user_input = st.chat_input("Ask about the videos...")

        if user_input or question:
            query = question or user_input

            st.session_state.chat_history.append({"role": "user", "content": query})
            st.chat_message("user").write(query)

            response, citations = query_rag(query, st.session_state.vector_store, st.session_state.videos)

            if response:
                st.session_state.chat_history.append({"role": "assistant", "content": response})

                if citations:
                    st.markdown("**Sources:**")
                    for c in citations:
                        st.caption(f"📹 Video {c['video']} - {c['title']}")

st.divider()
st.markdown("""
### 📋 Features
✅ Automatic engagement analysis
✅ Compare hooks and structure
✅ Explain WHY one performs better
✅ Suggest specific improvements
✅ RAG with transcript search
✅ Streaming AI responses
✅ Source citations

Built with Streamlit + LangChain + OpenAI
""")
