import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class ChatLLMResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question, based on the context.")
    sources_used: List[str] = Field(description="A list of the EXACT filenames of the sources used to answer the question. Must exactly match the filenames provided in the context. Empty if no sources were used.")


# RAG system prompt
_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful research assistant for the OmniMind intelligence platform. "
     "Answer the user's question using ONLY the provided context documents. "
     "If the context does not contain the answer, say so honestly. "
     "Always be concise and cite the source when possible. "
     "You must also return the EXACT filenames of the sources you actually used to formulate your answer.\n\n"
     "Context:\n{context}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])


class ChatService:
    def __init__(self):
        self.mock_mode = False
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_CHAT_MODEL,
                temperature=0.3,
            )
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for ChatService. Running in mock mode: {e}")
            self.mock_mode = True

    def _build_history(self, history: List[Dict[str, str]]):
        """Convert plain dict history to LangChain message objects."""
        messages = []
        for h in history:
            if h.get("role") == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h.get("role") == "assistant":
                messages.append(AIMessage(content=h["content"]))
        return messages

    async def get_response(self, project_id: str, message: str, history: List[Dict[str, str]]) -> ChatResponse:
        """
        Processes a chat message using a LangChain LCEL RAG pipeline.
        Scoped to the given project_id namespace in Pinecone.
        """
        if self.mock_mode:
            logger.info(f"[MOCK CHAT] Answering '{message}' for project {project_id}")
            return ChatResponse(
                answer=(
                    "This is a mock response from the RAG chatbot. "
                    "Configure GOOGLE_API_KEY and PINECONE_API_KEY to enable real answers."
                ),
                sources=[
                    {"filename": "Mock_Document.pdf", "excerpt": "This is a mock source excerpt.", "score": 0.95}
                ]
            )

        try:
            # Build Pinecone vector store for this project's namespace
            from langchain_pinecone import PineconeVectorStore
            from app.vector_store.pinecone_adapter import pinecone_adapter

            if not pinecone_adapter._index:
                # Pinecone not initialized — fall back to answering without context
                logger.warning("[ChatService] Pinecone not available, answering without retrieval context.")
                docs = []
            else:
                vectorstore = PineconeVectorStore(
                    index=pinecone_adapter._index,
                    embedding=self.embeddings,
                    namespace=str(project_id),
                )
                import asyncio
                retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
                docs = await asyncio.to_thread(retriever.invoke, message)

            # Format retrieved documents into a context string
            context_parts = []
            sources = []
            for doc in docs:
                excerpt = doc.page_content[:300]
                filename = doc.metadata.get("filename", "Unknown Document")
                context_parts.append(f"[{filename}]: {excerpt}")
                sources.append({
                    "filename": filename,
                    "excerpt": excerpt[:200] + "..." if len(excerpt) > 200 else excerpt,
                    "score": doc.metadata.get("score", None),
                })
            context_text = "\n\n".join(context_parts) if context_parts else "No relevant documents found."

            # Build the LCEL chain
            llm_with_tools = self.llm.with_structured_output(ChatLLMResponse)
            chain = _RAG_PROMPT | llm_with_tools

            result = await chain.ainvoke({
                "context": context_text,
                "history": self._build_history(history),
                "question": message,
            })

            answer = result.answer
            used_files = set(result.sources_used)

            # De-duplicate sources by filename and filter by used_files
            seen = set()
            unique_sources = []
            for s in sources:
                if s["filename"] not in seen and s["filename"] in used_files:
                    seen.add(s["filename"])
                    unique_sources.append(s)

            return ChatResponse(answer=answer, sources=unique_sources)

        except Exception as e:
            logger.error(f"ChatService failed: {e}", exc_info=True)
            raise


chat_service = ChatService()

