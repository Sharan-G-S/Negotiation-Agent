"""
Buyer Negotiation Agent - Represents the User as a Buyer
The agent negotiates with sellers on behalf of the user, finding best deals online
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import requests
from bs4 import BeautifulSoup
import random

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuyerPersonality(str, Enum):
    """Buyer negotiation personalities"""
    BUDGET_CONSCIOUS = "budget_conscious"    # Focuses on getting lowest price
    VALUE_SEEKER = "value_seeker"           # Wants best value for money
    TIME_SAVER = "time_saver"              # Quick decisions, fair prices
    QUALITY_FOCUSED = "quality_focused"     # Willing to pay for quality
    AGGRESSIVE_BARGAINER = "aggressive_bargainer"  # Pushes hard for discounts
    DIPLOMATIC_NEGOTIATOR = "diplomatic_negotiator"  # Polite but firm

class NegotiationPhase(str, Enum):
    """Phases of negotiation from buyer's perspective"""
    PRODUCT_INQUIRY = "product_inquiry"      # Initial product questions
    PRICE_DISCOVERY = "price_discovery"      # Finding out seller's price
    MARKET_COMPARISON = "market_comparison"  # Comparing with other sellers
    INITIAL_OFFER = "initial_offer"         # Making first offer
    COUNTER_NEGOTIATION = "counter_negotiation"  # Back and forth negotiation
    VALUE_JUSTIFICATION = "value_justification"  # Justifying price points
    FINAL_DECISION = "final_decision"       # Making final deal or walking away
    DEAL_CLOSURE = "deal_closure"           # Agreeing on terms

class OnlineSellerFinderTool(BaseTool):
    """Tool to find sellers online for a product"""
    name: str = "online_seller_finder"
    description: str = "Find top sellers online for a specific product with prices in INR"
    
    def _run(self, product_name: str) -> str:
        """Find sellers for the product"""
        # Mock data simulating online marketplace search
        # In real implementation, this would scrape Amazon, Flipkart, etc.
        
        sellers_data = {
            "iphone 13 pro": [
                {"seller": "TechMart Electronics", "price": 85000, "rating": 4.8, "location": "Mumbai"},
                {"seller": "Mobile World", "price": 82000, "rating": 4.6, "location": "Delhi"},
                {"seller": "Gadget Palace", "price": 87500, "rating": 4.7, "location": "Bangalore"},
                {"seller": "Electronics Hub", "price": 84000, "rating": 4.5, "location": "Chennai"},
                {"seller": "Digital Store", "price": 83500, "rating": 4.9, "location": "Pune"}
            ],
            "laptop": [
                {"seller": "Computer Zone", "price": 65000, "rating": 4.7, "location": "Hyderabad"},
                {"seller": "Tech Solutions", "price": 62000, "rating": 4.8, "location": "Kolkata"},
                {"seller": "IT World", "price": 67000, "rating": 4.6, "location": "Mumbai"},
            ],
            "default": [
                {"seller": "Best Electronics", "price": 15000, "rating": 4.5, "location": "Delhi"},
                {"seller": "Quality Goods", "price": 14500, "rating": 4.7, "location": "Mumbai"},
                {"seller": "Value Store", "price": 16000, "rating": 4.4, "location": "Bangalore"},
            ]
        }
        
        # Get sellers for product (case-insensitive search)
        product_key = next(
            (key for key in sellers_data.keys() if key in product_name.lower()), 
            "default"
        )
        
        sellers = sellers_data[product_key]
        
        # Format seller information
        result = f"Found {len(sellers)} sellers for '{product_name}':\n\n"
        for i, seller in enumerate(sellers, 1):
            result += f"{i}. {seller['seller']} - ₹{seller['price']:,}\n"
            result += f"   Rating: {seller['rating']}/5 | Location: {seller['location']}\n\n"
        
        # Add market analysis
        prices = [s['price'] for s in sellers]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        result += f"Market Analysis:\n"
        result += f"Average Price: ₹{avg_price:,.0f}\n"
        result += f"Lowest Price: ₹{min_price:,} | Highest: ₹{max_price:,}\n"
        result += f"Price Range: ₹{max_price - min_price:,}\n"
        
        return result

