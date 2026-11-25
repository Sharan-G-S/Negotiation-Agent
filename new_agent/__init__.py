"""
AI Negotiation Agent - New Architecture
Complete rewrite with LangChain, MCP, and advanced intelligence
"""

__version__ = "2.0.0"
__author__ = "AI Negotiation Team" 
__description__ = "Advanced AI-powered marketplace negotiation agent"

# Core components
from .main import IntegratedNegotiationSystem, NegotiationSystemCLI

# Individual modules available for advanced usage
from .core.agent import NegotiationAgent, ProductInfo, NegotiationGoals
from .mcp.server import NegotiationMCPServer, NegotiationContextManager
from .interface.chat import NegotiationChatInterface, ConsoleChatInterface
from .intelligence.strategy import NegotiationIntelligenceEngine

__all__ = [
    "IntegratedNegotiationSystem",
    "NegotiationSystemCLI",
    "NegotiationAgent", 
    "ProductInfo",
    "NegotiationGoals",
    "NegotiationMCPServer",
    "NegotiationContextManager", 
    "NegotiationChatInterface",
    "ConsoleChatInterface",
    "NegotiationIntelligenceEngine"
]