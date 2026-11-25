"""
AI Negotiation Agent - Complete Integration
Brings together all components into a unified system
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import all our custom modules
from core.agent import NegotiationAgent, ProductInfo, NegotiationGoals
from mcp.server import NegotiationMCPServer, NegotiationContextManager  
from interface.chat import NegotiationChatInterface, ConsoleChatInterface
from intelligence.strategy import NegotiationIntelligenceEngine, NegotiationPhase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedNegotiationSystem:
    """Complete AI Negotiation System Integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the integrated negotiation system"""
        
        self.config = config or {}
        
        # Initialize core components
        self.agent = None
        self.mcp_server = None
        self.context_manager = None
        self.chat_interface = None
        self.intelligence_engine = None
        
        # System status
        self.is_initialized = False
        self.active_sessions = {}
        
        logger.info("Integrated Negotiation System created")
    
    async def initialize(self, gemini_api_key: str, storage_path: str = "./negotiation_data"):
        """Initialize all system components"""
        
        try:
            logger.info("Initializing AI Negotiation System components...")
            
            # Initialize core agent
            self.agent = NegotiationAgent(api_key=gemini_api_key)
            logger.info("✅ Core negotiation agent initialized")
            
            # Initialize MCP server
            self.mcp_server = NegotiationMCPServer(storage_path)
            logger.info("✅ MCP server initialized")
            
            # Initialize context manager
            self.context_manager = NegotiationContextManager(self.mcp_server)
            logger.info("✅ Context manager initialized")
            
            # Initialize chat interface
            self.chat_interface = NegotiationChatInterface(
                self.agent, self.mcp_server, self.context_manager
            )
            logger.info("✅ Chat interface initialized")
            
            # Initialize intelligence engine
            self.intelligence_engine = NegotiationIntelligenceEngine()
            logger.info("✅ Intelligence engine initialized")
            
            self.is_initialized = True
            logger.info("🚀 System initialization complete!")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def start_negotiation(
        self,
        user_id: str,
        product_info: Dict,
        negotiation_goals: Dict,
        session_config: Dict = None
    ) -> str:
        """Start a new negotiation session"""
        
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        try:
            # Start chat session
            chat_id = await self.chat_interface.start_chat_session(
                user_id=user_id,
                product_info=product_info,
                goals=negotiation_goals,
                chat_config=session_config
            )
            
            # Track active session
            self.active_sessions[chat_id] = {
                "user_id": user_id,
                "started_at": datetime.now(),
                "status": "active"
            }
            
            logger.info(f"Started negotiation session {chat_id} for user {user_id}")
            return chat_id
            
        except Exception as e:
            logger.error(f"Error starting negotiation: {e}")
            raise
    
    async def process_seller_message(
        self,
        chat_id: str,
        seller_message: str,
        seller_info: Dict = None
    ) -> Dict[str, Any]:
        """Process a message from the seller"""
        
        if not self.is_initialized:
            raise RuntimeError("System not initialized")
        
        if chat_id not in self.active_sessions:
            raise ValueError(f"Chat session {chat_id} not found")
        
        try:
            # Process message through chat interface
            result = await self.chat_interface.send_seller_message(
                chat_id, seller_message, seller_info
            )
            
            # Get enhanced insights using intelligence engine
            insights = await self.get_negotiation_insights(chat_id)
            
            # Combine results
            enhanced_result = {
                **result,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error processing seller message: {e}")
            return {"error": str(e)}
    
    async def get_negotiation_insights(self, chat_id: str) -> Dict[str, Any]:
        """Get comprehensive negotiation insights"""
        
        if not self.is_initialized:
            return {}
        
        try:
            # Get basic insights from chat interface
            basic_insights = await self.chat_interface.get_negotiation_insights(chat_id)
            
            # Get conversation history
            history = await self.chat_interface.get_chat_history(chat_id, 20)
            
            # Extract seller messages for analysis
            seller_messages = [
                msg["content"] for msg in history 
                if msg.get("sender") == "seller"
            ]
            
            if seller_messages:
                # Analyze seller using intelligence engine
                seller_analysis = await self.intelligence_engine.analyze_seller(
                    history, seller_messages
                )
                
                # Get market intelligence
                chat_session = self.chat_interface.active_chats.get(chat_id, {})
                product_info = chat_session.get("product_info", {})
                
                market_intel = await self.intelligence_engine.generate_market_intelligence(
                    product_info
                )
                
                # Get tactic recommendations
                negotiation_context = chat_session.get("goals", {})
                current_phase = NegotiationPhase.ACTIVE_NEGOTIATION  # Would determine from context
                
                tactic_recommendations = await self.intelligence_engine.recommend_tactics(
                    seller_analysis, market_intel, negotiation_context, current_phase
                )
                
                # Enhanced insights
                enhanced_insights = {
                    **basic_insights,
                    "seller_analysis": {
                        "personality": seller_analysis.personality_type.value,
                        "flexibility": seller_analysis.flexibility_score,
                        "urgency": seller_analysis.urgency_level,
                        "motivations": seller_analysis.motivations
                    },
                    "market_intelligence": {
                        "average_price": market_intel.average_market_price,
                        "price_trend": market_intel.price_trend,
                        "market_saturation": market_intel.market_saturation
                    },
                    "recommended_tactics": [
                        {
                            "tactic": tactic.value,
                            "confidence": confidence,
                            "rationale": rationale
                        }
                        for tactic, confidence, rationale in tactic_recommendations[:3]
                    ]
                }
                
                return enhanced_insights
            
            return basic_insights
            
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return basic_insights if 'basic_insights' in locals() else {}
    
    async def get_session_analytics(self, chat_id: str) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        
        if not self.is_initialized:
            return {}
        
        try:
            # Get basic session info
            chat_session = self.chat_interface.active_chats.get(chat_id, {})
            session_id = chat_session.get("session_id")
            
            if not session_id:
                return {"error": "Session not found"}
            
            # Get MCP analytics
            mcp_analytics = await self.mcp_server.get_session_analytics(session_id)
            
            # Calculate negotiation performance
            goals = chat_session.get("goals", {})
            product_info = chat_session.get("product_info", {})
            
            initial_price = product_info.get("listed_price", 0)
            target_price = goals.get("target_price", 0)
            max_budget = goals.get("max_budget", 0)
            
            # Get current best offer (would need to parse from conversation)
            current_offer = initial_price  # Simplified - would extract from conversation
            
            performance_score = self.intelligence_engine.calculate_negotiation_score(
                initial_price, current_offer, target_price, max_budget
            )
            
            return {
                **mcp_analytics,
                "performance": performance_score,
                "session_info": {
                    "chat_id": chat_id,
                    "user_id": self.active_sessions.get(chat_id, {}).get("user_id"),
                    "started_at": self.active_sessions.get(chat_id, {}).get("started_at")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}
    
    async def end_negotiation(self, chat_id: str, outcome: str = "completed") -> Dict[str, Any]:
        """End a negotiation session"""
        
        if not self.is_initialized:
            return {"error": "System not initialized"}
        
        try:
            # End chat session
            result = await self.chat_interface.end_chat_session(chat_id, outcome)
            
            # Remove from active sessions
            if chat_id in self.active_sessions:
                del self.active_sessions[chat_id]
            
            logger.info(f"Ended negotiation session {chat_id} with outcome: {outcome}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending negotiation: {e}")
            return {"error": str(e)}
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active negotiation sessions"""
        
        if not self.is_initialized:
            return []
        
        try:
            # Get MCP active sessions
            mcp_sessions = await self.mcp_server.list_active_sessions()
            
            # Combine with local session data
            combined_sessions = []
            for session in mcp_sessions:
                session_id = session["id"]
                
                # Find corresponding chat session
                chat_id = None
                for cid, chat_data in self.chat_interface.active_chats.items():
                    if chat_data.get("session_id") == session_id:
                        chat_id = cid
                        break
                
                combined_session = {
                    **session,
                    "chat_id": chat_id,
                    "local_status": self.active_sessions.get(chat_id, {}).get("status", "unknown")
                }
                combined_sessions.append(combined_session)
            
            return combined_sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def get_global_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics"""
        
        if not self.is_initialized:
            return {}
        
        try:
            # Get MCP global analytics
            mcp_analytics = await self.mcp_server.get_global_analytics()
            
            # Add system-specific metrics
            system_analytics = {
                **mcp_analytics,
                "system_status": {
                    "initialized": self.is_initialized,
                    "active_sessions": len(self.active_sessions),
                    "components_status": {
                        "agent": self.agent is not None,
                        "mcp_server": self.mcp_server is not None,
                        "chat_interface": self.chat_interface is not None,
                        "intelligence_engine": self.intelligence_engine is not None
                    }
                }
            }
            
            return system_analytics
            
        except Exception as e:
            logger.error(f"Error getting global analytics: {e}")
            return {"error": str(e)}

# CLI Interface for the Complete System
class NegotiationSystemCLI:
    """Command-line interface for the negotiation system"""
    
    def __init__(self):
        self.system = IntegratedNegotiationSystem()
        self.current_session = None
    
    async def run(self):
        """Run the CLI interface"""
        
        print("🤖 AI Negotiation Agent - Complete System")
        print("=" * 60)
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            api_key = input("Enter your Gemini API key: ").strip()
            if not api_key:
                print("❌ API key required. Exiting...")
                return
        
        try:
            # Initialize system
            print("\n🚀 Initializing system...")
            await self.system.initialize(api_key)
            
            # Main menu loop
            await self._main_menu()
            
        except Exception as e:
            print(f"❌ System error: {e}")
    
    async def _main_menu(self):
        """Main menu loop"""
        
        while True:
            print("\n" + "=" * 60)
            print("🎯 MAIN MENU")
            print("1. Start New Negotiation")
            print("2. Continue Existing Session")
            print("3. View Session Analytics")
            print("4. List Active Sessions")
            print("5. Global Analytics")
            print("6. Demo Mode")
            print("0. Exit")
            print("=" * 60)
            
            choice = input("Select option: ").strip()
            
            if choice == "1":
                await self._start_new_negotiation()
            elif choice == "2":
                await self._continue_session()
            elif choice == "3":
                await self._view_analytics()
            elif choice == "4":
                await self._list_sessions()
            elif choice == "5":
                await self._global_analytics()
            elif choice == "6":
                await self._demo_mode()
            elif choice == "0":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
    
    async def _start_new_negotiation(self):
        """Start a new negotiation session"""
        
        print("\n📱 NEW NEGOTIATION SETUP")
        print("-" * 30)
        
        # Get product info
        product_name = input("Product name: ").strip() or "iPhone 13 Pro"
        listed_price = float(input("Listed price ($): ").strip() or "800")
        condition = input("Condition: ").strip() or "like-new"
        seller_name = input("Seller name: ").strip() or "John"
        
        product_info = {
            "name": product_name,
            "listed_price": listed_price,
            "condition": condition,
            "seller_name": seller_name,
            "platform": "facebook",
            "description": f"{condition} {product_name}",
            "category": "Electronics"
        }
        
        # Get negotiation goals
        target_price = float(input("Target price ($): ").strip() or "650")
        max_budget = float(input("Max budget ($): ").strip() or "720")
        
        goals = {
            "target_price": target_price,
            "max_budget": max_budget,
            "personality": "friendly",
            "timeline": "flexible"
        }
        
        try:
            # Start negotiation
            chat_id = await self.system.start_negotiation(
                user_id="cli_user",
                product_info=product_info,
                negotiation_goals=goals
            )
            
            self.current_session = chat_id
            print(f"\n✅ Started negotiation session: {chat_id}")
            
            # Start interactive chat
            await self._interactive_chat(chat_id)
            
        except Exception as e:
            print(f"❌ Error starting negotiation: {e}")
    
    async def _interactive_chat(self, chat_id: str):
        """Interactive chat for a session"""
        
        print(f"\n💬 INTERACTIVE CHAT - Session: {chat_id}")
        print("-" * 50)
        print("Commands: /insights, /analytics, /end, /help")
        
        # Get initial message
        history = await self.system.chat_interface.get_chat_history(chat_id, 1)
        if history:
            print(f"\n🤖 Agent: {history[0]['content']}")
        
        while True:
            seller_input = input("\n👤 Seller: ").strip()
            
            if not seller_input:
                continue
            
            if seller_input.startswith('/'):
                if await self._handle_chat_command(seller_input, chat_id):
                    break
                continue
            
            # Process seller message
            print("🤖 Agent is thinking...")
            
            try:
                result = await self.system.process_seller_message(chat_id, seller_input)
                
                if result.get("error"):
                    print(f"❌ Error: {result['error']}")
                    continue
                
                print(f"🤖 Agent: {result['agent_response']}")
                
                # Show quick insights
                insights = result.get("insights", {})
                if insights:
                    phase = insights.get("current_phase", "unknown")
                    progress = insights.get("progress_percentage", 0)
                    print(f"📊 Status: {phase.title()} | Progress: {progress}%")
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _handle_chat_command(self, command: str, chat_id: str) -> bool:
        """Handle chat commands. Returns True if should exit chat."""
        
        cmd = command.lower().split()[0]
        
        if cmd == "/help":
            print("""