class PriceComparisonTool(BaseTool):
    """Tool to compare current offer with market prices"""
    name: str = "price_comparison"
    description: str = "Compare seller's price with market rates and suggest negotiation strategy"
    
    def _run(self, seller_price: str, target_price: str, product: str) -> str:
        """Compare prices and suggest strategy"""
        try:
            seller_price_num = float(re.sub(r'[^\d.]', '', seller_price))
            target_price_num = float(re.sub(r'[^\d.]', '', target_price))
        except:
            return "Unable to parse prices for comparison."
        
        # Calculate differences
        difference = seller_price_num - target_price_num
        percentage_diff = (difference / seller_price_num) * 100
        
        result = f"Price Comparison Analysis:\n\n"
        result += f"Seller's Price: ₹{seller_price_num:,.0f}\n"
        result += f"Your Target: ₹{target_price_num:,.0f}\n"
        result += f"Difference: ₹{difference:,.0f} ({percentage_diff:.1f}% above target)\n\n"
        
        # Negotiation strategy suggestions
        if percentage_diff > 20:
            result += "Strategy: AGGRESSIVE NEGOTIATION\n"
            result += "- Seller's price is significantly high\n"
            result += "- Use market comparison data\n"
            result += "- Consider walking away as leverage\n"
        elif percentage_diff > 10:
            result += "Strategy: FIRM NEGOTIATION\n"
            result += "- Price is moderately high\n"
            result += "- Present your research and budget\n"
            result += "- Seek middle ground\n"
        elif percentage_diff > 0:
            result += "Strategy: GENTLE NEGOTIATION\n"
            result += "- Price is close to target\n"
            result += "- Ask for small discount\n"
            result += "- Consider additional value\n"
        else:
            result += "Strategy: ACCEPT OR ASK FOR EXTRAS\n"
            result += "- Price is at or below target\n"
            result += "- Consider accepting\n"
            result += "- Or ask for warranties/extras\n"
        
        return result

class NegotiationTacticTool(BaseTool):
    """Tool to suggest specific negotiation tactics"""
    name: str = "negotiation_tactics"
    description: str = "Get specific negotiation tactics based on seller's response and context"
    
    def _run(self, seller_response: str, negotiation_context: str) -> str:
        """Suggest tactics based on seller's response"""
        response_lower = seller_response.lower()
        
        tactics = []
        
        # Analyze seller's response and suggest tactics
        if "firm" in response_lower or "final" in response_lower:
            tactics.extend([
                "🎯 WALKAWAY TACTIC: 'I understand it's your final price, but it's above my budget. Thank you for your time.'",
                "🔄 ALTERNATIVE SEARCH: 'Let me check other sellers and get back to you if I don't find better options.'",
                "💡 VALUE ADDITION: 'Can you include accessories/warranty at this price?'"
            ])
        
        if "expensive" in response_lower or "high" in response_lower:
            tactics.extend([
                "📊 MARKET DATA: Show price comparison with other sellers",
                "💰 BUDGET CONSTRAINT: Explain your genuine budget limitations",
                "🤝 BULK/LOYALTY: Offer to buy multiple items or become repeat customer"
            ])
        
        if "condition" in response_lower or "quality" in response_lower:
            tactics.extend([
                "🔍 INSPECTION: Ask for detailed photos/videos",
                "⚠️ RISK PRICING: Price adjustment for used/older items",
                "🛡️ WARRANTY: Request warranty/return policy"
            ])
        
        if "urgent" in response_lower or "quick" in response_lower:
            tactics.extend([
                "⏰ TIME PRESSURE: Use urgency to your advantage",
                "💸 QUICK DEAL: Offer slightly higher for immediate closure",
                "🎪 DECISION DEADLINE: Set your own decision timeline"
            ])
        
        if not tactics:
            # Default tactics based on negotiation phase
            tactics = [
                "🎯 ANCHORING: Start with your target price as reference point",
                "📈 INCREMENTAL: Make small incremental offers",
                "🤔 THINKING TIME: 'Let me think about it' to create pressure",
                "🔄 ALTERNATIVES: Mention you're considering other options"
            ]
        
        result = "🎪 Recommended Negotiation Tactics:\n\n"
        for i, tactic in enumerate(tactics[:4], 1):
            result += f"{i}. {tactic}\n\n"
        
        return result

