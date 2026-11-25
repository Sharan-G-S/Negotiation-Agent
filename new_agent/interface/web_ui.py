"""
Web-based UI Dashboard for Negotiation Agent
Modern web interface with real-time negotiation display and controls
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import uvicorn

from ..core.agent import NegotiationAgent
from ..mcp.server import NegotiationMCPServer
from ..intelligence.strategy import NegotiationIntelligenceEngine, NegotiationPhase, NegotiationTactic
from .interactive_console import NegotiationTone

class NegotiationWebUI:
    """Web-based UI for negotiation agent"""
    
    def __init__(self):
        self.app = FastAPI(title="AI Negotiation Agent", description="Interactive negotiation interface")
        self.templates = Jinja2Templates(directory="templates")
        
        # Create templates and static directories
        self.setup_directories()
        
        # Core components
        self.agent = None
        self.mcp_server = None
        self.intelligence_engine = None
        
        # Active sessions
        self.active_sessions: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Setup routes
        self.setup_routes()
        
        # Initialize components
        asyncio.create_task(self.initialize_components())
    
    def setup_directories(self):
        """Create necessary directories and files"""
        # Create templates directory
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        # Create static directory
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    async def initialize_components(self):
        """Initialize AI components"""
        # Get API key from environment
        api_key = os.getenv('GOOGLE_API_KEY', 'mock')
        
        self.agent = NegotiationAgent(api_key=api_key)
        self.mcp_server = NegotiationMCPServer()
        self.intelligence_engine = NegotiationIntelligenceEngine()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard"""
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "AI Negotiation Agent Dashboard"
            })
        
        @self.app.get("/api/sessions")
        async def get_sessions():
            """Get all active sessions"""
            return {"sessions": list(self.active_sessions.keys())}
        
        @self.app.post("/api/sessions")
        async def create_session(data: dict):
            """Create new negotiation session"""
            session_id = str(uuid.uuid4())[:8]
            
            session_data = {
                "session_id": session_id,
                "product": data.get("product", "Product"),
                "target_price": data.get("target_price", 500),
                "max_price": data.get("max_price", 800),
                "tone": data.get("tone", "professional"),
                "created_at": datetime.now().isoformat(),
                "history": [],
                "current_phase": NegotiationPhase.GREETING,
                "round_count": 0,
                "status": "active"
            }
            
            self.active_sessions[session_id] = session_data
            
            # Create MCP session
            if self.mcp_server:
                mcp_session = await self.mcp_server.create_session({
                    "product": session_data["product"],
                    "target_price": session_data["target_price"],
                    "max_price": session_data["max_price"],
                    "user_id": session_id,
                    "tone": session_data["tone"]
                })
                session_data["mcp_session"] = mcp_session
            
            return {"session_id": session_id, "session": session_data}
        
        @self.app.get("/api/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get specific session"""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            return self.active_sessions[session_id]
        
        @self.app.post("/api/sessions/{session_id}/message")
        async def send_message(session_id: str, data: dict):
            """Send message in session"""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = self.active_sessions[session_id]
            seller_message = data.get("message", "")
            
            # Add seller message to history
            session["history"].append({
                "role": "seller",
                "message": seller_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Get AI response
            context = {
                "product": session["product"],
                "target_price": session["target_price"],
                "max_price": session["max_price"],
                "tone": session["tone"],
                "conversation_history": session["history"],
                "current_phase": session["current_phase"],
                "round_count": session["round_count"]
            }
            
            if self.agent:
                agent_response = await self.agent.get_response(seller_message, context)
            else:
                agent_response = "I'm interested in negotiating for this item."
            
            # Analyze seller
            seller_analysis = None
            tactics = []
            if self.intelligence_engine:
                seller_messages = [msg["message"] for msg in session["history"] if msg["role"] == "seller"]
                seller_analysis = await self.intelligence_engine.analyze_seller(
                    session["history"], seller_messages
                )
                tactics = await self.intelligence_engine.recommend_tactics(seller_analysis, context)
            
            # Add agent response to history
            session["history"].append({
                "role": "agent", 
                "message": agent_response,
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "seller_type": seller_analysis.personality_type if seller_analysis else "unknown",
                    "flexibility": seller_analysis.flexibility_score if seller_analysis else 0.5,
                    "urgency": seller_analysis.urgency_level if seller_analysis else 0.5,
                    "tactics": [(tactic.value, confidence) for tactic, confidence in tactics[:3]]
                }
            })
            
            session["round_count"] += 1
            
            # Notify WebSocket connections
            if session_id in self.websocket_connections:
                await self.websocket_connections[session_id].send_text(json.dumps({
                    "type": "message",
                    "session_id": session_id,
                    "history": session["history"],
                    "round_count": session["round_count"]
                }))
            
            return {"response": agent_response, "session": session}
        
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket connection for real-time updates"""
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle incoming WebSocket messages if needed
                    pass
            except WebSocketDisconnect:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
        
        @self.app.get("/api/tones")
        async def get_available_tones():
            """Get available negotiation tones"""
            return {
                "tones": [
                    {"value": tone.value, "label": tone.value.title(), "description": self.get_tone_description(tone)}
                    for tone in NegotiationTone
                ]
            }
        
        @self.app.get("/api/tactics")
        async def get_available_tactics():
            """Get available negotiation tactics"""
            return {
                "tactics": [
                    {"value": tactic.value, "label": tactic.value.replace("_", " ").title()}
                    for tactic in NegotiationTactic
                ]
            }
    
    def get_tone_description(self, tone: NegotiationTone) -> str:
        """Get description for tone"""
        descriptions = {
            NegotiationTone.PROFESSIONAL: "Formal, business-like approach",
            NegotiationTone.FRIENDLY: "Warm, relationship-focused",
            NegotiationTone.AGGRESSIVE: "Direct, assertive, high-pressure",
            NegotiationTone.DIPLOMATIC: "Tactful, measured responses",
            NegotiationTone.CASUAL: "Relaxed, informal style",
            NegotiationTone.FORMAL: "Structured, official communication",
            NegotiationTone.PERSUASIVE: "Influence-focused, compelling",
            NegotiationTone.ANALYTICAL: "Data-driven, logical approach"
        }
        return descriptions.get(tone, "")
    
    def run(self, host: str = "localhost", port: int = 8000):
        """Run the web server"""
        print(f"🚀 Starting AI Negotiation Agent Web UI...")
        print(f"📱 Dashboard: http://{host}:{port}")
        print(f"🔧 API Docs: http://{host}:{port}/docs")
        
        uvicorn.run(self.app, host=host, port=port)

# Create HTML templates
def create_dashboard_template():
    """Create the dashboard HTML template"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-shadow { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
        .message-bubble { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="bg-gray-100">
    <!-- Header -->
    <nav class="gradient-bg text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold">🤖 AI Negotiation Agent</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <button id="newSessionBtn" class="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition">
                        + New Session
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- Configuration Panel -->
            <div class="lg:col-span-1">
                <div class="bg-white card-shadow rounded-lg p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4">🎛️ Configuration</h2>
                    
                    <form id="configForm" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
                            <input type="text" id="productName" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="iPhone 13 Pro">
                        </div>
                        
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Target Price</label>
                                <input type="number" id="targetPrice" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Max Price</label>
                                <input type="number" id="maxPrice" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="800">
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Negotiation Tone</label>
                            <select id="negotiationTone" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                <option value="professional">Professional</option>
                                <option value="friendly">Friendly</option>
                                <option value="aggressive">Aggressive</option>
                                <option value="diplomatic">Diplomatic</option>
                                <option value="casual">Casual</option>
                                <option value="persuasive">Persuasive</option>
                                <option value="analytical">Analytical</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Aggressiveness</label>
                            <input type="range" id="aggressiveness" min="0" max="100" value="50" class="w-full">
                            <div class="flex justify-between text-xs text-gray-500">
                                <span>Gentle</span>
                                <span>Moderate</span>
                                <span>Assertive</span>
                            </div>
                        </div>
                        
                        <button type="button" id="startNegotiationBtn" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition font-semibold">
                            🚀 Start Negotiation
                        </button>
                    </form>
                </div>
                
                <!-- Analytics Panel -->
                <div class="bg-white card-shadow rounded-lg p-6 mt-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4">📊 Analytics</h2>
                    <div id="analyticsContent">
                        <div class="text-center text-gray-500 py-8">
                            Start a negotiation to see analytics
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main Chat Panel -->
            <div class="lg:col-span-2">
                <div class="bg-white card-shadow rounded-lg">
                    <!-- Chat Header -->
                    <div class="border-b border-gray-200 p-4">
                        <div class="flex justify-between items-center">
                            <h2 class="text-lg font-semibold text-gray-900">💬 Negotiation Chat</h2>
                            <div id="sessionInfo" class="text-sm text-gray-500">No active session</div>
                        </div>
                    </div>
                    
                    <!-- Chat Messages -->
                    <div id="chatMessages" class="h-96 overflow-y-auto p-4 space-y-4">
                        <div class="text-center text-gray-500 py-8">
                            Start a negotiation session to begin chatting
                        </div>
                    </div>
                    
                    <!-- Chat Input -->
                    <div class="border-t border-gray-200 p-4">
                        <div class="flex space-x-4">
                            <input type="text" id="messageInput" placeholder="Enter seller message..." 
                                   class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" disabled>
                            <button id="sendMessageBtn" class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition font-semibold" disabled>
                                Send
                            </button>
                        </div>
                        <div class="mt-2 flex flex-wrap gap-2">
                            <button class="quick-message bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm hover:bg-gray-200 transition" disabled>
                                "I'm interested in this item"
                            </button>
                            <button class="quick-message bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm hover:bg-gray-200 transition" disabled>
                                "What's your best price?"
                            </button>
                            <button class="quick-message bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm hover:bg-gray-200 transition" disabled>
                                "Can we negotiate?"
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Tactics Panel -->
                <div class="bg-white card-shadow rounded-lg p-6 mt-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4">🎯 Recommended Tactics</h2>
                    <div id="tacticsContent">
                        <div class="text-center text-gray-500 py-4">
                            Tactics will appear during negotiation
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSession = null;
        let websocket = null;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            loadTones();
        });

        function setupEventListeners() {
            document.getElementById('startNegotiationBtn').addEventListener('click', startNegotiation);
            document.getElementById('sendMessageBtn').addEventListener('click', sendMessage);
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });

            // Quick message buttons
            document.querySelectorAll('.quick-message').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.getElementById('messageInput').value = this.textContent.replace(/"/g, '');
                    sendMessage();
                });
            });
        }

        async function loadTones() {
            try {
                const response = await fetch('/api/tones');
                const data = await response.json();
                const select = document.getElementById('negotiationTone');
                select.innerHTML = '';
                data.tones.forEach(tone => {
                    const option = document.createElement('option');
                    option.value = tone.value;
                    option.textContent = tone.label;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading tones:', error);
            }
        }

        async function startNegotiation() {
            const config = {
                product: document.getElementById('productName').value,
                target_price: parseInt(document.getElementById('targetPrice').value),
                max_price: parseInt(document.getElementById('maxPrice').value),
                tone: document.getElementById('negotiationTone').value
            };

            try {
                const response = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                currentSession = data.session_id;
                
                // Update UI
                document.getElementById('sessionInfo').textContent = `Session: ${currentSession}`;
                document.getElementById('messageInput').disabled = false;
                document.getElementById('sendMessageBtn').disabled = false;
                document.querySelectorAll('.quick-message').forEach(btn => btn.disabled = false);
                
                // Clear chat
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = '<div class="text-center text-green-600 py-4">🚀 Negotiation started! Enter a seller message to begin.</div>';
                
                // Setup WebSocket
                setupWebSocket();
                
                // Update analytics
                updateAnalytics(data.session);
                
            } catch (error) {
                console.error('Error starting negotiation:', error);
                alert('Failed to start negotiation');
            }
        }

        function setupWebSocket() {
            if (websocket) websocket.close();
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            websocket = new WebSocket(`${protocol}//${window.location.host}/ws/${currentSession}`);
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    updateChatDisplay(data.history);
                    updateAnalytics({round_count: data.round_count});
                }
            };
        }

        async function sendMessage() {
            if (!currentSession) return;
            
            const message = document.getElementById('messageInput').value.trim();
            if (!message) return;

            try {
                const response = await fetch(`/api/sessions/${currentSession}/message`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });

                const data = await response.json();
                document.getElementById('messageInput').value = '';
                updateChatDisplay(data.session.history);
                updateAnalytics(data.session);
                
                // Display tactics
                const lastMessage = data.session.history[data.session.history.length - 1];
                if (lastMessage.analysis) {
                    updateTactics(lastMessage.analysis);
                }

            } catch (error) {
                console.error('Error sending message:', error);
                alert('Failed to send message');
            }
        }

        function updateChatDisplay(history) {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';

            history.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message-bubble ${msg.role === 'seller' ? 'text-right' : 'text-left'}`;
                
                const bubble = document.createElement('div');
                bubble.className = `inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    msg.role === 'seller' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-900'
                }`;
                
                const icon = msg.role === 'seller' ? '💼' : '🤖';
                bubble.innerHTML = `<strong>${icon} ${msg.role === 'seller' ? 'Seller' : 'Agent'}:</strong><br>${msg.message}`;
                
                messageDiv.appendChild(bubble);
                chatMessages.appendChild(messageDiv);
            });

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function updateAnalytics(session) {
            const analyticsContent = document.getElementById('analyticsContent');
            analyticsContent.innerHTML = `
                <div class="grid grid-cols-2 gap-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${session.round_count || 0}</div>
                        <div class="text-sm text-gray-500">Rounds</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-green-600">${(session.history || []).length}</div>
                        <div class="text-sm text-gray-500">Messages</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-purple-600">$${session.target_price || 0}</div>
                        <div class="text-sm text-gray-500">Target</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-red-600">$${session.max_price || 0}</div>
                        <div class="text-sm text-gray-500">Max Price</div>
                    </div>
                </div>
            `;
        }

        function updateTactics(analysis) {
            const tacticsContent = document.getElementById('tacticsContent');
            let tacticsHtml = '';
            
            if (analysis.tactics && analysis.tactics.length > 0) {
                tacticsHtml = '<div class="space-y-3">';
                analysis.tactics.forEach((tactic, index) => {
                    const [name, confidence] = tactic;
                    const percentage = Math.round(confidence * 100);
                    tacticsHtml += `
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-gray-900">${name.replace(/_/g, ' ').toUpperCase()}</div>
                                <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                                    <div class="bg-blue-600 h-2 rounded-full" style="width: ${percentage}%"></div>
                                </div>
                            </div>
                            <div class="ml-3 text-sm font-semibold text-gray-600">${percentage}%</div>
                        </div>
                    `;
                });
                tacticsHtml += '</div>';
                
                // Add seller analysis
                tacticsHtml += `
                    <div class="mt-6 pt-4 border-t border-gray-200">
                        <h4 class="text-sm font-semibold text-gray-900 mb-2">Seller Analysis</h4>
                        <div class="grid grid-cols-2 gap-2 text-sm">
                            <div>Type: <span class="font-medium">${analysis.seller_type}</span></div>
                            <div>Flexibility: <span class="font-medium">${Math.round(analysis.flexibility * 100)}%</span></div>
                        </div>
                    </div>
                `;
            } else {
                tacticsHtml = '<div class="text-center text-gray-500 py-4">No tactics recommended yet</div>';
            }
            
            tacticsContent.innerHTML = tacticsHtml;
        }
    </script>
</body>
</html>
    """
    
    # Write template file
    Path("templates").mkdir(exist_ok=True)
    with open("templates/dashboard.html", "w") as f:
        f.write(html_content)

# Create the web UI instance
def create_web_ui():
    """Create and return web UI instance"""
    create_dashboard_template()
    return NegotiationWebUI()

if __name__ == "__main__":
    ui = create_web_ui()
    ui.run()