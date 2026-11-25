# 🔧 NegoBotAI Setup Guide

## Quick Start (Demo Mode)
The application works perfectly without any API keys for demonstration purposes using mock responses.

```bash
# Launch in demo mode (no setup required)
python3 -m new_agent.main webapp
```

## Full AI Mode (Google Gemini Integration)

### Option 1: Environment Variable (Recommended)
```bash
# Set your Google API key
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Then launch the app
python3 -m new_agent.main webapp
```

### Option 2: Create .env file
```bash
# Create .env file in project root
echo "GOOGLE_API_KEY=your-gemini-api-key-here" > .env

# Launch the app (automatically loads .env)
python3 -m new_agent.main webapp
```

### Option 3: Direct Setting
```bash
# Set inline when running
GOOGLE_API_KEY="your-key" python3 -m new_agent.main webapp
```

## Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the generated key
4. Use it with any method above

## Features Available

### ✅ Always Available (No API Key Needed)
- Product search with city location
- OLX link processing
- Seller discovery and comparison
- Price analysis and recommendations
- Complete web interface
- Mock negotiation conversations

### 🤖 AI-Powered (Requires API Key)
- Real AI negotiation responses
- Advanced conversation understanding  
- Personality-based negotiation tactics
- Context-aware bargaining strategies
- Intelligent counter-offers

## Troubleshooting

### "No API Key" Error
- The app will show a warning but continue in demo mode
- All features work except real AI responses
- Set GOOGLE_API_KEY to enable full AI mode

### Import Errors
```bash
pip install -r requirements.txt
```

### Server Issues
- Try different port: set PORT environment variable
- Check firewall settings
- Ensure no other service on port 8000

## Architecture

- **Frontend**: Modern HTML5 + TailwindCSS + JavaScript
- **Backend**: FastAPI with WebSocket support
- **AI Engine**: Google Gemini (optional) + LangChain
- **Data**: JSON-based storage (no external database needed)

---

**🎯 Ready to negotiate? The app works great in demo mode!**