📋 Chat Commands:
/insights  - Show negotiation insights
/analytics - Show session analytics  
/end       - End negotiation
/help      - Show this help
""")
        
        elif cmd == "/insights":
            insights = await self.system.get_negotiation_insights(chat_id)
            print("\n📊 NEGOTIATION INSIGHTS:")
            print(json.dumps(insights, indent=2, default=str))
        
        elif cmd == "/analytics":
            analytics = await self.system.get_session_analytics(chat_id)
            print("\n📈 SESSION ANALYTICS:")
            print(json.dumps(analytics, indent=2, default=str))
        
        elif cmd == "/end":
            result = await self.system.end_negotiation(chat_id, "user_ended")
            if result.get("success"):
                print("✅ Negotiation ended successfully")
                return True
            else:
                print(f"❌ Error ending negotiation: {result.get('error')}")
        
        return False
    
    async def _continue_session(self):
        """Continue an existing session"""
        sessions = await self.system.list_active_sessions()
        
        if not sessions:
            print("No active sessions found")
            return
        
        print("\n📋 ACTIVE SESSIONS:")
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session.get('chat_id', 'Unknown')} - {session.get('created_at', 'Unknown')}")
        
        try:
            choice = int(input("Select session number: ")) - 1
            if 0 <= choice < len(sessions):
                chat_id = sessions[choice].get('chat_id')
                if chat_id:
                    await self._interactive_chat(chat_id)
                else:
                    print("❌ Invalid session")
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Invalid input")
    
    async def _view_analytics(self):
        """View session analytics"""
        if self.current_session:
            analytics = await self.system.get_session_analytics(self.current_session)
            print("\n📊 SESSION ANALYTICS:")
            print(json.dumps(analytics, indent=2, default=str))
        else:
            print("No current session")
    
    async def _list_sessions(self):
        """List all active sessions"""
        sessions = await self.system.list_active_sessions()
        print(f"\n📋 ACTIVE SESSIONS ({len(sessions)}):")
        
        for session in sessions:
            print(f"- {session.get('chat_id', 'Unknown')}: {session.get('status', 'Unknown')}")
    
    async def _global_analytics(self):
        """Show global analytics"""
        analytics = await self.system.get_global_analytics()
        print("\n🌐 GLOBAL ANALYTICS:")
        print(json.dumps(analytics, indent=2, default=str))
    
    async def _demo_mode(self):
        """Run in demo mode with simulated seller"""
        print("\n🎭 DEMO MODE")
        print("Running with simulated seller responses...")
        
        # Pre-configured demo session
        product_info = {
            "name": "MacBook Pro 2021",
            "listed_price": 1200.0,
            "condition": "excellent",
            "seller_name": "Sarah",
            "platform": "facebook",
            "description": "MacBook Pro 2021 in excellent condition",
            "category": "Electronics"
        }
        
        goals = {
            "target_price": 1000.0,
            "max_budget": 1100.0,
            "personality": "friendly",
            "timeline": "week"
        }
        
        try:
            chat_id = await self.system.start_negotiation("demo_user", product_info, goals)
            
            # Simulate seller responses
            simulated_responses = [
                "Hi! Thanks for your interest. The MacBook is in excellent condition.",
                "I'm asking $1200, but I might consider $1150 for a quick sale.",
                "How about we meet at $1100? That's my final offer."
            ]
            
            for response in simulated_responses:
                print(f"\n👤 Seller (simulated): {response}")
                
                result = await self.system.process_seller_message(chat_id, response)
                print(f"🤖 Agent: {result.get('agent_response', 'Error')}")
                
                # Show insights
                insights = result.get("insights", {})
                if insights.get("recommended_tactics"):
                    top_tactic = insights["recommended_tactics"][0]
                    print(f"💡 Recommended: {top_tactic['tactic']} ({top_tactic['confidence']:.1%})")
                
                input("Press Enter to continue...")
            
            # End demo
            await self.system.end_negotiation(chat_id, "demo_completed")
            print("\n✅ Demo completed!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")

# Main entry point
def main():
    """Main entry point for the negotiation system."""
    import sys
    import asyncio
    
    # Handle webapp mode first (runs synchronously)
    if len(sys.argv) > 1 and sys.argv[1] == "webapp":
        # Complete Web Application with UI (recommended)
        try:
            from .web_client import create_web_client
            print("🚀 Starting Web Client that connects to main backend...")
            print("💡 Make sure your main backend server is running on http://localhost:8000")
            print("📱 Web client will start on http://localhost:8001")
            
            client = create_web_client("http://localhost:8000")
            client.run(port=8001)  # Run on different port to avoid conflicts
            return
        except ImportError as e:
            print("❌ Web client requires additional packages. Install with:")
            print("   pip install fastapi uvicorn httpx websockets")
            print(f"Error: {e}")
            return
    
    # All other modes run in async context
    asyncio.run(_async_main())

async def _async_main():
    """Async main function for modes that require async execution."""
    import sys
    """Main entry point for the complete system"""
    
    # Check for command line arguments
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            # Quick demo mode
            print("🚀 Running Quick Demo...")
            
            from new_agent.core.agent import demo_negotiation
            from new_agent.mcp.server import test_mcp_server
            from new_agent.intelligence.strategy import demo_negotiation_intelligence
            
            print("\n1. Testing Core Agent...")
            await demo_negotiation()
            
            print("\n2. Testing MCP Server...")
            await test_mcp_server()
            
            print("\n3. Testing Intelligence Engine...")
            await demo_negotiation_intelligence()
            
            print("\n✅ All demos completed!")
            
        elif sys.argv[1] == "buyer":
            # Interactive Buyer Agent (User as buyer, manual seller input)
            try:
                from .interactive_buyer_console import InteractiveBuyerConsole
                console = InteractiveBuyerConsole()
                await console.run()
            except ImportError as e:
                print("❌ Buyer console requires 'rich' library. Install with: pip install rich")
                print(f"Error: {e}")
                # Run simple demo
                from .buyer_agent import demo_buyer_agent
                await demo_buyer_agent()
                
        elif sys.argv[1] == "buyer-demo":
            # Quick demo of buyer agent
            from .buyer_agent import demo_buyer_agent
            await demo_buyer_agent()
            
        elif sys.argv[1] == "interactive":
            # Rich console interface (recommended)
            try:
                from .interface.interactive_console import InteractiveNegotiationConsole
                console = InteractiveNegotiationConsole()
                await console.run()
            except ImportError as e:
                print("❌ Interactive console requires 'rich' library. Install with: pip install rich")
                print(f"Error: {e}")
                # Fallback to CLI
                cli = NegotiationSystemCLI()
                await cli.run()
                
        elif sys.argv[1] == "web":
            # Web-based dashboard
            try:
                from .interface.web_ui import create_web_ui
                ui = create_web_ui()
                ui.run()
            except ImportError as e:
                print("❌ Web UI requires additional packages. Install with:")
                print("   pip install fastapi uvicorn jinja2 websockets")
                print(f"Error: {e}")
                
        elif sys.argv[1] == "cli":
            # Basic CLI interface
            cli = NegotiationSystemCLI()
            await cli.run()
            
        else:
            print("🤖 AI Negotiation Agent")
            print("Usage: python -m new_agent.main [MODE]")
            print()
            print("Available modes:")
            print("  webapp      - Complete web application with modern UI and product search (RECOMMENDED)")
            print("  demo        - Quick demonstration of all components")
            print("  buyer       - Interactive buyer agent (recommended for your use case)")
            print("  buyer-demo  - Quick demo of buyer agent capabilities")
            print("  interactive - Rich console interface (original agent as seller)")
            print("  web         - Web-based dashboard with real-time UI")
            print("  cli         - Basic command line interface")
            print()
            print("💡 For your use case (agent as buyer), use:")
            print("   python -m new_agent.main webapp")
            print("   - or -")
            print("   python -m new_agent.main buyer")
            print()
            print("Examples:")
            print("  python -m new_agent.main buyer")
            print("  python -m new_agent.main buyer-demo")
            print("  python -m new_agent.main web")
            
    else:
        # Default to buyer mode if available, otherwise show help
        try:
            from .interactive_buyer_console import InteractiveBuyerConsole
            print("🚀 Starting Buyer Agent (default mode)")
            print("💡 Agent represents YOU as the buyer, you input seller responses manually")
            console = InteractiveBuyerConsole()
            await console.run()
        except ImportError:
            print("🛒 AI Buyer Negotiation Agent")
            print()
            print("For the best experience, install rich library:")
            print("  pip install rich")
            print()
            print("Then run: python -m new_agent.main buyer")
            print()
            print("Or try: python -m new_agent.main buyer-demo")
            print()
            print("Running basic demo...")
            from .buyer_agent import demo_buyer_agent
            await demo_buyer_agent()

if __name__ == "__main__":
    main()