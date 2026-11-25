"""
Interactive Chat Interface for AI Negotiation Agent
Provides real-time chat capabilities with WebSocket support
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import uuid

# WebSocket and Real-time Communication
class NegotiationChatInterface:
    """Real-time chat interface for negotiation sessions"""
    
    def __init__(self, agent, mcp_server, context_manager):
        self.agent = agent
        self.mcp_server = mcp_server
        self.context_manager = context_manager
        self.active_chats: Dict[str, Dict] = {}
        self.message_handlers: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    def add_message_handler(self, handler: Callable):
        """Add a message handler for real-time updates"""
        self.message_handlers.append(handler)
    
    async def start_chat_session(
        self,
        user_id: str,
        product_info: Dict,
        goals: Dict,
        chat_config: Dict = None
    ) -> str:
        """Start a new interactive chat session"""
        
        chat_id = f"chat_{uuid.uuid4().hex[:8]}"
        
        # Create negotiation context
        session_id = await self.context_manager.create_negotiation_context(
            product_info, goals
        )
        
        # Initialize chat session
        chat_session = {
            "chat_id": chat_id,
            "session_id": session_id,
            "user_id": user_id,
            "status": "active",
            "created_at": datetime.now(),
            "product_info": product_info,
            "goals": goals,
            "config": chat_config or {},
            "message_queue": [],
            "typing_status": {"agent": False, "seller": False}
        }
        
        self.active_chats[chat_id] = chat_session
        
        # Start the agent for this session
        await self.agent.start_negotiation(
            product=self._dict_to_product(product_info),
            goals=self._dict_to_goals(goals),
            session_id=session_id
        )
        
        # Get initial agent message
        opening_message = await self.agent.context.conversation_history[0]["message"]
        
        # Send opening message
        await self._send_message(chat_id, {
            "sender": "agent",
            "content": opening_message,
            "message_type": "opening",
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"Started chat session {chat_id} for user {user_id}")
        return chat_id
    
    async def send_seller_message(self, chat_id: str, message: str, sender_info: Dict = None) -> Dict:
        """Process incoming message from seller"""
        
        if chat_id not in self.active_chats:
            return {"error": "Chat session not found"}
        
        chat_session = self.active_chats[chat_id]
        
        try:
            # Add seller message to chat
            seller_msg = {
                "sender": "seller",
                "content": message,
                "message_type": "response",
                "timestamp": datetime.now().isoformat(),
                "sender_info": sender_info or {}
            }
            
            await self._send_message(chat_id, seller_msg)
            
            # Show agent typing
            await self._set_typing_status(chat_id, "agent", True)
            
            # Get agent response
            agent_response = await self.agent.respond_to_seller(message)
            
            # Stop agent typing
            await self._set_typing_status(chat_id, "agent", False)
            
            # Send agent response
            agent_msg = {
                "sender": "agent",
                "content": agent_response,
                "message_type": "response",
                "timestamp": datetime.now().isoformat(),
                "negotiation_data": await self._get_negotiation_context(chat_session["session_id"])
            }
            
            await self._send_message(chat_id, agent_msg)
            
            return {
                "success": True,
                "agent_response": agent_response,
                "chat_status": chat_session["status"],
                "negotiation_summary": await self._get_negotiation_summary(chat_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing seller message: {e}")
            return {"error": str(e)}
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a session"""
        
        if chat_id not in self.active_chats:
            return []
        
        chat_session = self.active_chats[chat_id]
        session_id = chat_session["session_id"]
        
        # Get messages from MCP server
        messages = await self.mcp_server.get_conversation_history(session_id, limit)
        
        return messages
    
    async def get_negotiation_insights(self, chat_id: str) -> Dict:
        """Get real-time negotiation insights"""
        
        if chat_id not in self.active_chats:
            return {}
        
        chat_session = self.active_chats[chat_id]
        session_id = chat_session["session_id"]
        
        # Get current negotiation status
        context = await self.context_manager.get_context_summary(session_id)
        analytics = await self.mcp_server.get_session_analytics(session_id)
        
        return {
            "current_phase": context.get("current_phase", "unknown"),
            "progress_percentage": self._calculate_progress(context, analytics),
            "recommended_action": context.get("next_recommended_action", ""),
            "price_analysis": {
                "target": chat_session["goals"]["target_price"],
                "current_offer": analytics.get("price_progression", [])[-1:] if analytics.get("price_progression") else None,
                "savings_potential": self._calculate_savings(chat_session, analytics)
            },
            "negotiation_health": self._assess_negotiation_health(analytics),
            "tactics_effectiveness": self._analyze_tactics_effectiveness(analytics)
        }
    
    async def simulate_seller_response(self, chat_id: str, seller_personality: str = "moderate") -> str:
        """Simulate a seller response for testing purposes"""
        
        if chat_id not in self.active_chats:
            return "Chat not found"
        
        chat_session = self.active_chats[chat_id]
        
        # Get conversation context
        history = await self.get_chat_history(chat_id, 5)
        last_agent_message = next((msg["content"] for msg in reversed(history) if msg["sender"] == "agent"), "")
        
        # Generate seller response based on personality
        seller_responses = {
            "flexible": [
                "That's an interesting offer. Let me think about it.",
                "I appreciate your offer. Can we meet somewhere in the middle?",
                "I'm willing to negotiate. What's your best offer?"
            ],
            "firm": [
                "I'm sorry, but my price is firm.",
                "I can't go that low. The price reflects the quality.",
                "I've already priced this fairly for the market."
            ],
            "eager": [
                "That works for me! When can you pick it up?",
                "Sure, I need to sell this quickly. Your offer is fine.",
                "Great! I'm ready to make a deal."
            ],
            "moderate": [
                "I understand you're looking for a good deal. Let me consider your offer.",
                "The item is worth more, but I'm open to reasonable offers.",
                "How about we compromise? I can do a bit better than my listed price."
            ]
        }
        
        responses = seller_responses.get(seller_personality, seller_responses["moderate"])
        import random
        return random.choice(responses)
    
    async def end_chat_session(self, chat_id: str, outcome: str = "completed") -> Dict:
        """End a chat session"""
        
        if chat_id not in self.active_chats:
            return {"error": "Chat session not found"}
        
        chat_session = self.active_chats[chat_id]
        session_id = chat_session["session_id"]
        
        try:
            # Close MCP session
            await self.mcp_server.close_session(session_id, outcome)
            
            # Update chat session
            chat_session["status"] = "closed"
            chat_session["ended_at"] = datetime.now()
            chat_session["outcome"] = outcome
            
            # Get final analytics
            final_analytics = await self.mcp_server.get_session_analytics(session_id)
            
            # Remove from active chats
            del self.active_chats[chat_id]
            
            return {
                "success": True,
                "outcome": outcome,
                "analytics": final_analytics,
                "session_summary": self._generate_session_summary(chat_session, final_analytics)
            }
            
        except Exception as e:
            self.logger.error(f"Error ending chat session: {e}")
            return {"error": str(e)}
    
    async def _send_message(self, chat_id: str, message: Dict):
        """Send message and notify handlers"""
        
        # Add to MCP server
        chat_session = self.active_chats[chat_id]
        await self.mcp_server.add_message(chat_session["session_id"], message)
        
        # Add to local queue
        chat_session["message_queue"].append(message)
        
        # Notify handlers
        for handler in self.message_handlers:
            try:
                await handler(chat_id, message)
            except Exception as e:
                self.logger.error(f"Message handler error: {e}")
    
    async def _set_typing_status(self, chat_id: str, sender: str, is_typing: bool):
        """Set typing status and notify handlers"""
        
        if chat_id in self.active_chats:
            self.active_chats[chat_id]["typing_status"][sender] = is_typing
            
            # Notify typing status
            for handler in self.message_handlers:
                try:
                    await handler(chat_id, {
                        "type": "typing_status",
                        "sender": sender,
                        "is_typing": is_typing
                    })
                except Exception:
                    pass
    
    async def _get_negotiation_context(self, session_id: str) -> Dict:
        """Get current negotiation context"""
        return await self.context_manager.get_context_summary(session_id)
    
    async def _get_negotiation_summary(self, chat_id: str) -> Dict:
        """Get negotiation summary for UI"""
        
        chat_session = self.active_chats[chat_id]
        context = await self._get_negotiation_context(chat_session["session_id"])
        
        return {
            "phase": context.get("current_phase", "unknown"),
            "rounds": context.get("rounds_completed", 0),
            "target_price": chat_session["goals"]["target_price"],
            "progress": f"{context.get('rounds_completed', 0)}/10 rounds"
        }
    
    def _dict_to_product(self, product_dict: Dict):
        """Convert dictionary to Product object"""
        # This would use the ProductInfo model from agent.py
        from new_agent.core.agent import ProductInfo
        return ProductInfo(**product_dict)
    
    def _dict_to_goals(self, goals_dict: Dict):
        """Convert dictionary to Goals object"""
        from new_agent.core.agent import NegotiationGoals
        return NegotiationGoals(**goals_dict)
    
    def _calculate_progress(self, context: Dict, analytics: Dict) -> int:
        """Calculate negotiation progress percentage"""
        rounds = context.get("rounds_completed", 0)
        phase = context.get("current_phase", "greeting")
        
        phase_weights = {
            "greeting": 10,
            "discovery": 25,
            "initial_offer": 40,
            "bargaining": 70,
            "closing": 90,
            "agreement": 100
        }
        
        base_progress = phase_weights.get(phase, 0)
        round_bonus = min(rounds * 5, 30)  # Up to 30% bonus from rounds
        
        return min(base_progress + round_bonus, 100)
    
    def _calculate_savings(self, chat_session: Dict, analytics: Dict) -> Dict:
        """Calculate potential savings"""
        listed_price = chat_session["product_info"]["listed_price"]
        target_price = chat_session["goals"]["target_price"]
        
        potential_savings = listed_price - target_price
        percentage_savings = (potential_savings / listed_price) * 100
        
        return {
            "potential_amount": potential_savings,
            "potential_percentage": round(percentage_savings, 1),
            "target_vs_listed": f"${target_price} vs ${listed_price}"
        }
    
    def _assess_negotiation_health(self, analytics: Dict) -> str:
        """Assess overall negotiation health"""
        rounds = analytics.get("negotiation_rounds", 0)
        duration = analytics.get("duration_minutes", 0)
        
        if rounds > 8 or duration > 60:
            return "stalled"
        elif rounds < 3:
            return "early"
        else:
            return "healthy"
    
    def _analyze_tactics_effectiveness(self, analytics: Dict) -> List[Dict]:
        """Analyze effectiveness of used tactics"""
        # Mock implementation - in real version would analyze conversation
        return [
            {"tactic": "anchoring", "effectiveness": 0.8, "usage_count": 2},
            {"tactic": "compromise", "effectiveness": 0.6, "usage_count": 1}
        ]
    
    def _generate_session_summary(self, chat_session: Dict, analytics: Dict) -> Dict:
        """Generate comprehensive session summary"""
        return {
            "duration_minutes": analytics.get("duration_minutes", 0),
            "total_messages": analytics.get("message_count", 0),
            "final_outcome": chat_session.get("outcome", "unknown"),
            "price_progression": analytics.get("price_progression", []),
            "tactics_used": analytics.get("tactics_used", []),
            "success_metrics": {
                "target_achieved": False,  # Would calculate based on final price
                "time_efficiency": "good",
                "communication_quality": "professional"
            }
        }

