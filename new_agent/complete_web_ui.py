"""
Complete Web UI for Buyer-Seller Negotiation
Agent bargains with seller (user input) in full NLP mode
"""

import asyncio
import json
import logging
import os
import random
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import uvicorn
import httpx

# Handle imports for both module and direct execution
try:
    from .buyer_agent import BuyerNegotiationAgent, BuyerPersonality, OnlineSellerFinderTool
except ImportError:
    # Fallback for direct execution - add parent directory to path
    import sys
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from new_agent.buyer_agent import BuyerNegotiationAgent, BuyerPersonality, OnlineSellerFinderTool

# Try to import GeminiService from backend
try:
    from backend.gemini_service import GeminiService
except ImportError:
    try:
        import sys
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        from backend.gemini_service import GeminiService
    except ImportError:
        print("Warning: Could not import GeminiService, will use mock responses only")
        GeminiService = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NegotiationWebApp:
    """Complete Web Application for Buyer-Seller Negotiation"""
    
    def __init__(self):
        self.app = FastAPI(title="AI Buyer Negotiation Agent", description="Complete negotiation interface")
        
        # Backend URL for potential future use
        self.backend_url = "http://localhost:8000"
        
        # Create template directory and file
        Path("templates").mkdir(exist_ok=True)
        
        self.templates = Jinja2Templates(directory="templates")
        
        # Setup directories
        self.setup_directories()
        
        # Active sessions and WebSocket connections
        self.active_sessions: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}  # Add sessions dict for compatibility
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Initialize AI service
        self.gemini_service = None
        self.use_real_ai = False
        
        # Try to initialize AI service
        try:
            if GeminiService is not None:
                self.gemini_service = GeminiService()
                self.use_real_ai = True
                print("✅ AI service initialized successfully")
            else:
                print("🎭 Running in mock mode - AI service not available")
        except Exception as e:
            print(f"⚠️  AI service initialization failed: {e}")
            print("🎭 Running in mock mode")
        
        # Setup routes
        self.setup_routes()
    
    def setup_directories(self):
        """Create necessary directories"""
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def main_dashboard(request: Request):
            """Main negotiation dashboard"""
            # Return HTML directly instead of using templates
            html_content = self._get_dashboard_html()
            return HTMLResponse(content=html_content)
        
        @self.app.get("/api/personalities")
        async def get_personalities():
            """Get available buyer personalities"""
            # Return personalities directly since this is self-contained
            return {
                "personalities": [
                    {
                        "value": "budget_conscious",
                        "label": "Budget Conscious",
                        "description": "Focuses on getting the lowest price possible"
                    },
                    {
                        "value": "value_seeker", 
                        "label": "Value Seeker",
                        "description": "Wants the best value for money (recommended)"
                    },
                    {
                        "value": "tech_savvy",
                        "label": "Tech Savvy",
                        "description": "Knowledgeable about technical specifications"
                    },
                    {
                        "value": "relationship_builder",
                        "label": "Relationship Builder", 
                        "description": "Builds rapport and maintains good relationships"
                    },
                    {
                        "value": "time_conscious",
                        "label": "Time Conscious",
                        "description": "Values quick decision-making and efficiency"
                    },
                    {
                        "value": "deal_hunter",
                        "label": "Deal Hunter",
                        "description": "Actively seeks the best deals and discounts"
                    }
                ]
            }

        @self.app.post("/api/search")
        async def search_products(request: Request):
            """Enhanced search with OLX link support and location-based sellers"""
            data = await request.json()
            product_input = data.get("query", "").strip()
            city = data.get("city", "").strip()
            
            # Check if input is an OLX link
            if "olx.in" in product_input.lower() or "quikr.com" in product_input.lower():
                try:
                    # Extract product details from OLX link (mock implementation)
                    product_name = self._extract_product_from_link(product_input)
                    sellers = self._find_sellers_with_location(product_name, city)
                    return {
                        "success": True,
                        "product_detected": product_name,
                        "link_processed": True,
                        "sellers": sellers,
                        "message": f"🔗 Product detected from link: {product_name}"
                    }
                except Exception as e:
                    logger.error(f"Failed to process link: {e}")
                    
            # Regular product search with location
            if city:
                product_query = f"{product_input} {city}"
                sellers = self._find_sellers_with_location(product_input, city)
                message = f"🏙️ Found sellers in {city} for {product_input}"
            else:
                sellers = self._mock_seller_search(product_input)
                message = f"Found sellers for {product_input}"
            
            return {
                "success": True,
                "sellers": sellers,
                "message": message,
                "link_processed": False
            }
        
        @self.app.get("/api/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session data"""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = self.active_sessions[session_id]
            agent = session["agent"]
            
            # Remove agent object for JSON serialization
            session_copy = session.copy()
            session_copy["summary"] = agent.get_negotiation_summary()
            del session_copy["agent"]  # Can't serialize the agent object
            
            return session_copy
            
        @self.app.post("/api/negotiate-url")
        async def negotiate_url(request: dict):
            """Start negotiation from marketplace URL"""
            url = request.get('url', '').strip()
            personality = request.get('personality', 'value_seeker')
            target_price = request.get('target_price', 0)
            max_budget = request.get('max_budget', 0)
            
            if not url:
                return {"error": "URL is required"}
            
            try:
                # Extract product from URL
                product_name = self._extract_product_from_link(url)
                
                # Create session data
                session_data = {
                    'product': product_name,
                    'personality': personality,
                    'target_price': target_price,
                    'max_budget': max_budget,
                    'source_url': url
                }
                
                # Create a new session
                session_id = str(uuid.uuid4())
                mock_mode = True  # Always mock mode for now
                
                self.active_sessions[session_id] = {
                    'id': session_id,
                    'config': session_data,
                    'conversation': [],
                    'created_at': datetime.now().isoformat(),
                    'mock_mode': mock_mode,
                    'agent': None  # No real agent in mock mode
                }
                
                print(f"🎯 Created URL-based session {session_id} for {product_name}")
                
                return {
                    'session_id': session_id,
                    'product_name': product_name,
                    'message': f'Ready to negotiate for {product_name}',
                    'mock_mode': mock_mode
                }
                
            except Exception as e:
                print(f"❌ Error creating URL session: {e}")
                return {"error": f"Failed to process URL: {str(e)}"}
            
        @self.app.post("/api/create-session")
        async def create_negotiation_session(data: dict):
            """Create new negotiation session"""
            session_id = str(uuid.uuid4())[:8]
            
            # Check if Google API key is available
            api_key = os.getenv('GOOGLE_API_KEY')
            mock_mode = not bool(api_key)
            
            if mock_mode:
                logger.info("🎭 Running in demo/mock mode - no Google API key found")
            
            # Create buyer agent
            personality = BuyerPersonality(data.get("personality", "value_seeker"))
            
            # Only create real agent if API key is available
            agent = None
            if not mock_mode:
                try:
                    agent = BuyerNegotiationAgent(api_key=api_key, personality=personality)
                    logger.info(f"✅ Created real AI agent with {personality.value} personality")
                except Exception as e:
                    logger.error(f"❌ Failed to create AI agent: {e}")
                    mock_mode = True
            
            # Store session data
            self.active_sessions[session_id] = {
                'id': session_id,
                'config': data,
                'conversation': [],
                'created_at': datetime.now().isoformat(),
                'mock_mode': mock_mode,
                'agent': agent
            }
            
            return {
                "session_id": session_id, 
                "status": "created",
                "mock_mode": mock_mode,
                "message": "🎭 Demo mode - AI responses are simulated" if mock_mode else "🤖 AI agent ready"
            }
        
        @self.app.post("/api/send-message")
        async def send_message(request: dict):
            """Process seller message and generate agent response"""
            session_id = request.get('session_id')
            message = request.get('message', '').strip()
            
            print(f"📨 Processing message for session {session_id}: {message}")
            
            if not session_id or not message:
                print("❌ Missing session_id or message")
                return {"error": "Session ID and message required"}
            
            if session_id not in self.active_sessions:
                print(f"❌ Session {session_id} not found in active sessions")
                print(f"Available sessions: {list(self.active_sessions.keys())}")
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            try:
                # Add seller message to conversation
                if 'conversation' not in session:
                    session['conversation'] = []
                    
                session['conversation'].append({
                    'role': 'seller',
                    'content': message,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"💬 Added seller message to session {session_id}")
                
                # Generate agent response
                ai_response = ""
                
                if session.get('mock_mode', True):
                    print("🎭 Generating mock response...")
                    ai_response = self._generate_mock_response(message, session)
                elif session.get('agent') and self.use_real_ai:
                    print("🤖 Generating real AI response...")
                    try:
                        agent = session['agent']
                        ai_response = await agent.respond_to_seller(message)
                    except Exception as e:
                        print(f"❌ AI generation failed: {e}")
                        ai_response = self._generate_mock_response(message, session)
                else:
                    print("🎭 No AI agent available, using mock response")
                    ai_response = self._generate_mock_response(message, session)
                
                # Add agent response to conversation
                session['conversation'].append({
                    'role': 'agent',
                    'content': ai_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"📝 Agent response added to session {session_id}: {ai_response[:100]}...")
                
                return {
                    "response": ai_response,
                    "session_id": session_id,
                    "mock_mode": session.get('mock_mode', True),
                    "message_count": len(session.get('conversation', []))
                }
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                return {
                    "error": f"Failed to process message: {str(e)}",
                    "response": "I apologize, but I'm having trouble processing your message right now. Please try again.",
                    "mock_mode": True
                }
            
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]

    def _get_dashboard_html(self) -> str:
        """Get the dashboard HTML content"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Buyer Negotiation Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-shadow { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
        .message-bubble { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .seller-message { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
        .agent-message { background: linear-gradient(135deg, #4834d4, #686de0); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <nav class="gradient-bg text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <h1 class="text-2xl font-bold">🛒 AI Buyer Negotiation Agent</h1>
                <div class="text-sm">Agent negotiates as buyer with seller (you)</div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
""" + self._get_rest_of_html()

    def _get_rest_of_html(self) -> str:
        """Get the rest of the HTML content - continuing from the header"""
        # I'll need to get the rest of the HTML from the create_negotiation_template function
        # For now, let me return a simple working version
        return """
        <!-- Setup Phase -->
        <div id="setupPhase" class="space-y-8">
            <!-- Search Section -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-800 mb-6">🔍 Find Products & Sellers</h2>
                <div class="grid md:grid-cols-2 gap-4">
                    <div>
                        <label for="productSearch" class="block text-sm font-medium text-gray-700 mb-2">Product Name or Marketplace Link</label>
                        <input type="text" id="productSearch" placeholder="e.g., iPhone 13 Pro or paste OLX/Quikr link" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    <div>
                        <label for="cityLocation" class="block text-sm font-medium text-gray-700 mb-2">City (Optional)</label>
                        <input type="text" id="cityLocation" placeholder="e.g., Mumbai, Delhi, Bangalore" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                </div>
                <button id="searchBtn" onclick="searchProducts()" 
                        class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition duration-200">
                    🔍 Search Sellers
                </button>
                
                <div id="searchResults" class="mt-6 hidden"></div>
            </div>

            <!-- Configuration Section -->
            <div id="configSection" class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-800 mb-6">⚙️ Setup Your AI Buyer Agent</h2>
                
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                        <label for="productName" class="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
                        <input type="text" id="productName" placeholder="What are you buying?" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label for="originalPrice" class="block text-sm font-medium text-gray-700 mb-2">Seller's Price (₹)</label>
                        <input type="number" id="originalPrice" placeholder="50000" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label for="targetPrice" class="block text-sm font-medium text-gray-700 mb-2">Target Price (₹)</label>
                        <input type="number" id="targetPrice" placeholder="45000" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label for="maxBudget" class="block text-sm font-medium text-gray-700 mb-2">Max Budget (₹)</label>
                        <input type="number" id="maxBudget" placeholder="48000" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label for="personality" class="block text-sm font-medium text-gray-700 mb-2">Agent Personality</label>
                        <select id="personality" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">Choose negotiation style...</option>
                        </select>
                    </div>
                    
                    <div>
                        <label for="tone" class="block text-sm font-medium text-gray-700 mb-2">Conversation Tone</label>
                        <select id="tone" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="friendly">Friendly</option>
                            <option value="professional">Professional</option>
                            <option value="casual">Casual</option>
                        </select>
                    </div>
                </div>
                
                <button onclick="startNegotiation()" 
                        class="mt-6 bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-lg text-lg font-bold transition duration-200">
                    🚀 Start Negotiation
                </button>
            </div>
        </div>

        <!-- Negotiation Phase -->
        <div id="negotiationPhase" class="hidden space-y-6">
            <!-- Status Bar -->
            <div class="bg-white rounded-lg shadow-lg p-4">
                <div class="flex flex-wrap justify-between items-center">
                    <div class="flex space-x-6">
                        <div><span class="font-medium text-gray-600">Session:</span> <span id="sessionId" class="text-blue-600 font-mono">-</span></div>
                        <div><span class="font-medium text-gray-600">Product:</span> <span id="currentProduct" class="text-green-600">-</span></div>
                        <div><span class="font-medium text-gray-600">Original:</span> <span id="currentOriginal" class="text-red-600">-</span></div>
                        <div><span class="font-medium text-gray-600">Target:</span> <span id="currentTarget" class="text-blue-600">-</span></div>
                        <div><span class="font-medium text-gray-600">Current Offer:</span> <span id="currentOffer" class="text-purple-600 font-bold">-</span></div>
                        <div><span class="font-medium text-gray-600">Savings:</span> <span id="potentialSavings" class="text-green-600 font-bold">-</span></div>
                    </div>
                </div>
            </div>

            <!-- Chat Interface -->
            <div class="grid lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">💬 Negotiation Chat</h3>
                        
                        <div id="chatMessages" class="space-y-4 max-h-96 overflow-y-auto mb-4 border rounded-lg p-4 bg-gray-50"></div>
                        
                        <div class="flex space-x-4">
                            <input type="text" id="sellerMessage" placeholder="Enter your message as the seller..." 
                                   disabled class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <button id="sendMessage" onclick="sendSellerMessage()" disabled
                                    class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition duration-200">
                                Send
                            </button>
                        </div>
                        
                        <!-- Quick Seller Messages -->
                        <div class="mt-4 flex flex-wrap gap-2">
                            <button class="quick-seller-msg bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded text-sm" disabled
                                    onclick="setSellerMessage('The price is firm, take it or leave it.')">
                                💪 Firm Price
                            </button>
                            <button class="quick-seller-msg bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded text-sm" disabled
                                    onclick="setSellerMessage('I can give you a small discount, maybe 5%')">
                                💰 Small Discount
                            </button>
                            <button class="quick-seller-msg bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded text-sm" disabled
                                    onclick="setSellerMessage('This is the best condition item, worth every penny')">
                                ⭐ Quality Focus
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Analysis Panel -->
                <div>
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">📊 Analysis</h3>
                        
                        <div class="space-y-4">
                            <div>
                                <span class="block text-sm font-medium text-gray-600">Negotiation Progress</span>
                                <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                                    <div id="progressBar" class="bg-blue-600 h-2 rounded-full" style="width: 0%"></div>
                                </div>
                            </div>
                            
                            <div>
                                <span class="block text-sm font-medium text-gray-600">Agent Strategy</span>
                                <div id="currentStrategy" class="text-sm text-gray-700 mt-1">Analyzing...</div>
                            </div>
                            
                            <div>
                                <span class="block text-sm font-medium text-gray-600">Next Move</span>
                                <div id="nextMove" class="text-sm text-gray-700 mt-1">Preparing...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Notifications -->
        <div id="notifications" class="fixed top-4 right-4 z-50 space-y-2"></div>
    </div>

    <script>
        let currentSession = null;
        let websocket = null;

        // Load personalities on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadPersonalities();
        });

        async function loadPersonalities() {
            try {
                const response = await fetch('/api/personalities');
                const data = await response.json();
                const select = document.getElementById('personality');
                
                // Clear existing options
                select.innerHTML = '<option value="">Choose negotiation style...</option>';
                
                if (data.personalities && data.personalities.length > 0) {
                    data.personalities.forEach(p => {
                        const option = document.createElement('option');
                        option.value = p.value;
                        option.textContent = `${p.label} - ${p.description}`;
                        if (p.value === 'value_seeker') option.selected = true;
                        select.appendChild(option);
                    });
                    console.log(`✅ Loaded ${data.personalities.length} personalities`);
                } else {
                    console.error('No personalities received from API');
                }
            } catch (error) {
                console.error('Error loading personalities:', error);
                showNotification('❌ Failed to load personality options', 'error');
            }
        }

        async function searchProducts() {
            const productName = document.getElementById('productSearch').value.trim();
            const cityLocation = document.getElementById('cityLocation').value.trim();
            
            if (!productName) {
                alert('Please enter a product name or paste a marketplace link');
                return;
            }

            const btn = document.getElementById('searchBtn');
            btn.disabled = true;
            btn.innerHTML = '🔄 Searching...';

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: productName,
                        city: cityLocation
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    displaySearchResults(data);
                    document.getElementById('productName').value = productName;
                } else {
                    showNotification('❌ Search failed. Please try again.', 'error');
                }

            } catch (error) {
                console.error('Search error:', error);
                showNotification('❌ Network error. Please check connection.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔍 Search Sellers';
            }
        }

        function displaySearchResults(data) {
            const resultsDiv = document.getElementById('searchResults');
            const sellers = data.sellers || [];
            
            let html = '<h3 class="text-lg font-bold text-gray-800 mb-4">🎯 Available Sellers</h3>';
            html += '<div class="grid gap-4">';
            
            sellers.forEach((seller, index) => {
                html += `
                    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition duration-200">
                        <div class="flex justify-between items-center">
                            <div>
                                <h4 class="font-bold text-gray-800">${seller.name}</h4>
                                <p class="text-sm text-gray-600">${seller.location || 'Online'}</p>
                                <p class="text-lg font-bold text-green-600">₹${seller.price.toLocaleString()}</p>
                            </div>
                            <button onclick="selectSeller(${index})" 
                                    class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
                                Select
                            </button>
                        </div>
                    </div>`;
            });
            
            html += '</div>';
            resultsDiv.innerHTML = html;
            resultsDiv.classList.remove('hidden');
        }

        function selectSeller(index) {
            const sellers = window.currentSellers || [];
            if (!sellers[index]) return;
            
            const seller = sellers[index];
            document.getElementById('originalPrice').value = seller.price;
            document.getElementById('targetPrice').value = Math.round(seller.price * 0.85);
            document.getElementById('maxBudget').value = Math.round(seller.price * 0.95);
            
            showNotification(`📋 Selected ${seller.name} - ₹${seller.price.toLocaleString()}`, 'success');
            document.getElementById('configSection').scrollIntoView({ behavior: 'smooth' });
        }

        async function startNegotiation() {
            const config = {
                product: document.getElementById('productName').value.trim(),
                original_price: document.getElementById('originalPrice').value,
                target_price: document.getElementById('targetPrice').value,
                max_budget: document.getElementById('maxBudget').value,
                personality: document.getElementById('personality').value,
                tone: document.getElementById('tone').value
            };

            if (!config.product) {
                alert('Please enter a product name');
                return;
            }

            try {
                const response = await fetch('/api/create-session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                currentSession = data.session_id;
                
                // Switch to negotiation phase
                document.getElementById('setupPhase').classList.add('hidden');
                document.getElementById('negotiationPhase').classList.remove('hidden');
                
                // Update UI
                document.getElementById('sessionId').textContent = currentSession;
                document.getElementById('currentProduct').textContent = config.product;
                document.getElementById('currentOriginal').textContent = `₹${parseInt(config.original_price).toLocaleString()}`;
                document.getElementById('currentTarget').textContent = `₹${parseInt(config.target_price).toLocaleString()}`;
                
                // Enable chat
                document.getElementById('sellerMessage').disabled = false;
                document.getElementById('sendMessage').disabled = false;
                document.querySelectorAll('.quick-seller-msg').forEach(btn => btn.disabled = false);
                
                // Add initial message
                addMessageToChat('system', '🚀 Negotiation started! Enter your first message as the seller.', 'System');

            } catch (error) {
                console.error('Error starting negotiation:', error);
                alert('Failed to start negotiation');
            }
        }

        async function sendSellerMessage() {
            const messageInput = document.getElementById('sellerMessage');
            const message = messageInput.value.trim();
            
            if (!message || !currentSession) return;

            // Add seller message to chat
            addMessageToChat('seller', message, 'Seller (You)');
            messageInput.value = '';

            // Show agent thinking
            const thinkingId = addMessageToChat('agent', 'Thinking...', 'Agent (Buyer)', true);

            try {
                const response = await fetch('/api/send-message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: currentSession,
                        message: message
                    })
                });

                const data = await response.json();
                
                // Remove thinking message
                document.getElementById(thinkingId).remove();
                
                if (data.error) {
                    addMessageToChat('system', `Error: ${data.error}`, 'System');
                    return;
                }
                
                // Add agent response
                addMessageToChat('agent', data.response, 'Agent (Buyer)');

            } catch (error) {
                console.error('Error sending message:', error);
                document.getElementById(thinkingId).remove();
                addMessageToChat('system', 'Error getting agent response. Please try again.', 'System');
            }
        }

        function addMessageToChat(type, message, sender, isTemporary = false) {
            const chatMessages = document.getElementById('chatMessages');
            const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = `message-bubble flex ${type === 'seller' ? 'justify-end' : 'justify-start'}`;
            
            let bgClass = 'bg-gray-200';
            if (type === 'seller') bgClass = 'seller-message text-white';
            else if (type === 'agent') bgClass = 'agent-message text-white';
            else if (type === 'system') bgClass = 'bg-yellow-100 text-yellow-800';
            
            messageDiv.innerHTML = `
                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${bgClass}">
                    <div class="text-xs opacity-75 mb-1">${sender}</div>
                    <div class="text-sm">${message}</div>
                    <div class="text-xs opacity-50 mt-1">${new Date().toLocaleTimeString()}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            return messageId;
        }

        function setSellerMessage(message) {
            document.getElementById('sellerMessage').value = message;
        }

        function showNotification(message, type = 'info') {
            const notifications = document.getElementById('notifications');
            const notification = document.createElement('div');
            
            let bgClass = 'bg-blue-500';
            if (type === 'success') bgClass = 'bg-green-500';
            else if (type === 'error') bgClass = 'bg-red-500';
            else if (type === 'warning') bgClass = 'bg-yellow-500';
            
            notification.className = `${bgClass} text-white px-4 py-2 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
            notification.textContent = message;
            
            notifications.appendChild(notification);
            
            // Animate in
            setTimeout(() => notification.classList.remove('translate-x-full'), 100);
            
            // Auto remove
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }

        // Allow Enter key to send message
        document.getElementById('sellerMessage').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendSellerMessage();
            }
        });
    </script>
</body>
</html>"""

    def _extract_product_from_link(self, url: str) -> str:
        """Extract product name from marketplace URL"""
        try:
            import re
            # Mock extraction - in real implementation, you'd scrape the page
            if "olx.in" in url.lower():
                # Extract from OLX URL pattern
                match = re.search(r'/([^/]+)-iid-', url)
                if match:
                    product = match.group(1).replace('-', ' ').title()
                    return product
            
            # Fallback: extract from URL path
            path = url.split('/')[-1]
            product = re.sub(r'[^a-zA-Z0-9\s]', ' ', path).strip().title()
            return product[:50]  # Limit length
            
        except Exception:
            return "Product from Link"
    
    def _find_sellers_with_location(self, product: str, city: str) -> List[Dict]:
        """Find sellers based on product and city location"""
        base_sellers = self._mock_seller_search(product)
        
        # Enhance with location-specific sellers
        if city.lower() in ['mumbai', 'delhi', 'bangalore', 'pune', 'chennai', 'kolkata', 'hyderabad']:
            # Add local marketplace sellers
            local_sellers = [
                {
                    "name": f"Local Electronics {city}",
                    "price": base_sellers[0]["price"] - random.randint(2000, 5000),
                    "rating": 4.2,
                    "location": city,
                    "type": "Local Store",
                    "delivery": "Same Day"
                },
                {
                    "name": f"OLX Seller - {city}",
                    "price": base_sellers[0]["price"] - random.randint(1000, 3000),
                    "rating": 4.0,
                    "location": city,
                    "type": "Individual Seller",
                    "delivery": "Pickup/Meet"
                }
            ]
            
            # Add location info to existing sellers
            for seller in base_sellers:
                if city.lower() in ['mumbai', 'delhi', 'bangalore']:
                    seller["delivery"] = "Next Day"
                else:
                    seller["delivery"] = "2-3 Days"
                seller["location"] = f"Ships to {city}"
            
            return local_sellers + base_sellers[:3]  # Limit to 5 total
        
        return base_sellers
    
    def _mock_seller_search(self, product: str) -> List[Dict]:
        """Mock seller search for demonstration"""
        logger.info(f"🔍 Mock search for product: {product}")
        
        # Determine base price based on product type
        product_lower = product.lower()
        if "iphone" in product_lower:
            base_price = 85000
        elif "laptop" in product_lower or "macbook" in product_lower:
            base_price = 120000
        elif "phone" in product_lower or "mobile" in product_lower:
            base_price = 35000
        elif "tv" in product_lower or "television" in product_lower:
            base_price = 45000
        else:
            base_price = 50000
        
        sellers = [
            {"name": "TechMart Online", "price": base_price, "rating": 4.5, "verified": True, "delivery": "2-3 Days", "type": "Online Store"},
            {"name": "ElectroWorld", "price": base_price + 2500, "rating": 4.2, "verified": True, "delivery": "Next Day", "type": "Electronics Store"},
            {"name": "GadgetHub", "price": base_price - 2000, "rating": 4.7, "verified": False, "delivery": "3-5 Days", "type": "Local Dealer"},
            {"name": "MegaElectronics", "price": base_price + 4000, "rating": 4.0, "verified": True, "delivery": "Same Day", "type": "Premium Store"},
            {"name": "QuickBuy Store", "price": base_price - 3000, "rating": 4.3, "verified": True, "delivery": "Next Day", "type": "Discount Store"}
        ]
        
        logger.info(f"📋 Found {len(sellers)} sellers for {product}")
        return sellers

    def _generate_mock_response(self, seller_message: str, session: dict) -> str:
        """Generate mock AI responses for demonstration"""
        seller_msg = seller_message.lower()
        config = session["config"]
        personality = config["personality"]
        target_price = config["target_price"]
        max_budget = config["max_budget"]
        
        # Mock responses based on seller message content
        if "price" in seller_msg and any(char.isdigit() for char in seller_msg):
            # Extract price from seller message
            prices = re.findall(r'[\d,]+', seller_message.replace(',', ''))
            if prices:
                seller_price = int(prices[0])
                
                if seller_price <= target_price:
                    return f"That's a great price! ₹{seller_price:,} works perfectly for me. When can we close this deal?"
                elif seller_price <= max_budget:
                    counter = max(target_price, seller_price - 5000)
                    return f"I appreciate the offer of ₹{seller_price:,}. Would you consider ₹{counter:,}? That would be perfect for my budget."
                else:
                    counter = min(max_budget, seller_price - 10000)
                    return f"₹{seller_price:,} is a bit high for me. I was thinking more around ₹{counter:,}. Can we work something out?"
        
        # Personality-based responses
        if personality == "aggressive_bargainer":
            responses = [
                "That's too expensive. I can get this cheaper elsewhere. What's your best price?",
                "I need a much better deal than that. Can you do significantly better?",
                "I'm a serious buyer but that price won't work. What's your rock-bottom price?"
            ]
        elif personality == "diplomatic_negotiator":
            responses = [
                "I appreciate your offer. Would you be open to discussing a more mutually beneficial price?",
                "Thank you for that. I was hoping for something a bit more reasonable. What do you think?",
                "I understand your position. Could we explore some middle ground that works for both of us?"
            ]
        elif personality == "budget_conscious":
            responses = [
                "I'm on a tight budget. Is there any way you could help me out with the pricing?",
                "That's beyond my budget. Do you have any room for negotiation?",
                "I really need to stick to my budget. What's the lowest you can go?"
            ]
        else:
            responses = [
                "That's interesting. Let me think about that offer.",
                "I see. Could you help me understand the value better?",
                "Thanks for sharing that. What are my options here?"
            ]
        
        return random.choice(responses)

    def run(self, host: str = "localhost", port: int = 8000):
        """Run the web application"""
        create_negotiation_template()
        print(f"🚀 Starting AI Buyer Negotiation Web App...")
        print(f"📱 Dashboard: http://{host}:{port}")
        print(f"🔧 API Docs: http://{host}:{port}/docs")
        
        uvicorn.run(self.app, host=host, port=port)

def create_negotiation_template():
    """Create the main negotiation dashboard template"""
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
        .seller-message { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
        .agent-message { background: linear-gradient(135deg, #4834d4, #686de0); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <nav class="gradient-bg text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <h1 class="text-2xl font-bold">🛒 AI Buyer Negotiation Agent</h1>
                <div class="text-sm">Agent negotiates as buyer with seller (you)</div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        
        <!-- Setup Phase -->
        <div id="setupPhase" class="space-y-6">
            
            <!-- Product Search -->
                        <div class="bg-white rounded-lg shadow-sm p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">🔍 Find Products & Sellers</h2>
                <div class="space-y-4">
                    <div class="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                        <input type="text" id="productSearch" placeholder="Enter product name or paste OLX/marketplace link (e.g., iPhone 13 Pro)" 
                               class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 px-3 py-2">
                        <input type="text" id="cityLocation" placeholder="Your City (e.g., Mumbai, Delhi)" 
                               class="w-full sm:w-48 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 px-3 py-2">
                        <button id="searchBtn" class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2 rounded-md hover:from-blue-700 hover:to-purple-700 font-semibold transition-all duration-200">
                            🔍 Search Sellers
                        </button>
                    </div>
                    <p class="text-sm text-gray-600">💡 <strong>Tips:</strong> Paste OLX links for instant product detection • Enter your city for local sellers • Try "iPhone 13 Pro Mumbai" for best results</p>
                </div>
            </div>

            <!-- Configuration -->
            <div class="bg-white card-shadow rounded-lg p-6">
                <h2 class="text-xl font-bold text-gray-900 mb-4">⚙️ Step 2: Configure Negotiation</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
                        <input type="text" id="productName" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Original Price (₹)</label>
                        <input type="number" id="originalPrice" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="90000">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Target Price (₹)</label>
                        <input type="number" id="targetPrice" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="75000">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Max Budget (₹)</label>
                        <input type="number" id="maxBudget" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value="85000">
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Agent Personality</label>
                        <select id="personality" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                            <!-- Will be populated by JavaScript -->
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Negotiation Tone</label>
                        <select id="tone" class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                            <option value="professional">Professional</option>
                            <option value="friendly">Friendly</option>
                            <option value="assertive">Assertive</option>
                            <option value="diplomatic">Diplomatic</option>
                        </select>
                    </div>
                </div>
                
                <button id="startNegotiation" class="mt-4 w-full bg-green-600 text-white py-3 px-6 rounded-md hover:bg-green-700 font-bold text-lg">
                    🚀 Start Negotiation
                </button>
            </div>
        </div>

        <!-- Negotiation Phase -->
        <div id="negotiationPhase" class="hidden">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <!-- Chat Interface -->
                <div class="lg:col-span-2">
                    <div class="bg-white card-shadow rounded-lg">
                        <!-- Chat Header -->
                        <div class="border-b border-gray-200 p-4">
                            <div class="flex justify-between items-center">
                                <h2 class="text-lg font-bold text-gray-900">💬 Negotiation Chat</h2>
                                <div id="negotiationStatus" class="text-sm font-medium px-3 py-1 rounded-full bg-green-100 text-green-800">
                                    Active
                                </div>
                            </div>
                            <div id="sessionInfo" class="text-sm text-gray-500 mt-1">
                                Session: <span id="sessionId">-</span>
                            </div>
                        </div>
                        
                        <!-- Chat Messages -->
                        <div id="chatMessages" class="h-96 overflow-y-auto p-4 space-y-4">
                            <div class="text-center text-gray-500 py-8">
                                Negotiation will start here...
                            </div>
                        </div>
                        
                        <!-- Chat Input -->
                        <div class="border-t border-gray-200 p-4">
                            <div class="flex space-x-4">
                                <input type="text" id="sellerMessage" placeholder="Enter your message as the seller..." 
                                       class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" disabled>
                                <button id="sendMessage" class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 font-semibold" disabled>
                                    Send
                                </button>
                            </div>
                            <div class="mt-3 flex flex-wrap gap-2">
                                <button class="quick-seller-msg bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm hover:bg-orange-200" disabled>
                                    "Price is ₹85,000"
                                </button>
                                <button class="quick-seller-msg bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm hover:bg-orange-200" disabled>
                                    "Best I can do is ₹80,000"
                                </button>
                                <button class="quick-seller-msg bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm hover:bg-orange-200" disabled>
                                    "This is my final offer"
                                </button>
                                <button class="quick-seller-msg bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm hover:bg-orange-200" disabled>
                                    "Deal!"
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Analytics Panel -->
                <div class="space-y-6">
                    
                    <!-- Current Deal -->
                    <div class="bg-white card-shadow rounded-lg p-6">
                        <h3 class="text-lg font-bold text-gray-900 mb-4">📊 Current Deal</h3>
                        <div id="dealInfo" class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-600">Product:</span>
                                <span id="currentProduct" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Original Price:</span>
                                <span id="currentOriginal" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Target Price:</span>
                                <span id="currentTarget" class="font-medium text-green-600">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Current Offer:</span>
                                <span id="currentOffer" class="font-medium text-blue-600">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Potential Savings:</span>
                                <span id="potentialSavings" class="font-bold text-green-600">-</span>
                            </div>
                        </div>
                    </div>

                    <!-- Negotiation Analytics -->
                    <div class="bg-white card-shadow rounded-lg p-6">
                        <h3 class="text-lg font-bold text-gray-900 mb-4">📈 Analytics</h3>
                        <div id="analyticsInfo" class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-600">Phase:</span>
                                <span id="currentPhase" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Round:</span>
                                <span id="currentRound" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Messages:</span>
                                <span id="messageCount" class="font-medium">-</span>
                            </div>
                        </div>
                    </div>

                    <!-- Tactics Panel -->
                    <div class="bg-white card-shadow rounded-lg p-6">
                        <h3 class="text-lg font-bold text-gray-900 mb-4">🎯 AI Tactics</h3>
                        <div id="tacticsInfo" class="text-sm text-gray-600">
                            Tactics will appear as negotiation progresses...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSession = null;
        let websocket = null;
        let currentSessionId = null;

        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
            
            // Style based on type
            if (type === 'success') {
                notification.className += ' bg-green-100 border-green-500 text-green-700';
            } else if (type === 'error') {
                notification.className += ' bg-red-100 border-red-500 text-red-700';
            } else {
                notification.className += ' bg-blue-100 border-blue-500 text-blue-700';
            }
            
            notification.innerHTML = `
                <div class="flex items-center">
                    <div class="mr-2">${message}</div>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-lg">&times;</button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Slide in
            setTimeout(() => {
                notification.style.transform = 'translateX(0)';
            }, 100);
            
            // Auto remove after 4 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.transform = 'translateX(full)';
                    setTimeout(() => notification.remove(), 300);
                }
            }, 4000);
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            loadPersonalities();
        });

        function setupEventListeners() {
            document.getElementById('searchBtn').addEventListener('click', searchProducts);
            document.getElementById('startNegotiation').addEventListener('click', startNegotiation);
            document.getElementById('sendMessage').addEventListener('click', sendSellerMessage);
            document.getElementById('sellerMessage').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendSellerMessage();
            });

            // Quick message buttons
            document.querySelectorAll('.quick-seller-msg').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.getElementById('sellerMessage').value = this.textContent.replace(/"/g, '');
                    sendSellerMessage();
                });
            });
        }

        async function loadPersonalities() {
            try {
                console.log('Loading personalities...');
                const response = await fetch('/api/personalities');
                console.log('Personalities response:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Personalities data:', data);
                
                const select = document.getElementById('personality');
                if (!select) {
                    console.error('Personality select element not found!');
                    return;
                }
                
                // Clear existing options
                select.innerHTML = '<option value="">Choose negotiation style...</option>';
                
                if (data.personalities && data.personalities.length > 0) {
                    data.personalities.forEach(p => {
                        const option = document.createElement('option');
                        option.value = p.value;
                        option.textContent = `${p.label} - ${p.description}`;
                        if (p.value === 'value_seeker') option.selected = true;
                        select.appendChild(option);
                    });
                    console.log(`✅ Loaded ${data.personalities.length} personalities`);
                } else {
                    console.error('No personalities received from API');
                }
            } catch (error) {
                console.error('Error loading personalities:', error);
                showNotification('❌ Failed to load personality options', 'error');
            }
        }

        async function searchProducts() {
            const productName = document.getElementById('productSearch').value.trim();
            const cityLocation = document.getElementById('cityLocation').value.trim();
            
            console.log('🔍 Search initiated:', {productName, cityLocation});
            
            if (!productName) {
                alert('Please enter a product name or paste a marketplace link');
                return;
            }

            const btn = document.getElementById('searchBtn');
            btn.disabled = true;
            btn.innerHTML = '🔄 Searching...';

            try {
                const searchData = {
                    query: productName,
                    city: cityLocation
                };
                
                console.log('📤 Sending search request:', searchData);
                
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(searchData)
                });

                console.log('📥 Search response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('📋 Search results:', data);
                
                if (data.success) {
                    if (data.link_processed) {
                        showNotification(`🔗 Processed: ${data.product_detected}`, 'success');
                        document.getElementById('productName').value = data.product_detected;
                    } else {
                        document.getElementById('productName').value = productName;
                    }
                    
                    displaySearchResults(data);
                    
                    if (cityLocation && data.sellers && data.sellers.length > 0) {
                        showNotification(`🏙️ Found ${data.sellers.length} sellers in ${cityLocation}`, 'info');
                    } else if (cityLocation) {
                        showNotification(`⚠️ No local sellers found in ${cityLocation}, showing online sellers`, 'info');
                    }
                } else {
                    console.error('Search failed:', data);
                    showNotification('❌ Search failed. Please try again.', 'error');
                }
                
                // Auto-populate product name
                if (!document.getElementById('productName').value) {
                    document.getElementById('productName').value = productName;
                }

            } catch (error) {
                console.error('Search error:', error);
                showNotification('❌ Network error. Please check connection.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔍 Search Sellers';
            }
        }

        function displaySearchResults(data) {
            const resultsDiv = document.getElementById('searchResults');
            
            // Handle new API format
            const sellers = data.sellers || [];
            const productName = data.product_detected || document.getElementById('productSearch').value;
            
            if (sellers.length === 0) {
                resultsDiv.innerHTML = '<div class="text-center text-gray-500 py-4">No sellers found</div>';
                resultsDiv.classList.remove('hidden');
                return;
            }

            let html = '<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">';
            html += `<h3 class="font-bold text-blue-900 mb-3">Found ${sellers.length} sellers for "${productName}"</h3>`;
            
            html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">';
            sellers.forEach((seller, index) => {
                const bgColor = index === 0 ? 'bg-green-100 border-green-300' : 'bg-white border-gray-200';
                const badge = index === 0 ? '<span class="bg-green-500 text-white text-xs px-2 py-1 rounded-full ml-2">Best Price</span>' : '';
                
                html += `
                    <div class="${bgColor} border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="font-semibold text-gray-900">${seller.name}${badge}</div>
                                <div class="flex items-center mt-1">
                                    <span class="text-yellow-500">${'★'.repeat(Math.floor(seller.rating))}</span>
                                    <span class="text-gray-500 text-sm ml-1">${seller.rating}/5</span>
                                    ${seller.verified ? '<span class="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">✓ Verified</span>' : ''}
                                </div>
                                ${seller.location ? `<div class="text-xs text-gray-600 mt-1">📍 ${seller.location}</div>` : ''}
                                ${seller.delivery ? `<div class="text-xs text-gray-500 mt-1">🚚 ${seller.delivery}</div>` : ''}
                            </div>
                            <div class="text-right">
                                <div class="text-xl font-bold text-blue-600">₹${seller.price.toLocaleString()}</div>
                                ${seller.type ? `<div class="text-xs text-gray-500">${seller.type}</div>` : ''}
                            </div>
                        </div>
                        <button onclick="selectSeller(${index})" class="mt-3 w-full bg-blue-600 text-white py-2 px-3 rounded hover:bg-blue-700 transition-colors text-sm">
                            Select & Configure
                        </button>
                    </div>
                `;
            });
            html += '</div>';

            if (data.market_data) {
            });
            html += '</div>';

            // Add market analysis if available
            if (sellers.length > 2) {
                const prices = sellers.map(s => s.price);
                const avgPrice = Math.round(prices.reduce((a, b) => a + b, 0) / prices.length);
                const minPrice = Math.min(...prices);
                const maxPrice = Math.max(...prices);
                
                html += '<div class="mt-4 pt-3 border-t border-blue-200">';
                html += '<div class="text-sm text-blue-700 grid grid-cols-3 gap-4 text-center">';
                html += `<div>Avg: ₹${avgPrice.toLocaleString()}</div>`;
                html += `<div>Best: ₹${minPrice.toLocaleString()}</div>`;
                html += `<div>High: ₹${maxPrice.toLocaleString()}</div>`;
                html += '</div></div>';
            }
            
            html += '</div>';
            
            resultsDiv.innerHTML = html;
            resultsDiv.classList.remove('hidden');
            
            // Store sellers data for selection
            window.currentSellers = sellers;
        }
        
        function selectSeller(index) {
            if (!window.currentSellers || !window.currentSellers[index]) {
                alert('Seller not found');
                return;
            }
            
            const seller = window.currentSellers[index];
            
            // Auto-populate configuration form
            document.getElementById('originalPrice').value = seller.price;
            document.getElementById('targetPrice').value = Math.round(seller.price * 0.85); // 15% discount target
            document.getElementById('maxBudget').value = Math.round(seller.price * 0.95); // 5% buffer
            
            // Show notification
            showNotification(`📋 Selected ${seller.name} - ₹${seller.price.toLocaleString()}`, 'success');
            
            // Scroll to configuration section
            document.getElementById('configSection').scrollIntoView({ behavior: 'smooth' });
            document.getElementById('configSection').style.display = 'block';
        }            html += '</div>';
            resultsDiv.innerHTML = html;
            resultsDiv.classList.remove('hidden');
        }

        async function startNegotiation() {
            const config = {
                product: document.getElementById('productName').value.trim(),
                original_price: document.getElementById('originalPrice').value,
                target_price: document.getElementById('targetPrice').value,
                max_budget: document.getElementById('maxBudget').value,
                personality: document.getElementById('personality').value,
                tone: document.getElementById('tone').value
            };

            if (!config.product) {
                alert('Please enter a product name');
                return;
            }

            try {
                const response = await fetch('/api/create-session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                currentSession = data.session_id;
                
                // Switch to negotiation phase
                document.getElementById('setupPhase').classList.add('hidden');
                document.getElementById('negotiationPhase').classList.remove('hidden');
                
                // Update UI
                document.getElementById('sessionId').textContent = currentSession;
                document.getElementById('currentProduct').textContent = config.product;
                document.getElementById('currentOriginal').textContent = `₹${parseInt(config.original_price).toLocaleString()}`;
                document.getElementById('currentTarget').textContent = `₹${parseInt(config.target_price).toLocaleString()}`;
                document.getElementById('currentOffer').textContent = 'Waiting...';
                document.getElementById('potentialSavings').textContent = 'TBD';
                
                // Enable chat
                document.getElementById('sellerMessage').disabled = false;
                document.getElementById('sendMessage').disabled = false;
                document.querySelectorAll('.quick-seller-msg').forEach(btn => btn.disabled = false);
                
                // Setup WebSocket
                setupWebSocket();
                
                // Add initial message
                addMessageToChat('system', '🚀 Negotiation started! Enter your first message as the seller.', 'System');

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
                if (data.type === 'new_message') {
                    updateAnalytics(data.analysis);
                    updateNegotiationStatus(data.negotiation_status);
                }
            };
        }

        async function sendSellerMessage() {
            const message = document.getElementById('sellerMessage').value.trim();
            if (!message || !currentSession) return;

            // Add seller message to chat
            addMessageToChat('seller', message, 'You (Seller)');
            document.getElementById('sellerMessage').value = '';

            // Show agent thinking
            const thinkingId = addMessageToChat('agent', 'Thinking and analyzing...', 'Agent (Buyer)', true);

            try {
                const response = await fetch('/api/send-message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: currentSession,
                        message: message
                    })
                });

                const data = await response.json();
                
                // Remove thinking message
                document.getElementById(thinkingId).remove();
                
                if (data.error) {
                    addMessageToChat('system', `Error: ${data.error}`, 'System');
                    return;
                }
                
                // Add agent response - backend returns 'response' field
                addMessageToChat('agent', data.response, 'Agent (Buyer)');
                
                // Update analytics (with fallbacks for missing data)
                updateAnalytics(data.analysis || {});
                updateNegotiationStatus(data.negotiation_status || {});
                updateTactics(data.tactics || []);

            } catch (error) {
                console.error('Error sending message:', error);
                document.getElementById(thinkingId).remove();
                addMessageToChat('system', 'Error getting agent response. Please try again.', 'System');
            }
        }

        function addMessageToChat(role, message, sender, isTemporary = false) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = isTemporary ? 'temp-' + Date.now() : null;
            
            if (messageId) messageDiv.id = messageId;
            
            messageDiv.className = `message-bubble ${role === 'seller' ? 'text-right' : 'text-left'}`;
            
            const bubble = document.createElement('div');
            bubble.className = `inline-block max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                role === 'seller' 
                    ? 'seller-message text-white' 
                    : role === 'agent'
                    ? 'agent-message text-white'
                    : 'bg-gray-200 text-gray-700'
            }`;
            
            const icon = role === 'seller' ? '💼' : role === 'agent' ? '🤖' : '📢';
            bubble.innerHTML = `<div class="font-semibold text-sm mb-1">${icon} ${sender}</div><div>${message}</div>`;
            
            messageDiv.appendChild(bubble);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            return messageId;
        }

        function updateAnalytics(analysis) {
            if (!analysis) return;
            
            document.getElementById('currentPhase').textContent = analysis.phase.replace('_', ' ').toUpperCase();
            document.getElementById('currentRound').textContent = analysis.round;
            document.getElementById('messageCount').textContent = analysis.round * 2;
            
            if (analysis.seller_price > 0) {
                document.getElementById('currentOffer').textContent = `₹${analysis.seller_price.toLocaleString()}`;
                const savings = analysis.seller_price - analysis.target_price;
                document.getElementById('potentialSavings').textContent = `₹${Math.max(0, savings).toLocaleString()}`;
            }
        }

        function updateNegotiationStatus(status) {
            const statusDiv = document.getElementById('negotiationStatus');
            statusDiv.textContent = status;
            
            // Update status color
            statusDiv.className = 'text-sm font-medium px-3 py-1 rounded-full ';
            if (status.includes('target')) {
                statusDiv.className += 'bg-green-100 text-green-800';
            } else if (status.includes('budget')) {
                statusDiv.className += 'bg-yellow-100 text-yellow-800';
            } else if (status.includes('above')) {
                statusDiv.className += 'bg-red-100 text-red-800';
            } else {
                statusDiv.className += 'bg-blue-100 text-blue-800';
            }
        }

        function updateTactics(tactics) {
            const tacticsDiv = document.getElementById('tacticsInfo');
            if (tactics && tactics.trim()) {
                // Parse tactics and format nicely
                const lines = tactics.split('\n').filter(line => line.trim());
                let formattedTactics = '';
                
                lines.forEach(line => {
                    if (line.includes('🎯') || line.includes('📊') || line.includes('💰') || line.includes('🤝')) {
                        formattedTactics += `<div class="mb-2 p-2 bg-blue-50 rounded text-sm">${line}</div>`;
                    }
                });
                
                tacticsDiv.innerHTML = formattedTactics || tactics;
            }
        }
    </script>
</body>
</html>
    """
    
    Path("templates").mkdir(exist_ok=True)
    with open("templates/negotiation_dashboard.html", "w") as f:
        f.write(html_content)

def create_web_app():
    """Create and return web app instance"""
    return NegotiationWebApp()

if __name__ == "__main__":
    app = create_web_app()
    app.run()