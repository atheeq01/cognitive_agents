import logging
from typing import Dict, Any, List
from app.schemas.cognitive import CognitiveInsights
from app.schemas.similarity import SimilarityMatch

logger = logging.getLogger(__name__)

class ReportGenerator:
    def generate_markdown_report(self, 
                                 document_name: str, 
                                 upload_timestamp: str, 
                                 summary: str, 
                                 cognitive_insights: CognitiveInsights, 
                                 similarities: List[SimilarityMatch], 
                                 contradictions: List[Dict[str, Any]]) -> str:
        """
        Generates a clear, structured Markdown report based on the analysis.
        Satisfies requirements for explicit references, clarity, and specific formatting.
        """
        md = f"# Document Intelligence Report: {document_name}\n"
        md += f"**Upload Timestamp**: {upload_timestamp}\n\n"
        
        md += "## 1. Executive Summary\n"
        md += f"{summary}\n\n"
        
        md += "## 2. Cross-Document Similarity\n"
        if not similarities:
            md += "No significant overlaps found with previously uploaded documents.\n\n"
        else:
            for sim in similarities:
                md += f"**Compared against:** Document `{sim.document_id}` (Similarity Score: {sim.similarity_score:.2f})\n"
                md += "- **Overlapping Topics**:\n"
                for topic in sim.overlapping_topics:
                    md += f"  - {topic}\n"
                md += "\n"
                
        md += "## 3. Contradiction Analysis\n"
        if not contradictions:
            md += "No contradictions detected against previous documents.\n\n"
        else:
            for contra in contradictions:
                doc_id = contra.get('conflicting_document_id', 'Unknown')
                reasoning = contra.get('reasoning', '')
                quote_a = contra.get('quote_a', '')
                quote_b = contra.get('quote_b', '')
                md += f"**Contradiction with Document:** `{doc_id}`\n"
                md += f"- **Target Document Quote**: \"{quote_a}\"\n"
                md += f"- **Previous Document Quote**: \"{quote_b}\"\n"
                md += f"- **Analysis**: {reasoning}\n\n"
                
        md += "## 4. Deep Cognitive Insights\n"
        md += f"- **Primary Intent**: {cognitive_insights.intent}\n\n"
        
        md += "### Reasoning Patterns\n"
        for pattern in cognitive_insights.reasoning_patterns:
            md += f"- {pattern}\n"
        md += "\n"
        
        md += "### Unstated Assumptions\n"
        for assumption in cognitive_insights.assumptions:
            md += f"- {assumption}\n"
        md += "\n"
        
        md += "### Explicit Conclusions\n"
        for conclusion in cognitive_insights.conclusions:
            md += f"- {conclusion}\n"
        md += "\n"
        
        md += "### Key Entity Relationships\n"
        if not cognitive_insights.relationships:
            md += "No strong entity relationships extracted.\n"
        else:
            for rel in cognitive_insights.relationships:
                md += f"- **{rel.entity_a}** *{rel.relationship}* **{rel.entity_b}**\n"
                
        return md

report_generator = ReportGenerator()
