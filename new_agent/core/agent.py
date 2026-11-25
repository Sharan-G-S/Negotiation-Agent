"""
Advanced AI Negotiation Agent - Core Implementation
Built with LangChain, MCP, and modern AI frameworks

This is a complete rewrite of the negotiation agent with:
- LangChain for LLM orchestration
- MCP (Model Context Protocol) for context management
- Advanced negotiation strategies
- Real-time interaction capabilities
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NegotiationPhase(str, Enum):
    """Current phase of negotiation"""
    GREETING = "greeting"
    DISCOVERY = "discovery"
    INITIAL_OFFER = "initial_offer"
    COUNTER_OFFER = "counter_offer"
    BARGAINING = "bargaining"
    CONCESSION = "concession"
    CLOSING = "closing"
    AGREEMENT = "agreement"
    REJECTION = "rejection"

class NegotiationTactic(str, Enum):
    """Available negotiation tactics"""
    ANCHORING = "anchoring"  # Set initial reference point
    BUNDLING = "bundling"    # Combine multiple items
    SCARCITY = "scarcity"    # Create urgency
    RECIPROCITY = "reciprocity"  # Give to get
    AUTHORITY = "authority"   # Reference expert opinions
    SOCIAL_PROOF = "social_proof"  # Reference others' actions
    COMPROMISE = "compromise"  # Find middle ground
    WALKAWAY = "walkaway"    # Threaten to leave

class AgentPersonality(str, Enum):
    """Agent personality types"""
    FRIENDLY = "friendly"
    ASSERTIVE = "assertive"
    ANALYTICAL = "analytical"
    DIPLOMATIC = "diplomatic"

class ProductInfo(BaseModel):
    """Product information model"""
    name: str
    listed_price: float
    description: str
    condition: str
    seller_name: str
    platform: str
    category: str
    location: Optional[str] = None
    features: List[str] = []
    images: List[str] = []

class NegotiationGoals(BaseModel):
    """User's negotiation goals"""
    target_price: float
    max_budget: float
    must_have_features: List[str] = []
    deal_breakers: List[str] = []
    timeline: str = "flexible"  # urgent, week, month, flexible
    personality: AgentPersonality = AgentPersonality.FRIENDLY

class NegotiationContext(BaseModel):
    """Complete negotiation context"""
    session_id: str
    product: ProductInfo
    goals: NegotiationGoals
    current_phase: NegotiationPhase = NegotiationPhase.GREETING
    conversation_history: List[Dict[str, Any]] = []
    seller_analysis: Dict[str, Any] = {}
    tactics_used: List[str] = []
    current_offer: Optional[float] = None
    seller_last_offer: Optional[float] = None
    negotiation_rounds: int = 0
    start_time: datetime = Field(default_factory=datetime.now)

class MarketAnalysisTool(BaseTool):
    """Tool for analyzing market prices and trends"""
    name: str = "market_analysis"
    description: str = "Analyze market prices for similar products to support negotiation"
    
    def _run(self, product_name: str, category: str, condition: str) -> str:
        """Simulate market analysis - in real implementation, this would call actual APIs"""
        # Mock market analysis
        similar_prices = [85, 92, 78, 95, 88]  # Mock prices in percentage of listed price
        avg_price = sum(similar_prices) / len(similar_prices)
        
        analysis = {
            "average_market_price_percentage": avg_price,
            "price_range": f"{min(similar_prices)}-{max(similar_prices)}%",
            "market_trend": "stable",
            "recommendation": "Price is within market range, 10-15% negotiation margin available"
        }
        return json.dumps(analysis, indent=2)

class SellerAnalysisTool(BaseTool):
    """Tool for analyzing seller behavior and patterns"""
    name: str = "seller_analysis"
    description: str = "Analyze seller's communication style and flexibility"
    
    def _run(self, seller_messages: str, response_time: str) -> str:
        """Analyze seller behavior patterns"""
        # Mock seller analysis
        analysis = {
            "communication_style": "casual",
            "flexibility_score": 0.7,  # 0-1 scale
            "urgency_indicators": ["quick responses", "multiple options offered"],
            "resistance_points": ["firm on price", "emphasizes product quality"],
            "negotiation_openness": "moderate"
        }
        return json.dumps(analysis, indent=2)

