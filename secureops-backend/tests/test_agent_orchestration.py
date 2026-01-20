"""Tests for LangChain agent orchestration."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.agents.agent_factory import AgentFactory
from src.agents.sql_tool import SQLTool
from src.agents.vector_tool import VectorTool
from src.agents.vision_tool import VisionTool


class TestSQLTool:
    """Test SQL tool."""
    
    @patch('src.agents.sql_tool.get_db_session')
    def test_sql_tool(self, mock_db):
        """Test SQL tool execution."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.keys.return_value = ['count', 'class_name']
        mock_result.fetchall.return_value = [(10, 'person')]
        mock_session.execute.return_value = mock_result
        mock_db.return_value.__enter__.return_value = mock_session
        mock_db.return_value.__exit__.return_value = None
        
        tool = SQLTool()
        result = tool._run("How many people were detected?")
        
        assert "count" in result.lower() or "person" in result.lower()


class TestVectorTool:
    """Test vector tool."""
    
    @patch('src.agents.vector_tool.DocumentEmbedder')
    @patch('src.agents.vector_tool.VectorStore')
    def test_vector_tool(self, mock_store, mock_embedder):
        """Test vector tool execution."""
        # Mock embedder
        mock_emb = Mock()
        mock_emb.embed_chunk.return_value = np.random.rand(1536).astype(np.float32)
        mock_embedder.return_value = mock_emb
        
        # Mock vector store
        mock_vs = Mock()
        mock_vs.search.return_value = []
        mock_store.return_value = mock_vs
        
        tool = VectorTool()
        result = tool._run("What are the safety regulations?")
        
        assert isinstance(result, str)


class TestVisionTool:
    """Test vision tool."""
    
    @patch('src.agents.vision_tool.get_db_session')
    def test_vision_tool(self, mock_db):
        """Test vision tool execution."""
        mock_session = Mock()
        mock_upload = Mock()
        mock_upload.id = "test123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_upload
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_db.return_value.__enter__.return_value = mock_session
        mock_db.return_value.__exit__.return_value = None
        
        tool = VisionTool()
        result = tool._run("test123", "general")
        
        assert "test123" in result or "No detections" in result


class TestAgentFactory:
    """Test agent factory."""
    
    @patch('src.agents.agent_factory.ChatOpenAI')
    @patch('src.agents.agent_factory.create_openai_tools_agent')
    def test_create_agent(self, mock_create_agent, mock_llm):
        """Test agent creation."""
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        mock_agent = Mock()
        mock_executor = Mock()
        mock_create_agent.return_value = mock_agent
        
        with patch('src.agents.agent_factory.AgentExecutor', return_value=mock_executor):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                agent = AgentFactory.create_agent()
                
                assert agent is not None