class BuyerNegotiationAgent:
    """Main Buyer Negotiation Agent - Represents the User"""
    
    def __init__(self, api_key: str = "mock", personality: BuyerPersonality = BuyerPersonality.VALUE_SEEKER):
        """Initialize the buyer agent"""
        self.api_key = api_key
        self.personality = personality
        self.mock_mode = api_key == "mock" or not api_key
        
        # Initialize LLM
        if not self.mock_mode:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model="gemini-1.5-pro",
                temperature=0.7
            )
        
        # Initialize tools
        self.tools = [
            OnlineSellerFinderTool(),
            PriceComparisonTool(),
            NegotiationTacticTool()
        ]
        
        # Current negotiation state
        self.current_negotiation = {
            "product": "",
            "target_price": 0,
            "max_budget": 0,
            "current_seller": "",
            "seller_price": 0,
            "negotiation_history": [],
            "phase": NegotiationPhase.PRODUCT_INQUIRY,
            "round": 0
        }
        
        # Memory for conversation
        self.conversation_memory = []
    
    def start_negotiation(self, product: str, target_price: int, max_budget: int):
        """Start a new negotiation session"""
        self.current_negotiation = {
            "product": product,
            "target_price": target_price,
            "max_budget": max_budget,
            "current_seller": "",
            "seller_price": 0,
            "negotiation_history": [],
            "phase": NegotiationPhase.PRODUCT_INQUIRY,
            "round": 0
        }
        self.conversation_memory = []
        
        return f"🛒 Starting negotiation for: {product}\n💰 Target: ₹{target_price:,} | Max Budget: ₹{max_budget:,}\n👤 Personality: {self.personality.replace('_', ' ').title()}"
    
    def find_sellers(self):
        """Find online sellers for the product"""
        finder = OnlineSellerFinderTool()
        return finder._run(self.current_negotiation["product"])
    
    def get_buyer_response(self, seller_message: str, seller_name: str = "Seller") -> Dict[str, Any]:
        """Generate buyer's response to seller's message"""
        # Update current seller and round
        self.current_negotiation["current_seller"] = seller_name
        self.current_negotiation["round"] += 1
        
        # Add seller message to history
        self.conversation_memory.append({
            "role": "seller",
            "message": seller_message,
            "timestamp": datetime.now().isoformat(),
            "round": self.current_negotiation["round"]
        })
        
        # Analyze seller's message for price extraction
        price_match = re.search(r'₹?[\d,]+', seller_message)
        if price_match:
            try:
                price_str = re.sub(r'[^\d]', '', price_match.group())
                self.current_negotiation["seller_price"] = int(price_str)
            except:
                pass
        
        # Update negotiation phase
        self._update_phase(seller_message)
        
        # Generate response based on personality and context
        if self.mock_mode:
            response = self._generate_mock_response(seller_message)
        else:
            response = self._generate_ai_response(seller_message)
        
        # Get price comparison and tactics
        comparison = ""
        tactics = ""
        
        if self.current_negotiation["seller_price"] > 0:
            price_tool = PriceComparisonTool()
            comparison = price_tool._run(
                str(self.current_negotiation["seller_price"]),
                str(self.current_negotiation["target_price"]),
                self.current_negotiation["product"]
            )
        
        tactic_tool = NegotiationTacticTool()
        tactics = tactic_tool._run(seller_message, str(self.current_negotiation))
        
        # Add response to memory
        self.conversation_memory.append({
            "role": "buyer",
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "round": self.current_negotiation["round"]
        })
        
        return {
            "response": response,
            "analysis": {
                "phase": self.current_negotiation["phase"],
                "round": self.current_negotiation["round"],
                "seller_price": self.current_negotiation["seller_price"],
                "target_price": self.current_negotiation["target_price"],
                "price_difference": self.current_negotiation["seller_price"] - self.current_negotiation["target_price"] if self.current_negotiation["seller_price"] > 0 else 0
            },
            "price_comparison": comparison,
            "tactics": tactics,
            "negotiation_status": self._get_negotiation_status()
        }
    
    def _update_phase(self, seller_message: str):
        """Update negotiation phase based on seller message"""
        message_lower = seller_message.lower()
        
        if "price" in message_lower or "₹" in seller_message or "cost" in message_lower:
            if self.current_negotiation["phase"] == NegotiationPhase.PRODUCT_INQUIRY:
                self.current_negotiation["phase"] = NegotiationPhase.PRICE_DISCOVERY
            elif self.current_negotiation["phase"] == NegotiationPhase.PRICE_DISCOVERY:
                self.current_negotiation["phase"] = NegotiationPhase.INITIAL_OFFER
        
        if "offer" in message_lower or "deal" in message_lower:
            self.current_negotiation["phase"] = NegotiationPhase.COUNTER_NEGOTIATION
        
        if "final" in message_lower or "last" in message_lower:
            self.current_negotiation["phase"] = NegotiationPhase.FINAL_DECISION
        
        if "sold" in message_lower or "deal" in message_lower and "final" in message_lower:
            self.current_negotiation["phase"] = NegotiationPhase.DEAL_CLOSURE
    
    def _generate_mock_response(self, seller_message: str) -> str:
        """Generate mock response when no AI is available"""
        message_lower = seller_message.lower()
        target = self.current_negotiation["target_price"]
        
        responses_by_personality = {
            BuyerPersonality.BUDGET_CONSCIOUS: {
                "price_high": f"That's quite expensive for me. I was looking to spend around ₹{target:,}. Can you work with that budget?",
                "negotiation": f"I understand your position, but ₹{target:,} is really my maximum. Can we meet somewhere there?",
                "default": "I'm interested in the product, but I'm working with a tight budget. What's your best price?"
            },
            BuyerPersonality.AGGRESSIVE_BARGAINER: {
                "price_high": f"That's way too high! I can get this for ₹{target:,} elsewhere. Your best price?",
                "negotiation": f"Look, I'm ready to buy today for ₹{target:,}. Yes or no?",
                "default": "Cut to the chase - what's your rock bottom price? I'm a serious buyer."
            },
            BuyerPersonality.DIPLOMATIC_NEGOTIATOR: {
                "price_high": f"I appreciate the quote, but it's above my budget of ₹{target:,}. Could we find a middle ground?",
                "negotiation": f"I respect your pricing, but I was hoping for something closer to ₹{target:,}. What do you think?",
                "default": "Thank you for the information. I'm genuinely interested - could we discuss the pricing?"
            },
            BuyerPersonality.VALUE_SEEKER: {
                "price_high": f"That seems a bit high for the value. I was thinking around ₹{target:,} would be fair. What do you think?",
                "negotiation": f"I want to make sure I'm getting good value. Would ₹{target:,} work for you?",
                "default": "I'm looking for the best value. What's included at that price?"
            }
        }
        
        personality_responses = responses_by_personality.get(self.personality, responses_by_personality[BuyerPersonality.VALUE_SEEKER])
        
        if "price" in message_lower and any(char.isdigit() for char in seller_message):
            return personality_responses.get("price_high", personality_responses["default"])
        elif self.current_negotiation["round"] > 2:
            return personality_responses.get("negotiation", personality_responses["default"])
        else:
            return personality_responses["default"]
    
    def _generate_ai_response(self, seller_message: str) -> str:
        """Generate AI response (when API is available)"""
        # This would use the LLM to generate contextual responses
        # For now, fall back to mock response
        return self._generate_mock_response(seller_message)
    
    def _get_negotiation_status(self) -> str:
        """Get current negotiation status"""
        seller_price = self.current_negotiation["seller_price"]
        target_price = self.current_negotiation["target_price"]
        max_budget = self.current_negotiation["max_budget"]
        
        if seller_price == 0:
            return "🔍 Waiting for seller's price"
        elif seller_price <= target_price:
            return "✅ Seller's price is at/below target!"
        elif seller_price <= max_budget:
            return "⚡ Price negotiable within budget"
        else:
            return "⚠️ Price above maximum budget"
    
    def get_negotiation_summary(self) -> Dict[str, Any]:
        """Get complete negotiation summary"""
        return {
            "product": self.current_negotiation["product"],
            "target_price": self.current_negotiation["target_price"],
            "max_budget": self.current_negotiation["max_budget"],
            "seller_price": self.current_negotiation["seller_price"],
            "current_phase": self.current_negotiation["phase"],
            "total_rounds": self.current_negotiation["round"],
            "conversation_history": self.conversation_memory,
            "negotiation_status": self._get_negotiation_status(),
            "savings_potential": max(0, self.current_negotiation["seller_price"] - self.current_negotiation["target_price"]) if self.current_negotiation["seller_price"] > 0 else 0
        }

