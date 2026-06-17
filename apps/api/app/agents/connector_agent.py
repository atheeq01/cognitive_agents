import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class EntityLink(BaseModel):
    source_entity_id: str = Field(description="The ID of the source entity")
    target_entity_id: str = Field(description="The ID of the target entity")
    relationship: str = Field(description="A description of the relationship")
    score: float = Field(description="The strength score of the relationship: exact=1.0, embedding_sim>0.9=0.8, causal=0.6, co-mention=0.3")
    valid_from: Optional[str] = Field(None, description="Start date of relationship if temporal")
    valid_to: Optional[str] = Field(None, description="End date of relationship if temporal")

class ConnectorAgentResponse(BaseModel):
    links: List[EntityLink]

class ConnectorAgent:
    def __init__(self):
        self.mock_mode = False
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_TEXT_MODEL,
                temperature=0.0,
            ).with_structured_output(ConnectorAgentResponse)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for ConnectorAgent. Running in mock mode: {e}")
            self.mock_mode = True

    async def connect_entities(self, project_id: str, ucd_content: str, extracted_entities: List[Dict[str, Any]]) -> List[EntityLink]:
        """
        Evaluates relationships between entities found within a document and assigns a link score.
        """
        if self.mock_mode:
            logger.info(f"[MOCK CONNECTOR] Connecting entities for project {project_id}")
            if not extracted_entities:
                return []
            return [
                EntityLink(
                    source_entity_id=extracted_entities[0].get("id", "entity_1"),
                    target_entity_id="entity_2",
                    relationship="subsidiary of",
                    score=0.6,
                    valid_from="2023-01-01",
                    valid_to=None
                )
            ]

        entities_context = "\n".join([f"ID: {e.get('id')} - {e.get('name')} ({e.get('type')})" for e in extracted_entities])

        prompt = f"""
        You are the ConnectorAgent for project {project_id}.
        Identify relationships between the following entities based on the text.
        
        ENTITIES:
        {entities_context}
        
        TEXT:
        <untrusted_document_content>
        {ucd_content}
        </untrusted_document_content>
        
        SCORING RULES:
        - Exact identity match: 1.0
        - High confidence semantic relationship: 0.8
        - Direct causal link identified in text: 0.6
        - Merely co-mentioned in the same sentence: 0.3
        
        Also extract any temporal boundaries (`valid_from`, `valid_to`) if explicitly stated.
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.links
        except Exception as e:
            logger.error(f"Failed to connect entities: {e}")
            raise

connector_agent = ConnectorAgent()
