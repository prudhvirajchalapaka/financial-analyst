import os
import shutil
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# --- FEATURE: Dynamic Temporary DB ---
# We will pass the DB path dynamically so it can be a temp folder
def create_vector_db(texts, image_summaries, image_paths, db_path):
    # 1. Prepare Documents
    documents = [Document(page_content=t, metadata={"source": "text"}) for t in texts]
    for summary, path in zip(image_summaries, image_paths):
        doc = Document(page_content=summary, metadata={"source": "image", "image_path": path})

    # 2. Create Embeddings (Local CPU)
    print("--- Creating Embeddings locally... ---")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # 3. Save to the specific Temp Path
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        persist_directory=db_path
    )
    return vectorstore

def get_rag_chain(db_path):
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embedding_function)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    # --- FEATURE: History-Aware Retrieval ---
    # This prompt tells the AI: "If the user asks a follow-up question, rewrite it to be standalone."
    contextualize_q_system_prompt = """Given a chat history and the latest user question 
    which might reference context in the chat history, formulate a standalone question 
    which can be understood without the chat history. Do NOT answer the question, 
    just reformulate it if needed and otherwise return it as is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # The Answer Prompt
    qa_system_prompt = """You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise.
    
    {context}"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # We build a chain that handles History -> Retrieval -> Answer
    from langchain.chains import create_history_aware_retriever, create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain
