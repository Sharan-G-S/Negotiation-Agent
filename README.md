# 🤖 AI Negotiation Agent

An intelligent AI-powered negotiation assistant that helps buyers negotiate better deals on online marketplaces. The system uses advanced AI (Google Gemini + LangChain) to analyze products, understand market conditions, and generate strategic negotiation responses.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)
![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🎯 Core Capabilities
- **Smart Product Scraping**: Automatically extracts product details from marketplace URLs (OLX, Facebook Marketplace, etc.)
- **AI-Powered Negotiations**: Uses Google Gemini AI with LangChain framework for intelligent response generation
- **Advanced Negotiation Engine**: Implements sophisticated tactics including anchoring, reciprocity, scarcity, and more
- **Real-time Communication**: WebSocket-based chat interface for seamless negotiation flow
- **Market Analysis**: Analyzes pricing trends and suggests optimal negotiation strategies

### 🛠️ Technical Highlights
- **Multi-Strategy Scraping**: Fallback mechanisms using Playwright, Selenium, CloudScraper, and HTTP requests
- **LangChain Integration**: Advanced AI agent with tools for market analysis, price calculation, and strategy selection
- **Session Management**: Persistent negotiation sessions with history tracking
- **User Authentication**: Secure JWT-based authentication for buyers and sellers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│    │   Chat UI    │  │  Product     │  │   Market     │        │
│    │  Interface   │  │   Display    │  │  Analysis    │        │
│    └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                    WebSocket / REST API
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Auth      │  │  Session    │  │    Negotiation          │ │
│  │  Service    │  │  Manager    │  │      Engine             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Enhanced   │  │   Gemini    │  │    LangChain            │ │
│  │  Scraper    │  │   Service   │  │      Agent              │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Negotiation-Agent/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── auth_service.py         # User authentication & JWT handling
│   ├── database.py             # JSON database operations
│   ├── enhanced_ai_service.py  # Enhanced AI response generation
│   ├── enhanced_scraper.py     # Multi-strategy web scraping
│   ├── gemini_service.py       # Google Gemini AI integration
│   ├── langchain_agent.py      # LangChain negotiation agent
│   ├── mcp_integration.py      # Model Context Protocol integration
│   ├── models.py               # Pydantic data models
│   ├── negotiation_engine.py   # Advanced negotiation tactics
│   ├── scraper_service.py      # Base scraping service
│   ├── session_manager.py      # Negotiation session management
│   ├── websocket_manager.py    # WebSocket connection handler
│   └── data/                   # JSON data storage
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React application
│   │   ├── AppSelfContained.jsx # Self-contained app component
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx    # Chat UI component
│   │   │   ├── MarketAnalysis.jsx   # Market analysis display
│   │   │   ├── ProductCard.jsx      # Product information card
│   │   │   ├── SellerPortal.jsx     # Seller management portal
│   │   │   ├── Sidebar.jsx          # Navigation sidebar
│   │   │   └── UnifiedAuth.jsx      # Authentication component
│   │   ├── hooks/
│   │   │   └── useNegotiationStore.js # State management
│   │   └── services/
│   │       ├── api.js           # REST API service
│   │       └── websocket.js     # WebSocket service
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── data/                       # Persistent data storage
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API Key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sharan-G-S/Negotiation-Agent.git
   cd Negotiation-Agent
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET_KEY=your_secure_secret_key
   ```

5. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   ```
   http://localhost:5173
   ```

## 🎮 Usage

### Starting a Negotiation

1. **Enter Product URL**: Paste a marketplace URL (OLX, Facebook Marketplace, etc.)
2. **Set Target Price**: Your desired purchase price
3. **Set Max Budget**: Maximum you're willing to pay
4. **Choose Approach**:
   - **Assertive**: Direct, confident negotiation style
   - **Diplomatic**: Balanced, collaborative approach
   - **Considerate**: Polite, budget-conscious style
5. **Select Timeline**: Urgent, within a week, or flexible
6. **Start Negotiation**: The AI will analyze the product and begin negotiating

### Negotiation Flow

1. AI scrapes and analyzes the product listing
2. Market analysis provides pricing insights
3. AI generates an opening offer based on your parameters
4. Enter seller's responses to continue the negotiation
5. AI adapts strategy based on seller's behavior
6. Track progress through the metrics panel

## 🧠 AI Negotiation Strategies

The system implements multiple negotiation tactics:

| Tactic | Description |
|--------|-------------|
| **Anchoring** | Start with a strategic low offer to set the price anchor |
| **Reciprocity** | Make small concessions to encourage seller reciprocation |
| **Scarcity** | Leverage time pressure when appropriate |
| **Social Proof** | Reference market prices and comparable sales |
| **Commitment** | Build incremental agreements toward the final deal |

## 🔧 API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Negotiation
- `POST /api/negotiate/start` - Start new negotiation
- `POST /api/negotiate/respond` - Process seller response
- `POST /api/negotiate/end` - End negotiation session
- `GET /api/sessions` - Get all sessions
- `GET /api/session/{session_id}` - Get specific session

### WebSocket
- `WS /ws/{session_id}` - Real-time negotiation updates

## 🛡️ Security Features

- JWT-based authentication
- Password hashing with PBKDF2
- Session management with expiration
- CORS protection
- Input validation with Pydantic

## 📊 Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **LangChain** - AI agent framework
- **Google Gemini** - Large language model
- **Pydantic** - Data validation
- **WebSockets** - Real-time communication
- **Playwright/Selenium** - Web scraping

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Framer Motion** - Animations
- **Lucide React** - Icons

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- LangChain for the agent framework
- FastAPI for the excellent web framework
- The open-source community

## 📧 Contact

**Sharan G S** - [@Sharan-G-S](https://github.com/Sharan-G-S)

Project Link: [https://github.com/Sharan-G-S/Negotiation-Agent](https://github.com/Sharan-G-S/Negotiation-Agent)

---

<p align="center">Made with ❤️ for smarter negotiations</p>
