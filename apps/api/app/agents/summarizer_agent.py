import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class SummaryResponse(BaseModel):
    summary: str = Field(description="A concise summary of the text chunk")

class SummarizerAgent:
    def __init__(self):
        self.mock_mode = False
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_TEXT_MODEL,
                temperature=0.3, # Slightly higher temperature for summary generation
            ).with_structured_output(SummaryResponse)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini. Running SummarizerAgent in mock mode: {e}")
            self.mock_mode = True

    async def summarize_chunk(self, project_id: str, chunk_text: str) -> str:
        """
        Takes a raw chunk of text and uses Gemini to generate a concise summary.
        """
        if self.mock_mode:
            logger.info(f"[MOCK SUMMARIZER] Summarizing chunk for project {project_id}")
            return "This is a mock summary of the provided text."

        prompt = f"""
        You are a highly capable summarizer agent serving project {project_id}.
        Your job is to read the following text chunk and provide a clear, concise summary of the main points.
        Do not include external information.

        TEXT:
        {chunk_text}
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.summary
        except Exception as e:
            logger.error(f"Failed to summarize chunk: {e}")
            raise

summarizer_agent = SummarizerAgent()
