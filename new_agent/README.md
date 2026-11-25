# AI Negotiation Agent - Complete System Documentation

## 🤖 Overview

This is a complete AI-powered negotiation agent system built from scratch using:
- **LangChain** for LLM orchestration and agent behavior
- **MCP (Model Context Protocol)** for context management and session persistence  
- **Google Gemini AI** for natural language processing
- **Advanced Negotiation Intelligence** for strategic decision-making

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    INTEGRATED SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Core Agent    │  │  Chat Interface │  │ Intelligence │ │
│  │   (LangChain)   │  │   (WebSocket)   │  │   Engine     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   MCP Server    │  │ Context Manager │                   │
│  │ (Persistence)   │  │   (State Mgmt)  │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 1. Core Agent (`new_agent/core/agent.py`)
- **NegotiationAgent**: Main AI agent class using LangChain
- **Tools Integration**: Market analysis, seller analysis, strategy selection
- **Memory Management**: Conversation buffer with context retention
- **Multi-phase Negotiation**: Handles different negotiation phases

### 2. MCP Server (`new_agent/mcp/server.py`)
- **Session Management**: Persistent storage of negotiation sessions
- **Context Updates**: Real-time context synchronization
- **Analytics**: Comprehensive session and global analytics
- **Data Persistence**: JSON-based storage with file backup

### 3. Chat Interface (`new_agent/interface/chat.py`)
- **Real-time Chat**: WebSocket-ready interactive interface
- **Message Handling**: Async message processing and routing
- **Typing Indicators**: Real-time status updates
- **Session Management**: Chat session lifecycle management

### 4. Intelligence Engine (`new_agent/intelligence/strategy.py`)
- **Seller Analysis**: AI-powered personality and behavior analysis
- **Market Intelligence**: Dynamic market analysis and pricing trends
- **Tactic Recommendation**: Strategic negotiation tactic selection
- **Performance Scoring**: Comprehensive negotiation evaluation

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create the new_agent directory
cd new_agent

# Install requirements
pip install -r requirements.txt

# Set up environment variables
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 2. Basic Usage

```python
import asyncio
from new_agent.main import IntegratedNegotiationSystem

async def quick_start():
    # Initialize system
    system = IntegratedNegotiationSystem()
    await system.initialize("your_gemini_api_key")
    
    # Define product and goals
    product_info = {
        "name": "iPhone 13 Pro",
        "listed_price": 800.0,
        "condition": "like-new",
        "seller_name": "John",
        "platform": "facebook"
    }
    
    goals = {
        "target_price": 650.0,
        "max_budget": 720.0,
        "personality": "friendly"
    }
    
    # Start negotiation
    chat_id = await system.start_negotiation("user123", product_info, goals)
    
    # Process seller message
    result = await system.process_seller_message(
        chat_id, 
        "Hi! The phone is in perfect condition. I'm asking $800."
    )
    
    print(f"Agent Response: {result['agent_response']}")

# Run
asyncio.run(quick_start())
```

### 3. CLI Interface

```bash
# Run full CLI interface
python -m new_agent.main

# Run quick demos
python -m new_agent.main demo
```

## 📖 Detailed Usage Guide

### Core Features

#### 1. Multi-Phase Negotiation
The system handles negotiations through distinct phases:

- **Greeting**: Initial rapport building
- **Discovery**: Information gathering about product and seller
- **Initial Positioning**: Setting negotiation anchors
- **Active Negotiation**: Back-and-forth offer exchanges
- **Concession Trading**: Strategic compromises
- **Closing**: Final agreement or walkaway

#### 2. Advanced Negotiation Tactics

**Positioning Tactics:**
- **Anchoring**: Set favorable reference points
- **Framing**: Present information strategically
- **Bracketing**: Use extreme positions to make targets reasonable

**Pressure Tactics:**
- **Scarcity**: Create urgency through limited availability
- **Deadline Pressure**: Use time constraints effectively
- **Strategic Walkaway**: Threaten to leave negotiation

