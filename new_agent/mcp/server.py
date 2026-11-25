"""
Model Context Protocol (MCP) Server for Negotiation Agent
Handles context management, session persistence, and real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# MCP Server implementation
class NegotiationMCPServer:
    """MCP Server for managing negotiation contexts and sessions"""
    
    def __init__(self, storage_path: str = "./negotiation_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.active_sessions: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize data files
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage directories and files"""
        (self.storage_path / "sessions").mkdir(exist_ok=True)
        (self.storage_path / "contexts").mkdir(exist_ok=True)
        (self.storage_path / "analytics").mkdir(exist_ok=True)
        
        # Load active sessions
        self._load_active_sessions()
    
    def _load_active_sessions(self):
        """Load active sessions from storage"""
        sessions_file = self.storage_path / "active_sessions.json"
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r') as f:
                    self.active_sessions = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading active sessions: {e}")
                self.active_sessions = {}
    
    def _save_active_sessions(self):
        """Save active sessions to storage"""
        sessions_file = self.storage_path / "active_sessions.json"
        try:
            with open(sessions_file, 'w') as f:
                json.dump(self.active_sessions, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving active sessions: {e}")
    
    async def create_session(self, session_data: Dict) -> str:
        """Create a new negotiation session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        session_info = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "data": session_data,
            "messages": [],
            "context_updates": []
        }
        
        # Store in active sessions
        self.active_sessions[session_id] = session_info
        
        # Persist to file
        session_file = self.storage_path / "sessions" / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_info, f, indent=2, default=str)
        
        self._save_active_sessions()
        
        self.logger.info(f"Created new session: {session_id}")
        return session_id
    
    async def update_context(self, session_id: str, context_update: Dict) -> bool:
        """Update negotiation context for a session"""
        if session_id not in self.active_sessions:
            self.logger.error(f"Session {session_id} not found")
            return False
        
        try:
            # Add timestamp to update
            context_update["timestamp"] = datetime.now().isoformat()
            
            # Update active session
            session = self.active_sessions[session_id]
            session["context_updates"].append(context_update)
            session["last_updated"] = datetime.now().isoformat()
            
            # Merge context updates into session data
            if "context" not in session["data"]:
                session["data"]["context"] = {}
            
            session["data"]["context"].update(context_update)
            
            # Persist updates
            await self._persist_session(session_id)
            
            self.logger.info(f"Updated context for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating context: {e}")
            return False
    
    async def add_message(self, session_id: str, message: Dict) -> bool:
        """Add a message to the session"""
        if session_id not in self.active_sessions:
            return False
        
        try:
            message["timestamp"] = datetime.now().isoformat()
            message["id"] = f"msg_{len(self.active_sessions[session_id]['messages']) + 1}"
            
            self.active_sessions[session_id]["messages"].append(message)
            self.active_sessions[session_id]["last_updated"] = datetime.now().isoformat()
            
            # Persist updates
            await self._persist_session(session_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding message: {e}")
            return False
    
    async def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Get current session context"""
        if session_id not in self.active_sessions:
            # Try to load from file
            await self._load_session(session_id)
        
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["data"].get("context", {})
        
        return None
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.active_sessions:
            await self._load_session(session_id)
        
        if session_id in self.active_sessions:
            messages = self.active_sessions[session_id]["messages"]
            return messages[-limit:] if limit > 0 else messages
        
        return []
    
    async def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a negotiation session"""
        if session_id not in self.active_sessions:
            await self._load_session(session_id)
        
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        messages = session["messages"]
        
        # Calculate analytics
        analytics = {
            "session_id": session_id,
            "duration_minutes": 0,
            "message_count": len(messages),
            "agent_messages": len([m for m in messages if m.get("sender") == "agent"]),
            "seller_messages": len([m for m in messages if m.get("sender") == "seller"]),
            "negotiation_rounds": 0,
            "price_progression": [],
            "tactics_used": [],
            "final_outcome": session.get("status", "active")
        }
        
        # Calculate duration
        if messages:
            start_time = datetime.fromisoformat(session["created_at"])
            last_time = datetime.fromisoformat(messages[-1]["timestamp"])
            analytics["duration_minutes"] = (last_time - start_time).total_seconds() / 60
        
        # Extract price progression and tactics
        for msg in messages:
            if "price" in msg.get("content", "").lower():
                # Extract price mentions (simplified)
                import re
                prices = re.findall(r'\$(\d+(?:\.\d{2})?)', msg.get("content", ""))
                if prices:
                    analytics["price_progression"].append({
                        "timestamp": msg["timestamp"],
                        "sender": msg.get("sender"),
                        "price": float(prices[0])
                    })
        
        return analytics
    
    async def close_session(self, session_id: str, outcome: str = "completed") -> bool:
        """Close a negotiation session"""
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            session["status"] = "closed"
            session["outcome"] = outcome
            session["closed_at"] = datetime.now().isoformat()
            
            # Generate final analytics
            analytics = await self.get_session_analytics(session_id)
            session["final_analytics"] = analytics
            
            # Persist final session
            await self._persist_session(session_id)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            self._save_active_sessions()
            
            self.logger.info(f"Closed session {session_id} with outcome: {outcome}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing session: {e}")
            return False
    
    async def _persist_session(self, session_id: str):
        """Persist session data to file"""
        if session_id not in self.active_sessions:
            return
        
        session_file = self.storage_path / "sessions" / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(self.active_sessions[session_id], f, indent=2, default=str)
    
    async def _load_session(self, session_id: str):
        """Load session from file"""
        session_file = self.storage_path / "sessions" / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    self.active_sessions[session_id] = session_data
            except Exception as e:
                self.logger.error(f"Error loading session {session_id}: {e}")
    
    async def list_active_sessions(self) -> List[Dict]:
        """List all active negotiation sessions"""
        return [
            {
                "id": sid,
                "created_at": session["created_at"],
                "last_updated": session.get("last_updated"),
                "message_count": len(session["messages"]),
                "status": session["status"]
            }
            for sid, session in self.active_sessions.items()
        ]
    
    async def get_global_analytics(self) -> Dict:
        """Get analytics across all sessions"""
        all_sessions = list(self.active_sessions.values())
        
        # Load closed sessions for comprehensive analytics
        sessions_dir = self.storage_path / "sessions"
        for session_file in sessions_dir.glob("*.json"):
            if session_file.stem not in self.active_sessions:
                try:
                    with open(session_file, 'r') as f:
                        closed_session = json.load(f)
                        all_sessions.append(closed_session)
                except Exception:
                    continue
        
        analytics = {
            "total_sessions": len(all_sessions),
            "active_sessions": len(self.active_sessions),
            "closed_sessions": len(all_sessions) - len(self.active_sessions),
            "success_rate": 0,
            "average_duration_minutes": 0,
            "average_rounds": 0,
            "most_common_outcomes": {},
            "platform_breakdown": {}
        }
        
        if all_sessions:
            # Calculate success rate
            successful = len([s for s in all_sessions if s.get("outcome") in ["agreement", "success"]])
            analytics["success_rate"] = successful / len(all_sessions) * 100
            
            # Calculate averages
            total_duration = 0
            total_messages = 0
            
            for session in all_sessions:
                if session.get("final_analytics"):
                    total_duration += session["final_analytics"].get("duration_minutes", 0)
                total_messages += len(session.get("messages", []))
            
            analytics["average_duration_minutes"] = total_duration / len(all_sessions)
            analytics["average_messages_per_session"] = total_messages / len(all_sessions)
        
        return analytics

# Context Manager for handling MCP operations
class NegotiationContextManager:
    """Manages negotiation contexts with MCP integration"""
    
    def __init__(self, mcp_server: NegotiationMCPServer):
        self.mcp_server = mcp_server
        self.current_contexts: Dict[str, Dict] = {}
    
    async def create_negotiation_context(
        self, 
        product_info: Dict,
        goals: Dict,
        user_preferences: Dict = None
    ) -> str:
        """Create a new negotiation context"""
        
        context_data = {
            "product_info": product_info,
            "goals": goals,
            "user_preferences": user_preferences or {},
            "negotiation_state": {
                "phase": "greeting",
                "round": 0,
                "tactics_used": [],
                "offers_made": [],
                "seller_offers": []
            },
            "market_data": {},
            "seller_analysis": {}
        }
        
        # Create session in MCP server
        session_id = await self.mcp_server.create_session(context_data)
        
        # Store locally for quick access
        self.current_contexts[session_id] = context_data
        
        return session_id
    
    async def update_negotiation_state(
        self, 
        session_id: str, 
        state_updates: Dict
    ) -> bool:
        """Update negotiation state"""
        
        if session_id not in self.current_contexts:
            # Load from MCP server
            context = await self.mcp_server.get_session_context(session_id)
            if context:
                self.current_contexts[session_id] = context
            else:
                return False
        
        # Update local context
        if "negotiation_state" not in self.current_contexts[session_id]:
            self.current_contexts[session_id]["negotiation_state"] = {}
        
        self.current_contexts[session_id]["negotiation_state"].update(state_updates)
        
        # Persist to MCP server
        return await self.mcp_server.update_context(session_id, state_updates)
    
    async def get_context_summary(self, session_id: str) -> Dict:
        """Get a summary of the negotiation context"""
        
        if session_id not in self.current_contexts:
            context = await self.mcp_server.get_session_context(session_id)
            if context:
                self.current_contexts[session_id] = context
            else:
                return {}
        
        context = self.current_contexts[session_id]
        
        return {
            "product": context.get("product_info", {}).get("name", "Unknown"),
            "target_price": context.get("goals", {}).get("target_price", 0),
            "current_phase": context.get("negotiation_state", {}).get("phase", "unknown"),
            "rounds_completed": context.get("negotiation_state", {}).get("round", 0),
            "tactics_available": ["anchoring", "bundling", "scarcity", "compromise"],
            "next_recommended_action": self._get_recommended_action(context)
        }
    
    def _get_recommended_action(self, context: Dict) -> str:
        """Get recommended next action based on context"""
        state = context.get("negotiation_state", {})
        phase = state.get("phase", "greeting")
        round_num = state.get("round", 0)
        
        if phase == "greeting":
            return "Express interest and ask about product details"
        elif phase == "discovery":
            return "Make initial offer based on market analysis"
        elif phase == "bargaining" and round_num < 3:
            return "Counter-offer with justification"
        elif round_num >= 5:
            return "Consider final offer or walk away"
        else:
            return "Continue negotiation with appropriate tactic"

# Example usage and testing
async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🔧 Testing MCP Server...")
    
    # Initialize MCP server
    mcp_server = NegotiationMCPServer("./test_negotiation_data")
    context_manager = NegotiationContextManager(mcp_server)
    
    # Create test negotiation
    product_info = {
        "name": "iPhone 13 Pro",
        "listed_price": 800,
        "seller": "John Doe",
        "platform": "Facebook Marketplace"
    }
    
    goals = {
        "target_price": 650,
        "max_budget": 720,
        "timeline": "flexible"
    }
    
    # Create context
    session_id = await context_manager.create_negotiation_context(product_info, goals)
    print(f"✅ Created session: {session_id}")
    
    # Add some messages
    await mcp_server.add_message(session_id, {
        "sender": "agent",
        "content": "Hi! I'm interested in your iPhone. Is it still available?"
    })
    
    await mcp_server.add_message(session_id, {
        "sender": "seller", 
        "content": "Yes, it's available. I'm asking $800 for it."
    })
    
    # Update context
    await context_manager.update_negotiation_state(session_id, {
        "phase": "initial_offer",
        "round": 1
    })
    
    # Get analytics
    analytics = await mcp_server.get_session_analytics(session_id)
    print(f"📊 Session analytics: {analytics}")
    
    # Get context summary
    summary = await context_manager.get_context_summary(session_id)
    print(f"📋 Context summary: {summary}")
    
    print("✅ MCP Server test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())