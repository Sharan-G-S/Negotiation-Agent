# 🤖 NegoBotAI - Complete Web Application

**AI-Powered Negotiation Agent with Modern Web Interface**

## 🌟 Features

- **🔍 Smart Product Search**: Find products across multiple categories
- **🏪 Seller Discovery**: Automatically find and compare sellers with best prices
- **🤖 AI Negotiation Chat**: Real-time NLP conversation with intelligent bargaining
- **📊 Price Analytics**: Track negotiations and deal success rates
- **⚙️ Customizable Agent**: Set personality, budget, and negotiation strategies
- **💱 Multi-Currency Support**: INR and other currencies
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start

### Option 1: Direct Launch (Recommended)
```bash
python launch_webapp.py
```

### Option 2: Using Main Script
```bash
python -m new_agent.main webapp
```

### Option 3: Traditional Method
```bash
# Install dependencies
pip install -r requirements.txt

# Set up your Google API key (optional, uses mock data if not set)
export GOOGLE_API_KEY="your-gemini-api-key"

# Launch the web application
python -m new_agent.main webapp
```

## 🌐 Access the Application

Once launched, open your browser and navigate to:
- **Local**: http://localhost:8000
- **Network**: http://0.0.0.0:8000 (accessible from other devices)

## 🎯 How to Use

1. **Search for Products**: Enter product name/category in the search bar
2. **Select Sellers**: Choose from discovered sellers with price comparisons
3. **Configure Agent**: Set your budget, target price, and negotiation style
4. **Start Negotiation**: Begin real-time chat with the AI agent representing you as buyer
5. **Track Progress**: Monitor deal progress and negotiation analytics

## 🔧 Configuration Options

### Agent Personalities
- **Aggressive**: Direct, firm negotiation tactics
- **Friendly**: Relationship-building approach
- **Professional**: Business-focused negotiations
- **Budget-Conscious**: Price-focused strategy
- **Quality-Focused**: Emphasizes product quality
- **Time-Pressured**: Quick deal closure

### Negotiation Settings
- **Target Price**: Your ideal price point
- **Maximum Budget**: Upper limit you're willing to pay
- **Original Price**: Starting price from seller
- **Tone**: Formal, casual, or friendly communication style

## 🏗️ Technical Architecture

- **Backend**: FastAPI with WebSocket support
- **AI Engine**: Google Gemini with LangChain agents
- **Frontend**: Modern HTML5 with TailwindCSS
- **Real-time**: WebSocket communication for instant chat
- **Data Storage**: JSON-based session management

## 📱 User Interface

### Main Dashboard
- Product search and filtering
- Seller comparison table
- Negotiation configuration panel
- Real-time chat interface

### Analytics Panel
- Deal success rate tracking
- Price savings analysis
- Negotiation history
- Performance metrics

## 🔒 Security & Privacy

- Session-based user management
- Secure API key handling
- Local data storage
- No sensitive information logged

## 🐛 Troubleshooting

### Common Issues
- **Port already in use**: The app will automatically try alternative ports
- **Missing packages**: Run `pip install -r requirements.txt`
- **API key errors**: Set `GOOGLE_API_KEY` environment variable or use mock mode

### Getting Help
- Check browser console for JavaScript errors
- Monitor terminal output for server logs
- Ensure all requirements are installed

## 🎨 Customization

The web interface uses TailwindCSS and can be easily customized:
- Edit templates in `new_agent/complete_web_ui.py`
- Modify styles in the HTML template
- Add new API endpoints in the FastAPI application

## 📈 Performance

- Lightweight single-file application
- Efficient WebSocket communication
- Responsive design optimized for speed
- Mock data mode for development/testing

---

**Ready to negotiate? Launch the app and start saving money! 🎯💰**