# Demo function
async def demo_buyer_agent():
    """Demonstrate the buyer agent"""
    print("🛒 Buyer Negotiation Agent Demo")
    print("=" * 50)
    
    # Initialize agent
    agent = BuyerNegotiationAgent(personality=BuyerPersonality.VALUE_SEEKER)
    
    # Start negotiation
    print(agent.start_negotiation("iPhone 13 Pro", 75000, 85000))
    print()
    
    # Find sellers
    print("🔍 Finding sellers online...")
    sellers = agent.find_sellers()
    print(sellers)
    
    # Simulate conversation with seller
    print("\n💬 Negotiation Conversation:")
    print("-" * 30)
    
    seller_messages = [
        "Hi! I have iPhone 13 Pro in excellent condition. Price is ₹85,000.",
        "This is already a good price for this model. Best I can do is ₹82,000.",
        "I can't go below ₹80,000. This is my final offer.",
        "Okay, ₹78,000 and we have a deal!"
    ]
    
    for i, seller_msg in enumerate(seller_messages, 1):
        print(f"\n📱 Seller: {seller_msg}")
        
        response_data = agent.get_buyer_response(seller_msg, "TechMart Electronics")
        
        print(f"🛒 Buyer: {response_data['response']}")
        print(f"📊 Status: {response_data['negotiation_status']}")
        
        if i == 2:  # Show analysis after a couple rounds
            print(f"\n📈 Price Analysis:")
            print(response_data['price_comparison'])
    
    # Final summary
    print("\n📋 Final Negotiation Summary:")
    summary = agent.get_negotiation_summary()
    print(f"Product: {summary['product']}")
    print(f"Final Price: ₹{summary['seller_price']:,}")
    print(f"Target: ₹{summary['target_price']:,}")
    print(f"Savings: ₹{summary['savings_potential']:,}")
    print(f"Total Rounds: {summary['total_rounds']}")
    print(f"Status: {summary['negotiation_status']}")

if __name__ == "__main__":
    asyncio.run(demo_buyer_agent())