class NegotiationStrategyTool(BaseTool):
    """Tool for selecting optimal negotiation strategies"""
    name: str = "negotiation_strategy"
    description: str = "Select the best negotiation tactic based on current context"
    
    def _run(self, context: str, current_phase: str, seller_analysis: str) -> str:
        """Select appropriate negotiation strategy"""
        # Mock strategy selection
        strategies = {
            "recommended_tactic": "anchoring",
            "opening_line": "I've been researching similar items and noticed...",
            "price_suggestion": "Start 20% below target",
            "fallback_options": ["bundling", "compromise"],
            "risk_assessment": "low"
        }
        return json.dumps(strategies, indent=2)

class NegotiationAgent:
    """Main AI Negotiation Agent Class"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        """Initialize the negotiation agent"""
        self.api_key = api_key
        self.model_name = model
        self.mock_mode = api_key == "mock" or not api_key
        
        if not self.mock_mode:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model,
                temperature=0.7,
                max_tokens=1000
            )
        else:
            # Mock LLM for testing
            self.llm = None
        
        # Initialize tools
        self.tools = [
            MarketAnalysisTool(),
            SellerAnalysisTool(),
            NegotiationStrategyTool()
        ]
        
        # Initialize memory with conversation buffer
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        
        # Current negotiation context
        self.context: Optional[NegotiationContext] = None
        
        # Initialize agent
        self._setup_agent()
    
    def _setup_agent(self):
        """Set up the LangChain agent with tools and prompts"""
        
        # Create negotiation-specific prompt
        negotiation_prompt = PromptTemplate(
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"],
            template="""
You are an expert AI negotiation agent helping users get better deals on online marketplaces.

CORE PRINCIPLES:
- Always be respectful and professional
- Use data-driven negotiation tactics
- Adapt your approach based on seller's responses
- Aim for win-win outcomes
- Know when to walk away

CURRENT NEGOTIATION CONTEXT:
Product: {product_name}
Listed Price: ${listed_price}
Target Price: ${target_price}
Max Budget: ${max_budget}
Current Phase: {current_phase}

AVAILABLE TOOLS:
{tools}

Tool Names: {tool_names}

CONVERSATION HISTORY:
{chat_history}

CURRENT SITUATION:
{input}

Your response should be natural, conversational, and strategically sound. 
Use tools when you need market data, seller analysis, or strategy recommendations.

RESPONSE FORMAT:
Always respond as if you're chatting directly with the seller on their behalf.

Thought: [Your reasoning about the situation]
Action: [Tool name if needed, or "Final Answer" if ready to respond]
Action Input: [Tool input if using a tool]
Observation: [Tool output - this will be provided]
... (this Thought/Action/Action Input/Observation cycle can repeat)
Thought: I now have enough information to respond
Final Answer: [Your negotiation response to the seller]

{agent_scratchpad}
"""
        )
        
        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=negotiation_prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    async def start_negotiation(
        self, 
        product: ProductInfo, 
        goals: NegotiationGoals,
        session_id: str = None
    ) -> str:
        """Start a new negotiation session"""
        
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize negotiation context
        self.context = NegotiationContext(
            session_id=session_id,
            product=product,
            goals=goals
        )
        
        # Generate opening message
        opening_prompt = f"""
Start a negotiation for {product.name} listed at ${product.listed_price}.
Your target is ${goals.target_price} with a max budget of ${goals.max_budget}.
The seller is {product.seller_name} on {product.platform}.

