"""LangChain agent factory for orchestration."""

from typing import List, Optional, Dict, Any
import logging

try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain.chat_models import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

from src.core.config import get_config
from src.core.exceptions import AgentError
from .sql_tool import SQLTool
from .vector_tool import VectorTool
from .vision_tool import VisionTool

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating LangChain agents."""
    
    @staticmethod
    def create_agent(
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Create LangChain agent with tools."""
        if not LANGCHAIN_AVAILABLE:
            raise AgentError("LangChain not available. Install langchain and langchain-openai")
        
        try:
            app_config = get_config()
            llm_config = app_config.llm
            
            # Get API key from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                # Try to get from config if available
                try:
                    config_dict = app_config.dict()
                    api_key = config_dict.get("openai_api_key")
                except:
                    pass
            
            if not api_key:
                raise AgentError("OPENAI_API_KEY environment variable not set. Set it in .env file or environment.")
            
            # Initialize LLM
            if llm_config.provider == "openai":
                llm = ChatOpenAI(
                    model=llm_config.model,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens,
                    openai_api_key=api_key
                )
            else:
                raise AgentError(f"Unsupported LLM provider: {llm_config.provider}")
            
            # Get tools
            if tools is None:
                # We need to initialize tools inside create_agent now because of the wiring
                # Reuse the logic we just put in _get_default_tools removal
                # Actually, best to move the wiring logic to a helper or put it here.
                # Let's put the logic here directly as the previous edit replaced _get_default_tools body but kept the method.
                # Wait, my previous edit replaced _get_default_tools body.
                # So tools = AgentFactory._get_default_tools() will work if I updated the method.
                # BUT the method is static and I need to instantiate classes.
                # Let's verify what I replaced.
                tools = AgentFactory._get_default_tools()
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a Safety Compliance Assistant for SecureOps.

GUARDRAILS:
1. You MUST answer using ONLY the provided context from the 'vector_search' or 'sql_analytics' tools.
2. If the answer is not in the context, respond with "I don't have that information in the safety reports."
3. Do NOT make up information or use outside knowledge.
4. Keep answers concise, professional, and safety-focused.

Your Capabilities:
1. vector_search: Search generated Safety Reports (PDFs) and compliance docs. Use this for specific violation details, rule explanations, and report summaries.
2. sql_analytics: Query aggregate statistics (e.g., "How many violations yesterday?").
3. vision_summary: Get general video context.

Strategy:
- Always try 'vector_search' first if the user asks about specific violations or rules.
- Think step by step."""),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent
            agent = create_openai_tools_agent(llm, tools, prompt)
            
            # Create executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            logger.info("LangChain agent created successfully")
            return agent_executor
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise AgentError(f"Agent creation failed: {e}") from e
    
    @staticmethod
    def _get_default_tools() -> List:
        """Get default tools for agent."""
        try:
            # Initialize RAG components
            from src.stages.documents.embedder import DocumentEmbedder
            from src.stages.documents.vector_store import VectorStore
            from src.agents.vector_tool import VectorTool as VectorService
            from langchain.tools import StructuredTool
            
            embedder = DocumentEmbedder()
            store = VectorStore()
            vector_service = VectorService(store)
            
            def rag_search(query: str) -> str:
                """Search safety reports and regulations."""
                try:
                    # RAG Flow: Embed -> Search
                    embedding = embedder.embed_chunk(
                        type('Chunk', (), {'content': query, 'chunk_id': '', 'document_id': '', 'chunk_index': 0, 'metadata': {}})()
                    )
                    results = vector_service.search(embedding)
                    
                    if not results:
                        return "No relevant documents found."
                        
                    formatted = f"Found {len(results)} relevant sections:\n\n"
                    for i, res in enumerate(results, 1):
                        formatted += f"{i}. {res.content[:200]}...\n(Doc: {res.document_id})\n\n"
                    return formatted
                except Exception as e:
                    return f"Search error: {e}"

            vector_tool = StructuredTool.from_function(
                func=rag_search,
                name="vector_search",
                description="Search safety reports and regulations. Input is a natural language question."
            )

            return [
                SQLTool(),
                vector_tool,
                VisionTool()
            ]
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            # Fallback to empty or raise
            return []
    
    @staticmethod
    def create_simple_agent(config: Optional[Dict[str, Any]] = None):
        """Create agent with default configuration."""
        return AgentFactory.create_agent(config=config)

