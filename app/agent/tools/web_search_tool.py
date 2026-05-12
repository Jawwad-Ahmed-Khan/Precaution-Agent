"""
This module provides the WebSearchTool for the Precaution Definer Agent.

The WebSearchTool is used for:
1. Road access status to the disaster area.
2. Current NGO operations on the ground.
3. Available emergency supplies in nearby cities.
4. Current weather affecting logistics.
5. Recent news about ongoing relief efforts.
"""

from agents import WebSearchTool

# Instantiate the built-in WebSearchTool
web_search_tool = WebSearchTool()