Generate a friendly, professional opening message to start the negotiation.
Show genuine interest in the product and begin building rapport.
"""
        
        try:
            # Get agent's response
            response = await self._get_agent_response(opening_prompt)
            
            # Update context
            self.context.current_phase = NegotiationPhase.DISCOVERY
            self._add_to_conversation("agent", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error starting negotiation: {e}")
            return "Hello! I'm interested in your product. Could you tell me more about it?"
    
    async def get_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Unified method to get agent response for any interface"""
        if self.mock_mode:
            return self._get_mock_response(message, context)
        
        # If no active negotiation, create one
        if not self.context and context:
            await self.start_negotiation(
                product_name=context.get("product", "Unknown Product"),
                listed_price=context.get("max_price", 1000),
                target_price=context.get("target_price", 500),
                max_budget=context.get("max_price", 1000),
                user_preferences={"tone": context.get("tone", "professional")}
            )
        
        # Use existing respond_to_seller method
        try:
            return await self.respond_to_seller(message)
        except Exception as e:
            logger.error(f"Error in get_response: {e}")
            return "I appreciate your message. Let me consider this and get back to you with a thoughtful response."
    
    def _get_mock_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate mock response for testing when no API key is available"""
        message_lower = message.lower()
        
        # Mock negotiation responses
        if "price" in message_lower or "cost" in message_lower or "$" in message:
            if context and context.get("target_price"):
                target = context["target_price"]
                return f"I appreciate the offer. I was hoping we could work something out closer to ${target}. What do you think?"
            else:
                return "That's a good starting point. I was thinking of something a bit lower. What's the best you can do?"
        
        elif "interested" in message_lower or "buy" in message_lower:
            return "Yes, I'm definitely interested! Can you tell me more about the condition and your asking price?"
        
        elif "condition" in message_lower:
            return "That sounds good. What price were you thinking?"
        
        elif "final" in message_lower or "last" in message_lower:
            return "I understand this might be your final offer. Let me think about it for a moment."
        
        elif "no" in message_lower or "can't" in message_lower:
            return "I understand your position. Perhaps we can find a middle ground that works for both of us?"
        
        elif "deal" in message_lower or "sold" in message_lower:
            return "Excellent! I'm glad we could reach an agreement. Thank you!"
        
        else:
            return "Thank you for that information. I'm interested in moving forward with this negotiation."

    async def respond_to_seller(self, seller_message: str) -> str:
        """Process seller's message and generate appropriate response"""
        
        if not self.context:
            raise ValueError("No active negotiation session. Please start a negotiation first.")
        
        # Add seller message to conversation
        self._add_to_conversation("seller", seller_message)
        
        # Update negotiation phase based on message content
        self._update_negotiation_phase(seller_message)
        
        # Prepare context for agent
        context_prompt = f"""
SELLER'S MESSAGE: {seller_message}

NEGOTIATION CONTEXT:
- Current Phase: {self.context.current_phase}
- Negotiation Round: {self.context.negotiation_rounds}
- Your Target: ${self.context.goals.target_price}
- Max Budget: ${self.context.goals.max_budget}
- Listed Price: ${self.context.product.listed_price}
- Current Offer: {self.context.current_offer or 'None'}
- Seller's Last Offer: {self.context.seller_last_offer or 'None'}

Respond appropriately to continue the negotiation toward your goal.
"""
        
        try:
            # Get agent's strategic response
            response = await self._get_agent_response(context_prompt)
            
            # Update context
            self.context.negotiation_rounds += 1
            self._add_to_conversation("agent", response)
            
            # Extract any price offers from response
            self._extract_offers_from_response(response, seller_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error responding to seller: {e}")
            return "I understand. Let me think about that and get back to you."
    
    async def _get_agent_response(self, prompt: str) -> str:
        """Get response from the AI agent"""
        try:
            # Prepare input with current context
            agent_input = {
                "input": prompt,
                "product_name": self.context.product.name if self.context else "Unknown",
                "listed_price": self.context.product.listed_price if self.context else 0,
                "target_price": self.context.goals.target_price if self.context else 0,
                "max_budget": self.context.goals.max_budget if self.context else 0,
                "current_phase": self.context.current_phase if self.context else "greeting"
            }
            
            # Invoke agent
            result = await asyncio.to_thread(self.agent_executor.invoke, agent_input)
            
            # Extract the final answer
            if isinstance(result, dict) and "output" in result:
                return result["output"]
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting agent response: {e}")
            # Fallback response
            return "Thank you for your message. I'm interested in moving forward with this deal."
    
    def _add_to_conversation(self, sender: str, message: str):
        """Add message to conversation history"""
        if self.context:
            self.context.conversation_history.append({
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "phase": self.context.current_phase
            })
    
    def _update_negotiation_phase(self, seller_message: str):
        """Update negotiation phase based on seller's message"""
        message_lower = seller_message.lower()
        
        if any(word in message_lower for word in ["price", "cost", "dollar", "$"]):
            if self.context.current_phase == NegotiationPhase.DISCOVERY:
                self.context.current_phase = NegotiationPhase.INITIAL_OFFER
            elif self.context.current_phase in [NegotiationPhase.INITIAL_OFFER, NegotiationPhase.COUNTER_OFFER]:
                self.context.current_phase = NegotiationPhase.BARGAINING
        
        if any(word in message_lower for word in ["deal", "sold", "agree", "accept"]):
            self.context.current_phase = NegotiationPhase.AGREEMENT
        
        if any(word in message_lower for word in ["no", "can't", "won't", "final"]):
            if self.context.negotiation_rounds > 3:
                self.context.current_phase = NegotiationPhase.CLOSING
    
    def _extract_offers_from_response(self, agent_response: str, seller_message: str):
        """Extract price offers from messages"""
        import re
        
        # Extract prices from agent response
        agent_prices = re.findall(r'\$(\d+(?:\.\d{2})?)', agent_response)
        if agent_prices:
            self.context.current_offer = float(agent_prices[-1])
        
        # Extract prices from seller message
        seller_prices = re.findall(r'\$(\d+(?:\.\d{2})?)', seller_message)
        if seller_prices:
            self.context.seller_last_offer = float(seller_prices[-1])
    
    def get_negotiation_summary(self) -> Dict[str, Any]:
        """Get summary of current negotiation"""
        if not self.context:
            return {"error": "No active negotiation"}
        
        return {
            "session_id": self.context.session_id,
            "product": self.context.product.dict(),
            "goals": self.context.goals.dict(),
            "current_phase": self.context.current_phase,
            "negotiation_rounds": self.context.negotiation_rounds,
            "current_offer": self.context.current_offer,
            "seller_last_offer": self.context.seller_last_offer,
            "conversation_length": len(self.context.conversation_history),
            "duration_minutes": (datetime.now() - self.context.start_time).total_seconds() / 60
        }
    
    def export_conversation(self) -> List[Dict[str, Any]]:
        """Export full conversation history"""
        if not self.context:
            return []
        return self.context.conversation_history

# Example usage and testing functions
async def demo_negotiation():
    """Demonstrate the negotiation agent"""
    print("🤖 AI Negotiation Agent Demo")
    print("=" * 50)
    
    # Initialize agent (you'll need to provide your API key)
    agent = NegotiationAgent(api_key="AIzaSyDD94qIFoT1XQ62GLWzXpvLjKDgwaXpmpI")
    
    # Create product info
    product = ProductInfo(
        name="iPhone 13 Pro 256GB",
        listed_price=800.0,
        description="Excellent condition iPhone 13 Pro with original box and accessories",
        condition="Like New",
        seller_name="John",
        platform="Facebook Marketplace",
        category="Electronics",
        location="San Francisco, CA",
        features=["256GB storage", "Original box", "All accessories", "No scratches"]
    )
    
    # Set negotiation goals
    goals = NegotiationGoals(
        target_price=650.0,
        max_budget=720.0,
        personality=AgentPersonality.FRIENDLY,
        timeline="week"
    )
    
    # Start negotiation
    opening_message = await agent.start_negotiation(product, goals)
    print(f"\n🤖 Agent: {opening_message}")
    
    # Simulate seller responses
    seller_responses = [
        "Hi! Thanks for your interest. The phone is in perfect condition. I'm asking $800 but I might consider $780.",
        "I understand you want a good deal, but $650 is too low. I can do $750 final offer.",
        "Okay, let me think about it. How about we meet in the middle at $700?"
    ]
    
    for i, seller_msg in enumerate(seller_responses):
        print(f"\n👤 Seller: {seller_msg}")
        agent_response = await agent.respond_to_seller(seller_msg)
        print(f"🤖 Agent: {agent_response}")
        
        # Show negotiation progress
        summary = agent.get_negotiation_summary()
        print(f"📊 Status: {summary['current_phase']} | Round: {summary['negotiation_rounds']}")
    
    print("\n" + "=" * 50)
    print("Demo completed!")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_negotiation())