# Console-based Interactive Chat for Testing
class ConsoleChatInterface:
    """Console-based interface for testing the chat functionality"""
    
    def __init__(self, chat_interface: NegotiationChatInterface):
        self.chat_interface = chat_interface
        self.current_chat_id = None
    
    async def start_interactive_session(self):
        """Start an interactive console session"""
        print("🤖 AI Negotiation Agent - Interactive Chat")
        print("=" * 60)
        
        # Get product information
        product_info = await self._get_product_info()
        goals = await self._get_negotiation_goals()
        
        # Start chat session
        self.current_chat_id = await self.chat_interface.start_chat_session(
            user_id="test_user",
            product_info=product_info,
            goals=goals
        )
        
        print(f"\n✅ Started negotiation session: {self.current_chat_id}")
        print("\n🎯 Negotiation Goals:")
        print(f"   Target Price: ${goals['target_price']}")
        print(f"   Max Budget: ${goals['max_budget']}")
        print(f"   Timeline: {goals.get('timeline', 'flexible')}")
        
        # Get initial agent message
        history = await self.chat_interface.get_chat_history(self.current_chat_id, 1)
        if history:
            print(f"\n🤖 Agent: {history[0]['content']}")
        
        # Start interactive loop
        await self._interactive_loop()
    
    async def _get_product_info(self) -> Dict:
        """Get product information from user"""
        print("\n📱 Enter Product Information:")
        
        name = input("Product Name: ").strip() or "iPhone 13 Pro 256GB"
        listed_price = float(input("Listed Price ($): ").strip() or "800")
        condition = input("Condition (new/like-new/good/fair): ").strip() or "like-new"
        seller_name = input("Seller Name: ").strip() or "John"
        platform = input("Platform (olx/facebook/other): ").strip() or "facebook"
        location = input("Location: ").strip() or "San Francisco, CA"
        
        return {
            "name": name,
            "listed_price": listed_price,
            "condition": condition,
            "seller_name": seller_name,
            "platform": platform,
            "location": location,
            "description": f"{condition} {name} for sale",
            "category": "Electronics",
            "features": ["Original box", "All accessories"]
        }
    
    async def _get_negotiation_goals(self) -> Dict:
        """Get negotiation goals from user"""
        print("\n🎯 Enter Negotiation Goals:")
        
        target_price = float(input("Target Price ($): ").strip() or "650")
        max_budget = float(input("Maximum Budget ($): ").strip() or "720")
        timeline = input("Timeline (urgent/week/month/flexible): ").strip() or "flexible"
        personality = input("Agent Personality (friendly/assertive/diplomatic): ").strip() or "friendly"
        
        return {
            "target_price": target_price,
            "max_budget": max_budget,
            "timeline": timeline,
            "personality": personality,
            "must_have_features": [],
            "deal_breakers": []
        }
    
    async def _interactive_loop(self):
        """Main interactive chat loop"""
        print("\n" + "=" * 60)
        print("💬 Chat Started - Type your messages as the seller")
        print("Commands: /insights, /history, /simulate, /end, /help")
        print("=" * 60)
        
        while True:
            try:
                # Get seller message
                seller_input = input("\n👤 Seller: ").strip()
                
                if not seller_input:
                    continue
                
                # Handle commands
                if seller_input.startswith('/'):
                    await self._handle_command(seller_input)
                    continue
                
                # Process seller message
                print("🤖 Agent is typing...")
                result = await self.chat_interface.send_seller_message(
                    self.current_chat_id, 
                    seller_input
                )
                
                if result.get("error"):
                    print(f"❌ Error: {result['error']}")
                    continue
                
                print(f"🤖 Agent: {result['agent_response']}")
                
                # Show negotiation status
                summary = result.get("negotiation_summary", {})
                if summary:
                    print(f"📊 Status: {summary.get('phase', 'unknown').title()} | Round {summary.get('rounds', 0)}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Ending negotiation session...")
                await self._end_session()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _handle_command(self, command: str):
        """Handle chat commands"""
        cmd = command.lower().split()[0]
        
        if cmd == "/help":
            print("""
📋 Available Commands:
/insights  - Show negotiation insights
/history   - Show chat history
/simulate  - Simulate seller response
/end       - End negotiation session
/help      - Show this help
""")
        
        elif cmd == "/insights":
            insights = await self.chat_interface.get_negotiation_insights(self.current_chat_id)
            print("\n📊 Negotiation Insights:")
            print(f"   Phase: {insights.get('current_phase', 'unknown').title()}")
            print(f"   Progress: {insights.get('progress_percentage', 0)}%")
            print(f"   Recommended: {insights.get('recommended_action', 'Continue')}")
            
            price_analysis = insights.get('price_analysis', {})
            if price_analysis:
                print(f"   Target: ${price_analysis.get('target', 0)}")
                savings = price_analysis.get('savings_potential', {})
                if savings:
                    print(f"   Potential Savings: ${savings.get('potential_amount', 0)} ({savings.get('potential_percentage', 0)}%)")
        
        elif cmd == "/history":
            history = await self.chat_interface.get_chat_history(self.current_chat_id, 10)
            print("\n📜 Chat History (last 10 messages):")
            for msg in history[-5:]:  # Show last 5 for brevity
                sender_icon = "🤖" if msg["sender"] == "agent" else "👤"
                print(f"   {sender_icon} {msg['sender'].title()}: {msg['content']}")
        
        elif cmd == "/simulate":
            personality = input("Seller personality (flexible/firm/eager/moderate): ").strip() or "moderate"
            response = await self.chat_interface.simulate_seller_response(self.current_chat_id, personality)
            print(f"\n🎭 Simulated Seller ({personality}): {response}")
        
        elif cmd == "/end":
            await self._end_session()
        
        else:
            print(f"❌ Unknown command: {command}")
    
    async def _end_session(self):
        """End the negotiation session"""
        if self.current_chat_id:
            result = await self.chat_interface.end_chat_session(self.current_chat_id, "user_ended")
            
            if result.get("success"):
                print("✅ Negotiation session ended successfully")
                
                analytics = result.get("analytics", {})
                if analytics:
                    print(f"📊 Final Analytics:")
                    print(f"   Duration: {analytics.get('duration_minutes', 0):.1f} minutes")
                    print(f"   Messages: {analytics.get('message_count', 0)}")
                    print(f"   Outcome: {result.get('outcome', 'unknown').title()}")
            else:
                print(f"❌ Error ending session: {result.get('error', 'unknown')}")

# Example usage and demo
async def demo_interactive_chat():
    """Demo the interactive chat interface"""
    from new_agent.core.agent import NegotiationAgent
    from new_agent.mcp.server import NegotiationMCPServer, NegotiationContextManager
    
    # Initialize components
    print("🚀 Initializing AI Negotiation System...")
    
    # Note: You'll need to provide your actual API key
    agent = NegotiationAgent(api_key="your-gemini-api-key")
    mcp_server = NegotiationMCPServer()
    context_manager = NegotiationContextManager(mcp_server)
    
    # Create chat interface
    chat_interface = NegotiationChatInterface(agent, mcp_server, context_manager)
    
    # Create console interface
    console = ConsoleChatInterface(chat_interface)
    
    # Start interactive session
    await console.start_interactive_session()

if __name__ == "__main__":
    asyncio.run(demo_interactive_chat())