**Value-based Tactics:**
- **Value Stacking**: Emphasize total value proposition
- **Bundling/Unbundling**: Package optimization
- **Problem Solving**: Collaborative approach

#### 3. Intelligent Seller Analysis

The system analyzes sellers across multiple dimensions:

```python
# Seller personality types detected
- ANALYTICAL: Data-driven, logical
- DRIVER: Results-focused, impatient  
- EXPRESSIVE: Emotional, relationship-focused
- AMIABLE: Friendly, cooperative
```

#### 4. Market Intelligence

Real-time market analysis includes:
- Comparable price analysis
- Market trend detection
- Supply/demand indicators
- Seasonal adjustment factors

### API Reference

#### Core Classes

**IntegratedNegotiationSystem**
```python
# Main system class
system = IntegratedNegotiationSystem()
await system.initialize(api_key)
chat_id = await system.start_negotiation(user_id, product_info, goals)
result = await system.process_seller_message(chat_id, message)
analytics = await system.get_session_analytics(chat_id)
```

**NegotiationAgent**
```python
# Core AI agent
agent = NegotiationAgent(api_key)
response = await agent.start_negotiation(product, goals)
reply = await agent.respond_to_seller(seller_message)
```

**NegotiationIntelligenceEngine**
```python
# Strategy and analysis engine
intel = NegotiationIntelligenceEngine()
seller_analysis = await intel.analyze_seller(history, messages)
tactics = await intel.recommend_tactics(analysis, market_data, context, phase)
```

## 🎯 Negotiation Strategies

### 1. Personality-Based Approaches

**For Analytical Sellers:**
- Use data and market comparisons
- Provide detailed justifications
- Focus on logical arguments
- Avoid high-pressure tactics

**For Driver Personalities:**
- Be direct and concise
- Focus on bottom-line results  
- Use time-based pressure effectively
- Avoid lengthy relationship building

**For Expressive Types:**
- Build personal connections
- Use emotional appeals
- Reference social proof
- Create excitement about the deal

**For Amiable Sellers:**
- Emphasize mutual benefit
- Use collaborative language
- Avoid confrontational approaches
- Build long-term relationship focus

### 2. Phase-Specific Strategies

**Opening Phase:**
```python
# Focus on relationship building and information gathering
recommended_tactics = [
    "LIKING",  # Build personal connection
    "INFORMATION_GATHERING",  # Learn seller's situation
    "VALUE_STACKING"  # Understand full value proposition
]
```

**Active Negotiation:**
```python  
# Strategic positioning and offer exchanges
recommended_tactics = [
    "ANCHORING",  # Set favorable reference points
    "RECIPROCITY",  # Give-and-take dynamics
    "CONTRAST_PRINCIPLE"  # Make offers seem reasonable
]
```

**Closing Phase:**
```python
# Final push toward agreement
recommended_tactics = [
    "COMPROMISE",  # Find mutually acceptable solution
    "INCREMENTAL_COMMITMENT",  # Secure agreement on points
    "DEADLINE_PRESSURE"  # Create decision urgency
]
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
NEGOTIATION_DATA_PATH=./negotiation_data
LOG_LEVEL=INFO
MAX_NEGOTIATION_ROUNDS=10
DEFAULT_AGENT_PERSONALITY=friendly
```

### System Configuration
```python
config = {
    "max_memory_messages": 20,
    "default_timeout": 30,
    "enable_analytics": True,
    "auto_save_sessions": True,
    "market_analysis_enabled": True
}

system = IntegratedNegotiationSystem(config)
```

## 📊 Analytics and Monitoring

### Session Analytics
```python
analytics = await system.get_session_analytics(chat_id)

# Returns:
{
    "duration_minutes": 15.5,
    "message_count": 12,
    "negotiation_rounds": 4,
    "performance": {
        "overall_score": 85.2,
        "savings_achieved": 15.0,
        "target_achievement": 90.5
    },
    "tactics_effectiveness": [
        {"tactic": "anchoring", "success_rate": 0.8},
        {"tactic": "compromise", "success_rate": 0.9}
    ]
}
```

