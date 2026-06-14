import asyncio
import logging
import uuid
from app.agents.connector_agent import connector_agent
from app.firestore.graph_edges import graph_edges_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline():
    project_id = "test-project-456"
    ucd_id = str(uuid.uuid4())
    
    # Mock extracted entities
    entities = [
        {"id": "e1", "name": "Acme Corp", "type": "Organization"},
        {"id": "e2", "name": "Global Tech", "type": "Organization"}
    ]
    
    ucd_content = "Acme Corp acquired Global Tech on 2023-01-01."
    
    logger.info("=== TEST: Connector Agent & Temporal Edges ===")
    
    # Run Connector Agent
    links = await connector_agent.connect_entities(project_id, ucd_content, entities)
    
    logger.info(f"Connector Agent found {len(links)} links.")
    if links:
        link = links[0]
        logger.info(f"Link: {link.source_entity_id} -> {link.target_entity_id}")
        logger.info(f"Relationship: {link.relationship}")
        logger.info(f"Score: {link.score}")
        logger.info(f"Valid From: {link.valid_from}")
        
        # Convert links to dictionaries for the firestore store
        edge_dicts = [link.model_dump() for link in links]
        
        # Save to Firestore
        logger.info("\n=== Writing to Firestore Graph Edges ===")
        graph_edges_store.save_edges(project_id, ucd_id, edge_dicts)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
