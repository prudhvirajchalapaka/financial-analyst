import streamlit as st
import os
import tempfile
import shutil
from dotenv import load_dotenv
from src.ingest import load_pdf_elements
from src.summarize import generate_image_summaries
from src.rag import create_vector_db, get_rag_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Page Config
st.set_page_config(page_title="Financial AI Analyst", layout="wide")

# Check for API Key
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    st.error("CRITICAL ERROR: GOOGLE_API_KEY not found. Please check your .env file.")
    st.stop()

# --- FEATURE: Session State Management ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Stores UI messages
if "store" not in st.session_state:
    st.session_state.store = {} # Stores LangChain memory object

# --- FEATURE: Temporary Database Handling ---
# We create a specific temp folder for this session
if "temp_db_path" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
    st.session_state.temp_db_path = os.path.join(st.session_state.temp_dir, "chroma_db")
    st.session_state.db_ready = False

# Sidebar: Upload Section
with st.sidebar:
    st.header("📂 1. Upload Report")
    st.caption("Data is deleted when you refresh or close.")
    
    uploaded_file = st.file_uploader(
        "Drag & Drop PDF here", 
        type="pdf", 
        help="Upload a 10-K or Financial Report"
    )

    if uploaded_file and not st.session_state.db_ready:
        if st.button("Process PDF", type="primary"):
            with st.spinner("🔍 Reading text & Analyzing charts..."):
                # Save PDF to temp file
                temp_pdf_path = os.path.join(st.session_state.temp_dir, "temp.pdf")
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Create Image Directory in temp
                temp_img_dir = os.path.join(st.session_state.temp_dir, "images")
                os.makedirs(temp_img_dir, exist_ok=True)
                
                # Run Pipeline
                texts, tables = load_pdf_elements(temp_pdf_path, temp_img_dir)
                img_summaries, img_paths = generate_image_summaries(temp_img_dir)
                create_vector_db(texts, img_summaries, img_paths, st.session_state.temp_db_path)
                
                st.session_state.db_ready = True
                st.success("✅ Ready! Start chatting.")

    if st.session_state.db_ready:
        st.info("Database is Active in Temp Memory.")
        if st.button("Clear & Restart"):
            # Cleanup
            shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Main Chat Interface
st.title("🤖 Financial Multi-Modal Chat")
st.caption("I can read charts, tables, and text from your PDF.")

# 1. Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. Handle User Input
if user_input := st.chat_input("Ask about revenue, risks, or specific charts..."):
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    if not st.session_state.db_ready:
        with st.chat_message("assistant"):
            st.warning("⚠️ Please upload and process a PDF first.")
    else:
        # Generate Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    rag_chain = get_rag_chain(st.session_state.temp_db_path)
                    
                    # Manage History for LangChain
                    def get_session_history(session_id: str) -> BaseChatMessageHistory:
                        if session_id not in st.session_state.store:
                            st.session_state.store[session_id] = ChatMessageHistory()
                        return st.session_state.store[session_id]
                    
                    conversational_rag_chain = RunnableWithMessageHistory(
                        rag_chain,
                        get_session_history,
                        input_messages_key="input",
                        history_messages_key="chat_history",
                        output_messages_key="answer",
                    )
                    
                    response = conversational_rag_chain.invoke(
                        {"input": user_input},
                        config={"configurable": {"session_id": "current_session"}}
                    )
                    
                    answer_text = response["answer"]
                    st.markdown(answer_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer_text})
                    
                    # Optional: Show Sources Expander
                    with st.expander("View Source Evidence"):
                        for i, doc in enumerate(response["context"]):
                            source_type = doc.metadata.get("source", "unknown")
                            st.markdown(f"**Source {i+1} ({source_type}):**")
                            st.markdown(f"> {doc.page_content[:200]}...")
                            if source_type == "image":
                                st.image(doc.metadata["image_path"], caption="Found Chart", width=300)

                except Exception as e:
                    st.error(f"Error: {e}")
