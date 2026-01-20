"""SQL tool for LangChain agent."""

from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import text
import logging

from src.db.session import get_db_session
from src.db.models import Detection

logger = logging.getLogger(__name__)


class SQLToolInput(BaseModel):
    """Input for SQL tool."""
    query: str = Field(description="Natural language query about video detections")


class SQLTool(BaseTool):
    """SQL analytics tool for querying detection data."""
    
    name = "sql_analytics"
    description = """
    Use this tool to query structured video detection data from the database.
    This tool can answer questions about:
    - Detection counts (people, machinery, PPE violations)
    - Time-based analytics (detections over time, peak hours)
    - Video statistics (total videos processed, frames analyzed)
    - Compliance metrics (PPE violations, proximity violations)
    
    Input should be a natural language question about the video data.
    """
    args_schema = SQLToolInput
    
    def _run(self, query: str) -> str:
        """Execute SQL query based on natural language."""
        try:
            # Parse query and generate SQL
            sql_query = self._parse_query(query)
            
            # Execute query
            with get_db_session() as session:
                result = session.execute(text(sql_query))
                rows = result.fetchall()
                
                # Format results
                if not rows:
                    return "No results found."
                
                # Convert to readable format
                columns = result.keys()
                formatted_results = []
                
                for row in rows[:50]:  # Limit to 50 rows
                    row_dict = dict(zip(columns, row))
                    formatted_results.append(row_dict)
                
                return self._format_results(formatted_results, query)
                
        except Exception as e:
            logger.error(f"SQL tool error: {e}")
            return f"Error executing query: {str(e)}"
    
    def _parse_query(self, query: str) -> str:
        """Parse natural language query to SQL."""
        query_lower = query.lower()
        
        # Detection counts
        if "count" in query_lower or "how many" in query_lower:
            if "person" in query_lower or "people" in query_lower:
                return """
                    SELECT COUNT(*) as count, class_name
                    FROM detections
                    WHERE class_name = 'person'
                    GROUP BY class_name
                """
            elif "machinery" in query_lower or "vehicle" in query_lower:
                return """
                    SELECT COUNT(*) as count, class_name
                    FROM detections
                    WHERE class_name IN ('car', 'bus', 'truck')
                    GROUP BY class_name
                """
            else:
                return """
                    SELECT class_name, COUNT(*) as count
                    FROM detections
                    GROUP BY class_name
                    ORDER BY count DESC
                """
        
        # Time-based queries
        elif "time" in query_lower or "when" in query_lower or "hour" in query_lower:
            return """
                SELECT DATE_TRUNC('hour', timestamp) as hour, 
                       COUNT(*) as detection_count,
                       class_name
                FROM detections
                GROUP BY hour, class_name
                ORDER BY hour DESC
                LIMIT 24
            """
        
        # Video statistics
        elif "video" in query_lower:
            return """
                SELECT 
                    COUNT(DISTINCT video_id) as total_videos,
                    COUNT(*) as total_detections,
                    COUNT(DISTINCT frame_number) as total_frames
                FROM detections
            """
        
        # Default: all detections summary
        else:
            return """
                SELECT 
                    class_name,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM detections
                GROUP BY class_name
                ORDER BY count DESC
            """
    
    def _format_results(self, results: list, original_query: str) -> str:
        """Format SQL results for agent."""
        if not results:
            return "No results found."
        
        if len(results) == 1 and len(results[0]) == 1:
            # Single value result
            value = list(results[0].values())[0]
            return f"The answer is: {value}"
        
        # Multiple results
        formatted = "Query results:\n"
        for i, row in enumerate(results[:10], 1):  # Limit to 10 rows
            formatted += f"{i}. {row}\n"
        
        if len(results) > 10:
            formatted += f"\n... and {len(results) - 10} more results."
        
        return formatted
    
    async def _arun(self, query: str) -> str:
        """Async version."""
        return self._run(query)

