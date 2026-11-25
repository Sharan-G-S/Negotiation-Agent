"""
Web Client for AI Negotiation Agent
Connects to the main backend server for real agent interactions
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import httpx

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NegotiationWebClient:
    """Web client that connects to the main backend server"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        """Initialize the web client application"""
        self.app = FastAPI(
            title="AI Negotiation Agent - Web Client",
            description="Web interface that connects to the main negotiation backend",
            version="2.0.0"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Backend configuration
        self.backend_url = backend_url.rstrip('/')
        
        # Application state for frontend
        self.websocket_connections = {}
        
        # Setup routes
        self.setup_routes()
        
        print(f"🔗 Web client initialized - connecting to backend: {self.backend_url}")
    
    def setup_routes(self):
        """Setup all web application routes"""
        
        @self.app.get("/")
        async def home():
            """Serve the main web interface"""
            return HTMLResponse(self.get_main_page())
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check that also checks backend connectivity"""
            try:
                async with httpx.AsyncClient() as client:
                    backend_response = await client.get(f"{self.backend_url}/api/health")
                    backend_healthy = backend_response.status_code == 200
                    backend_data = backend_response.json() if backend_healthy else {}
            except Exception as e:
                backend_healthy = False
                backend_data = {"error": str(e)}
            
            return {
                "status": "healthy",
                "frontend": "running", 
                "backend": "connected" if backend_healthy else "disconnected",
                "backend_url": self.backend_url,
                "backend_data": backend_data
            }
        
        @self.app.get("/api/personalities")
        async def get_personalities():
            """Get available buyer personalities from backend"""
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.backend_url}/api/personalities")
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Error fetching personalities from backend: {e}")
            
            # Fallback personalities if backend not available
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
        async def search_products(request: dict):
            """Search for products - proxy to backend or mock implementation"""
            try:
                # First try to use backend search if available
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.backend_url}/api/search", 
                        json=request
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Backend search failed: {e}")
            
            # Mock search results if backend not available
            product_name = request.get('product', '').lower()
            city = request.get('city', 'Mumbai')
            
            mock_results = self.get_mock_search_results(product_name, city)
            return {
                "success": True,
                "results": mock_results,
                "total": len(mock_results),
                "city": city,
                "mock_mode": True
            }
        
        @self.app.post("/api/negotiate-product")
        async def start_negotiation(request: dict):
            """Start negotiation with backend server"""
            try:
                # Forward request to backend
                async with httpx.AsyncClient() as client:
                    # Use demo negotiate endpoint as it's available in backend
                    negotiation_request = {
                        "product_url": f"demo://{request.get('product', 'product')}",
                        "target_price": request.get('target_price', 10000),
                        "max_budget": request.get('max_budget', 15000),
                        "approach": request.get('personality', 'diplomatic').lower(),
                        "timeline": request.get('timeline', 'flexible'),
                        "special_requirements": request.get('requirements')
                    }
                    
                    response = await client.post(
                        f"{self.backend_url}/api/demo-negotiate",
                        json=negotiation_request,
                        headers={"Authorization": "Bearer demo_token"}  # For demo
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "success": True,
                            "session_id": result.get("session", {}).get("session_id"),
                            "product_info": result.get("product_info", {}),
                            "message": "Connected to AI negotiation agent!",
                            "backend_response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Backend error: {response.status_code}",
                            "message": "Could not connect to negotiation backend"
                        }
                        
            except Exception as e:
                print(f"Error starting negotiation: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to connect to negotiation backend"
                }
        
        @self.app.post("/api/send-message")
        async def send_message(request: dict):
            """Send seller message to backend for AI response"""
            try:
                session_id = request.get('session_id')
                message = request.get('message', '')
                
                if not session_id or not message:
                    return {"error": "Session ID and message required"}
                
                # Forward to backend
                async with httpx.AsyncClient() as client:
                    backend_request = {
                        "session_id": session_id,
                        "message": message
                    }
                    
                    response = await client.post(
                        f"{self.backend_url}/api/seller-response",
                        json=backend_request
                    )
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "response": "Message processed by AI agent",
                            "backend_response": response.json()
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Backend error: {response.status_code}",
                            "response": "Could not process message through backend"
                        }
                        
            except Exception as e:
                print(f"Error sending message: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "response": "Failed to connect to negotiation backend"
                }
        
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time updates - connects to backend WebSocket"""
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                # For now, keep connection alive and handle basic communication
                while True:
                    try:
                        # Listen for frontend messages
                        data = await websocket.receive_text()
                        message_data = json.loads(data)
                        
                        # Forward to backend if needed
                        # For now, just acknowledge
                        await websocket.send_text(json.dumps({
                            "type": "ack",
                            "message": "WebSocket connected"
                        }))
                        
                    except WebSocketDisconnect:
                        break
                        
            except WebSocketDisconnect:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
            except Exception as e:
                print(f"WebSocket error: {e}")
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
    
    def get_mock_search_results(self, product_name: str, city: str) -> List[dict]:
        """Generate mock search results"""
        base_products = [
            {"name": "iPhone 14 Pro", "price": 65000, "seller": "TechStore", "location": "Electronics Market"},
            {"name": "MacBook Air M2", "price": 85000, "seller": "AppleWorld", "location": "Tech Hub"},
            {"name": "Samsung Galaxy S23", "price": 55000, "seller": "MobileZone", "location": "Phone Market"},
            {"name": "Dell XPS 13", "price": 75000, "seller": "LaptopCenter", "location": "Computer Mall"},
            {"name": "iPad Air", "price": 45000, "seller": "TabletWorld", "location": "Electronics Plaza"}
        ]
        
        # Filter and modify based on search query
        results = []
        for product in base_products:
            if not product_name or product_name in product["name"].lower():
                result = {
                    "id": f"prod_{len(results) + 1}",
                    "title": product["name"],
                    "price": product["price"],
                    "originalPrice": int(product["price"] * 1.2),
                    "seller": product["seller"],
                    "location": f"{product['location']}, {city}",
                    "condition": "Excellent",
                    "description": f"{product['name']} in excellent condition",
                    "images": ["https://via.placeholder.com/300x200?text=Product+Image"]
                }
                results.append(result)
        
        return results[:5]  # Limit to 5 results
    
    def get_main_page(self) -> str:
        """Generate the main web page HTML"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Negotiation Agent - Connected to Backend</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .chat-bubble-user { background: #3B82F6; color: white; margin-left: auto; }
        .chat-bubble-agent { background: #E5E7EB; color: #1F2937; margin-right: auto; }
        .notification { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div id="notification" class="notification hidden"></div>

    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold">🤖 AI Negotiation Agent (Connected)</h1>
                <div class="flex items-center space-x-4">
                    <div id="connectionStatus" class="flex items-center space-x-2">
                        <div class="w-3 h-3 rounded-full bg-yellow-400"></div>
                        <span class="text-sm">Checking backend...</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <div class="container mx-auto px-6 py-8">
        <div class="max-w-6xl mx-auto">
            <!-- Setup Phase -->
            <div id="setupPhase" class="space-y-8">
                <!-- Instructions -->
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <h2 class="text-lg font-semibold text-blue-800 mb-2">🔗 Connected to Main Backend</h2>
                    <p class="text-blue-700">This web interface connects to your main negotiation backend server for real AI agent interactions.</p>
                </div>

                <!-- Product Search -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">🔍 Find Your Product</h2>
                    
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
                            <input type="text" id="productSearch" placeholder="e.g., iPhone 14, MacBook Pro" 
                                   class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">City</label>
                            <input type="text" id="citySearch" placeholder="e.g., Mumbai, Delhi, Bangalore" value="Mumbai"
                                   class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>
                    
                    <button onclick="searchProducts()" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium">
                        🔍 Search Products
                    </button>
                    
                    <div id="searchResults" class="mt-6 hidden">
                        <h3 class="text-lg font-medium mb-4 text-gray-800">Search Results</h3>
                        <div id="productsList" class="grid md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
                    </div>
                </div>

                <!-- Agent Configuration -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">🤖 Configure Your AI Agent</h2>
                    
                    <div class="grid md:grid-cols-2 gap-6">
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Selected Product</label>
                                <div id="selectedProduct" class="p-3 bg-gray-50 rounded-md text-gray-500">
                                    No product selected
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Agent Personality</label>
                                <select id="agentPersonality" class="w-full px-4 py-2 border border-gray-300 rounded-md">
                                    <option value="">Loading personalities...</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Target Price (₹)</label>
                                <input type="number" id="targetPrice" placeholder="e.g., 45000" 
                                       class="w-full px-4 py-2 border border-gray-300 rounded-md">
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Maximum Budget (₹)</label>
                                <input type="number" id="maxBudget" placeholder="e.g., 50000" 
                                       class="w-full px-4 py-2 border border-gray-300 rounded-md">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6">
                        <button onclick="startNegotiation()" id="startBtn"
                                class="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-md font-bold text-lg">
                            🚀 Start AI Negotiation (Backend)
                        </button>
                    </div>
                </div>
            </div>

            <!-- Negotiation Phase -->
            <div id="negotiationPhase" class="hidden space-y-6">
                <!-- Session Info -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">📊 Live Negotiation Session</h2>
                    <div class="grid md:grid-cols-3 gap-4 text-sm">
                        <div><strong>Session:</strong> <span id="sessionId"></span></div>
                        <div><strong>Product:</strong> <span id="currentProduct"></span></div>
                        <div><strong>Status:</strong> <span id="sessionStatus" class="text-green-600">Active</span></div>
                    </div>
                </div>

                <!-- Chat Interface -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">💬 Real-Time AI Negotiation</h2>
                    <div class="text-sm text-blue-700 bg-blue-50 p-3 rounded-md mb-4">
                        <strong>You are the seller.</strong> The AI agent represents the buyer and will negotiate with you in real-time through the backend server.
                    </div>
                    
                    <div id="chatMessages" class="h-96 overflow-y-auto border border-gray-200 rounded-md p-4 mb-4 space-y-3">
                    </div>
                    
                    <div class="flex space-x-3">
                        <input type="text" id="sellerMessage" placeholder="Enter your seller message..." 
                               class="flex-1 px-4 py-2 border border-gray-300 rounded-md"
                               onkeypress="handleKeyPress(event)">
                        <button onclick="sendSellerMessage()" 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium">
                            Send to AI
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let selectedProductData = null;
        let websocket = null;

        document.addEventListener('DOMContentLoaded', function() {
            checkBackendConnection();
            loadPersonalities();
        });

        async function checkBackendConnection() {
            const statusElement = document.getElementById('connectionStatus');
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                
                if (data.backend === 'connected') {
                    statusElement.innerHTML = `
                        <div class="w-3 h-3 rounded-full bg-green-400"></div>
                        <span class="text-sm">Backend Connected</span>
                    `;
                    showNotification('✅ Connected to main backend server', 'success');
                } else {
                    statusElement.innerHTML = `
                        <div class="w-3 h-3 rounded-full bg-red-400"></div>
                        <span class="text-sm">Backend Offline</span>
                    `;
                    showNotification('⚠️ Backend server offline', 'warning');
                }
            } catch (error) {
                statusElement.innerHTML = `
                    <div class="w-3 h-3 rounded-full bg-red-400"></div>
                    <span class="text-sm">Connection Error</span>
                `;
                showNotification('❌ Cannot connect to backend', 'error');
            }
        }

        async function loadPersonalities() {
            try {
                const response = await fetch('/api/personalities');
                const data = await response.json();
                
                const select = document.getElementById('agentPersonality');
                select.innerHTML = '<option value="">Select agent personality...</option>';
                
                if (data.personalities) {
                    data.personalities.forEach(personality => {
                        const option = document.createElement('option');
                        option.value = personality.value;
                        option.textContent = `${personality.label} - ${personality.description}`;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading personalities:', error);
            }
        }

        async function searchProducts() {
            const product = document.getElementById('productSearch').value.trim();
            const city = document.getElementById('citySearch').value.trim() || 'Mumbai';
            
            if (!product) {
                showNotification('Please enter a product name', 'error');
                return;
            }

            showNotification('🔍 Searching products...', 'info');

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product, city })
                });

                const data = await response.json();
                if (data.success && data.results) {
                    displaySearchResults(data.results);
                    showNotification(`Found ${data.results.length} products`, 'success');
                }
            } catch (error) {
                showNotification('Search failed', 'error');
            }
        }

        function displaySearchResults(results) {
            const resultsDiv = document.getElementById('searchResults');
            const productsList = document.getElementById('productsList');
            
            resultsDiv.classList.remove('hidden');
            productsList.innerHTML = '';

            results.forEach(product => {
                const productCard = document.createElement('div');
                productCard.className = 'border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-blue-50';
                productCard.onclick = () => selectProduct(product);
                
                productCard.innerHTML = `
                    <div class="space-y-2">
                        <h4 class="font-medium">${product.title}</h4>
                        <p class="text-lg font-bold text-blue-600">₹${product.price.toLocaleString()}</p>
                        <p class="text-sm text-gray-500">${product.seller}</p>
                    </div>
                `;
                productsList.appendChild(productCard);
            });
        }

        function selectProduct(product) {
            selectedProductData = product;
            const selectedDiv = document.getElementById('selectedProduct');
            selectedDiv.innerHTML = `
                <div class="text-gray-900">
                    <div class="font-medium">${product.title}</div>
                    <div class="text-blue-600 font-bold">₹${product.price.toLocaleString()}</div>
                </div>
            `;
            
            // Auto-fill prices
            document.getElementById('targetPrice').value = Math.floor(product.price * 0.85);
            document.getElementById('maxBudget').value = Math.floor(product.price * 0.95);
            
            showNotification('✅ Product selected', 'success');
        }

        async function startNegotiation() {
            if (!selectedProductData) {
                showNotification('Please select a product first', 'error');
                return;
            }

            const personality = document.getElementById('agentPersonality').value;
            const targetPrice = parseInt(document.getElementById('targetPrice').value);
            const maxBudget = parseInt(document.getElementById('maxBudget').value);

            if (!personality || !targetPrice || !maxBudget) {
                showNotification('Please fill in all fields', 'error');
                return;
            }

            showNotification('🤖 Connecting to AI backend...', 'info');

            try {
                const response = await fetch('/api/negotiate-product', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product: selectedProductData.title,
                        target_price: targetPrice,
                        max_budget: maxBudget,
                        personality: personality
                    })
                });

                const data = await response.json();

                if (data.success && data.session_id) {
                    currentSessionId = data.session_id;
                    
                    // Switch to negotiation phase
                    document.getElementById('setupPhase').classList.add('hidden');
                    document.getElementById('negotiationPhase').classList.remove('hidden');
                    
                    // Update session info
                    document.getElementById('sessionId').textContent = currentSessionId;
                    document.getElementById('currentProduct').textContent = selectedProductData.title;
                    
                    // Add initial message
                    addChatMessage('system', '🚀 AI agent connected! You are the seller - start the negotiation.', 'System');
                    
                    showNotification('✅ Connected to AI negotiation backend!', 'success');
                } else {
                    showNotification(`❌ ${data.message || data.error}`, 'error');
                }
            } catch (error) {
                showNotification('Failed to connect to backend', 'error');
            }
        }

        async function sendSellerMessage() {
            const messageInput = document.getElementById('sellerMessage');
            const message = messageInput.value.trim();
            
            if (!message || !currentSessionId) return;

            // Add seller message to chat
            addChatMessage('seller', message, 'You (Seller)');
            messageInput.value = '';

            // Show AI thinking
            const thinkingId = addChatMessage('agent', '🤔 AI analyzing...', 'AI Agent', true);

            try {
                const response = await fetch('/api/send-message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        message: message
                    })
                });

                const data = await response.json();

                // Remove thinking message
                const thinkingElement = document.getElementById(thinkingId);
                if (thinkingElement) thinkingElement.remove();

                if (data.success) {
                    addChatMessage('agent', data.response || 'Message processed by backend AI', 'AI Agent');
                } else {
                    addChatMessage('agent', `❌ ${data.error}`, 'AI Agent');
                }

            } catch (error) {
                const thinkingElement = document.getElementById(thinkingId);
                if (thinkingElement) thinkingElement.remove();
                
                addChatMessage('agent', '❌ Backend connection failed', 'AI Agent');
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendSellerMessage();
            }
        }

        function addChatMessage(sender, message, senderName, isTemporary = false) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageId = 'msg_' + Date.now() + Math.random();
            
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = `flex ${sender === 'seller' ? 'justify-end' : 'justify-start'}`;
            
            let bgColor, textColor;
            if (sender === 'seller') {
                bgColor = 'bg-blue-600';
                textColor = 'text-white';
            } else if (sender === 'agent') {
                bgColor = 'bg-gray-200';
                textColor = 'text-gray-900';
            } else {
                bgColor = 'bg-yellow-100';
                textColor = 'text-yellow-900';
            }
            
            messageDiv.innerHTML = `
                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${bgColor} ${textColor}">
                    <div class="text-xs opacity-75 mb-1">${senderName}</div>
                    <div class="text-sm">${message}</div>
                    <div class="text-xs opacity-75 mt-1">${new Date().toLocaleTimeString()}</div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return isTemporary ? messageId : null;
        }

        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            
            let bgColor, icon;
            switch (type) {
                case 'success': bgColor = 'bg-green-500'; icon = '✅'; break;
                case 'error': bgColor = 'bg-red-500'; icon = '❌'; break;
                case 'warning': bgColor = 'bg-yellow-500'; icon = '⚠️'; break;
                default: bgColor = 'bg-blue-500'; icon = 'ℹ️';
            }
            
            notification.innerHTML = `
                <div class="${bgColor} text-white px-6 py-3 rounded-md shadow-lg flex items-center space-x-2">
                    <span>${icon}</span>
                    <span>${message}</span>
                </div>
            `;
            notification.classList.remove('hidden');
            
            setTimeout(() => {
                notification.classList.add('hidden');
            }, 5000);
        }
    </script>
</body>
</html>'''
    
    def run(self, host: str = "0.0.0.0", port: int = 8001, reload: bool = True):
        """Run the web client application"""
        print(f"\\n🚀 Starting AI Negotiation Web Client")
        print(f"📱 Web Interface: http://{host}:{port}")
        print(f"🔗 Backend Server: {self.backend_url}")
        print(f"💡 This web client connects to your main backend for real AI agent interactions")
        print("\\n" + "="*60)
        
        uvicorn.run(
            "new_agent.web_client:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )


def create_web_client(backend_url: str = "http://localhost:8000") -> NegotiationWebClient:
    """Create and return a web client instance"""
    return NegotiationWebClient(backend_url)


# Global app instance for uvicorn
client = NegotiationWebClient()
app = client.app

if __name__ == "__main__":
    client.run()