### Performance Scoring
The system calculates comprehensive performance scores:

- **Overall Score**: Weighted combination of all metrics (0-100)
- **Savings Achievement**: Percentage savings vs. listed price
- **Target Achievement**: How close to target price (0-100%)
- **Budget Efficiency**: Optimal use of available budget
- **Performance Grade**: Letter grade (A-F)

## 🧪 Testing and Development

### Running Tests
```bash
# Unit tests
pytest new_agent/tests/

# Integration tests  
python -m new_agent.main demo

# Interactive testing
python -m new_agent.main
# Choose option 6 for demo mode
```

### Development Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable development features
config = {
    "debug_mode": True,
    "mock_market_data": True,
    "simulate_seller_responses": True
}
```

## 🚀 Deployment Options

### 1. Standalone Application
```bash
python -m new_agent.main
```

### 2. Web API Integration
```python
from fastapi import FastAPI
from new_agent.main import IntegratedNegotiationSystem

app = FastAPI()
system = IntegratedNegotiationSystem()

@app.post("/negotiate")
async def negotiate_endpoint(request: NegotiationRequest):
    result = await system.process_seller_message(
        request.chat_id, 
        request.message
    )
    return result
```

### 3. WebSocket Real-time
```python
# Real-time WebSocket integration ready
# See chat.py for WebSocket handlers
```

## 🎓 Advanced Usage Examples

### Custom Negotiation Strategy
```python
# Create custom tactic
class CustomTactic(BaseTool):
    name = "custom_pressure"
    description = "Apply custom pressure based on seller urgency"
    
    def _run(self, context: str) -> str:
        # Custom logic here
        return "Custom negotiation response"

# Add to agent
agent.tools.append(CustomTactic())
```

### Multi-product Negotiation
```python
# Handle bundle negotiations
products = [
    {"name": "iPhone", "price": 800},
    {"name": "AirPods", "price": 200}
]

# System automatically handles bundling tactics
bundle_context = {"products": products, "bundle_discount": 0.1}
```

### Integration with Marketplace APIs
```python
# Placeholder for marketplace integration
class MarketplaceConnector:
    async def fetch_product_data(self, url: str):
        # Scrape product information
        pass
    
    async def send_message(self, seller_id: str, message: str):
        # Send message through marketplace API
        pass
```

## 🤝 Contributing

To extend the system:

1. **Add New Tactics**: Extend `NegotiationTactic` enum and implement in intelligence engine
2. **Custom Tools**: Create new LangChain tools for specific marketplace features
3. **Enhanced Analytics**: Add new metrics to analytics engine
4. **UI Components**: Build web interface using the chat interface API

## 📈 Performance Optimization

### Memory Management
- Automatic conversation buffer pruning
- Context compression for long negotiations
- Efficient session storage with JSON serialization

### Response Speed
- Async processing throughout
- Parallel tool execution
- Cached market intelligence

### Scalability
- Stateless core agent design
- Persistent session storage
- Horizontal scaling ready

## ⚠️ Important Notes

1. **API Keys**: Ensure proper Gemini API key configuration
2. **Rate Limits**: Respect AI service rate limits in production
3. **Data Privacy**: Session data is stored locally by default
4. **Legal Compliance**: Ensure negotiations comply with platform terms of service
5. **Testing**: Always test with simulated scenarios before live usage

## 🎯 Success Metrics

The system tracks multiple success metrics:

- **Negotiation Success Rate**: Percentage of successful deals
- **Average Savings**: Mean savings achieved across sessions  
- **Time Efficiency**: Average time to reach agreement
- **User Satisfaction**: Based on target achievement
- **Tactic Effectiveness**: Success rate by negotiation tactic

This comprehensive system provides enterprise-grade negotiation capabilities with full observability, analytics, and extensibility for various marketplace scenarios.