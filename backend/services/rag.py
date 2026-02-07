import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Singleton embedding function to avoid reloading
_embedding_function = None

def get_embedding_function():
    """Get or create the embedding function (singleton pattern)."""
    global _embedding_function
    if _embedding_function is None:
        print("--- Loading embedding model... ---")
        _embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedding_function

def create_vector_db(texts: list[str], image_summaries: list[str], image_paths: list[str], db_path: str):
    """
    Create a ChromaDB vector store from text and image summaries.
    
    Args:
        texts: List of text chunks
        image_summaries: List of image descriptions
        image_paths: List of paths to source images
        db_path: Path to persist the database
    """
    # Prepare Documents
    documents = [Document(page_content=t, metadata={"source": "text"}) for t in texts]
    for summary, path in zip(image_summaries, image_paths):
        doc = Document(page_content=summary, metadata={"source": "image", "image_path": path})
        documents.append(doc)

    print(f"--- Creating vector DB with {len(documents)} documents ---")
    embedding_function = get_embedding_function()
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        persist_directory=db_path
    )
    return vectorstore

def get_rag_chain(db_path: str):
    """
    Create a RAG chain with history-aware retrieval.
    
    Args:
        db_path: Path to the ChromaDB database
        
    Returns:
        A LangChain retrieval chain
    """
    embedding_function = get_embedding_function()
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embedding_function)
    
    # Improved Retrieval: Use MMR (Maximal Marginal Relevance) to get diverse chunks
    # This helps avoid getting 5 chunks that are all the same, ensuring broader context.
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 12,              # Get more chunks (since we have smaller chunks now)
            "fetch_k": 30,        # Initial fetch pool
            "lambda_mult": 0.7    # Balance between relevance (1.0) and diversity (0.0)
        }
    )
    
    # History-Aware Retrieval Prompt
    contextualize_q_system_prompt = """Given a chat history and the latest user question 
    which might reference context in the chat history, formulate a standalone question 
    which can be understood without the chat history. Do NOT answer the question, 
    just reformulate it if needed and otherwise return it as is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Answer Generation Prompt - STRICT GROUNDING
    qa_system_prompt = """You are a highly accurate financial analyst assistant. 
    Your goal is to provide precise, data-backed answers based ONLY on the provided context.
    
    RULES:
    1. **Strict Context Adherence**: Answer ONLY using the retrieved context. If the answer is not in the context, say "I cannot find this information in the document."
    2. **No Hallucinations**: Do not make up numbers, dates, or facts. Do not use outside knowledge unless it's general financial terminology definitions.
    3. **Citations**: When citing numbers or key facts, implicitly reference the source (e.g., "According to the text..." or "The table shows...").
    4. **Numerical Accuracy**: Double-check all numbers. If doing math, show your work briefly.
    5. **Tone**: Professional, objective, and concise.
    
    CONTEXT:
    {context}"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain
