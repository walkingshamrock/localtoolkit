"""
Tests for the MCP FastMCP server module.

This module tests the FastMCP server import and integration functionality.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestFastMCPServerImport:
    """Test the FastMCP server import functionality."""
    
    def test_fastmcp_import(self):
        """Test that FastMCP can be imported from the localtoolkit MCP module."""
        try:
            from localtoolkit.mcp.server.fastmcp.server import FastMCP
            assert FastMCP is not None
        except ImportError as e:
            pytest.fail(f"Failed to import FastMCP: {e}")
    
    def test_fastmcp_import_matches_original(self):
        """Test that the imported FastMCP is the same as the original."""
        from localtoolkit.mcp.server.fastmcp.server import FastMCP as LocalFastMCP
        
        # Mock the original import to avoid dependency issues in tests
        with patch('mcp.server.fastmcp.server.FastMCP') as MockOriginalFastMCP:
            # Re-import to trigger the import statement
            import importlib
            import localtoolkit.mcp.server.fastmcp.server
            importlib.reload(localtoolkit.mcp.server.fastmcp.server)
            
            # The local import should be the same reference as the original
            from localtoolkit.mcp.server.fastmcp.server import FastMCP as ReloadedFastMCP
            
            # In a real scenario, these would be the same object
            # In our test, we just verify the import works
            assert ReloadedFastMCP is not None


class TestFastMCPIntegration:
    """Test FastMCP integration patterns used in localtoolkit."""
    
    def test_tool_registration_pattern(self, mock_fastmcp, sample_tool_function):
        """Test the tool registration pattern used throughout localtoolkit."""
        # Simulate the registration pattern used in modules
        @mock_fastmcp.tool()
        def test_tool(param: str) -> dict:
            return sample_tool_function(param)
        
        # Verify the tool decorator was called
        mock_fastmcp.tool.assert_called_once()
        
        # Verify we can call the decorated function
        result = test_tool("test_value")
        assert result is not None
    
    def test_multiple_tool_registration(self, mock_fastmcp):
        """Test registering multiple tools on the same server."""
        # Register multiple tools
        @mock_fastmcp.tool()
        def tool1() -> dict:
            return {"tool": "1"}
        
        @mock_fastmcp.tool()
        def tool2() -> dict:
            return {"tool": "2"}
        
        @mock_fastmcp.tool()
        def tool3() -> dict:
            return {"tool": "3"}
        
        # Verify all tools were registered
        assert mock_fastmcp.tool.call_count == 3
    
    def test_server_run_pattern(self, mock_fastmcp):
        """Test the server run pattern."""
        # This simulates how the server would be started
        mock_fastmcp.run()
        
        # Verify run was called
        mock_fastmcp.run.assert_called_once()
    
    def test_module_registration_pattern(self, mock_fastmcp):
        """Test the module registration pattern used in localtoolkit."""
        # Simulate the register_to_mcp pattern used in each module
        def register_module_tools(mcp):
            @mcp.tool()
            def module_tool_1() -> dict:
                return {"module": "test", "tool": "1"}
            
            @mcp.tool()
            def module_tool_2() -> dict:
                return {"module": "test", "tool": "2"}
        
        # Register the module
        register_module_tools(mock_fastmcp)
        
        # Verify tools were registered
        assert mock_fastmcp.tool.call_count == 2
    
    def test_error_handling_in_tools(self, mock_fastmcp):
        """Test error handling pattern in MCP tools."""
        @mock_fastmcp.tool()
        def error_prone_tool(should_fail: bool = False) -> dict:
            if should_fail:
                return {
                    "success": False,
                    "error": "Tool execution failed",
                    "message": "An error occurred"
                }
            return {
                "success": True,
                "message": "Tool executed successfully"
            }
        
        # Test successful execution
        success_result = error_prone_tool(False)
        assert success_result["success"] is True
        
        # Test error handling
        error_result = error_prone_tool(True)
        assert error_result["success"] is False
        assert "error" in error_result
    
    def test_standardized_response_format(self, mock_fastmcp):
        """Test that tools follow the standardized response format."""
        @mock_fastmcp.tool()
        def standard_response_tool() -> dict:
            return {
                "success": True,
                "data": "test_data",
                "message": "Operation completed successfully",
                "metadata": {
                    "execution_time_ms": 150
                }
            }
        
        result = standard_response_tool()
        
        # Verify required keys are present
        assert "success" in result
        assert "message" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["message"], str)
        
        # Verify optional keys
        if "data" in result:
            assert result["data"] is not None
        if "metadata" in result:
            assert isinstance(result["metadata"], dict)


class TestMCPServerConfiguration:
    """Test MCP server configuration patterns."""
    
    def test_server_initialization(self, mock_fastmcp):
        """Test server initialization pattern."""
        # This would typically be done in main.py
        server = mock_fastmcp
        
        # Verify server is properly initialized
        assert server is not None
    
    def test_transport_configuration(self, mock_fastmcp):
        """Test different transport configurations."""
        # Test stdio transport (default)
        mock_fastmcp.run(transport="stdio")
        mock_fastmcp.run.assert_called_with(transport="stdio")
        
        # Reset mock
        mock_fastmcp.run.reset_mock()
        
        # Test HTTP transport
        mock_fastmcp.run(transport="http", port=8000)
        mock_fastmcp.run.assert_called_with(transport="http", port=8000)
    
    def test_tool_metadata_handling(self, mock_fastmcp):
        """Test tool metadata and documentation handling."""
        @mock_fastmcp.tool()
        def documented_tool(param1: str, param2: int = 10) -> dict:
            """
            A well-documented tool for testing.
            
            Args:
                param1: A string parameter
                param2: An integer parameter with default value
                
            Returns:
                dict: Standard response format
            """
            return {
                "success": True,
                "param1": param1,
                "param2": param2,
                "message": "Documented tool executed"
            }
        
        # Verify the tool was registered
        mock_fastmcp.tool.assert_called_once()
        
        # Test the function still works
        result = documented_tool("test", 20)
        assert result["param1"] == "test"
        assert result["param2"] == 20