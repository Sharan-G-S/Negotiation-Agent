# Simple test script for the negotiation agent
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test basic Gemini AI connection"""
    api_key = os.getenv("GEMINI_API_KEY")  
    if not api_key or api_key == "AIzaSyDD94qIFoT1XQ62GLWzXpvLjKDgwaXpmpI":
        print("❌ GEMINI_API_KEY not configured in .env file")
        print("Please add your Gemini API key to the .env file")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test simple interaction
        response = model.generate_content("Hello! I'm testing the connection. Please respond with a simple greeting.")
        print("✅ Gemini AI connection successful!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Gemini AI: {e}")
        return False

def test_negotiation_scenario():
    """Test a simple negotiation scenario"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠️ Skipping negotiation test - no API key configured")
        return
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        You are Bob, a buyer interested in purchasing a used laptop. 
        The seller is asking $800 for it. 
        Respond as Bob would, showing interest but trying to negotiate the price down.
        Keep your response conversational and brief.
        """
        
        response = model.generate_content(prompt)
        print("🤖 Negotiation Test Response:")
        print(response.text)
        
    except Exception as e:
        print(f"❌ Negotiation test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing NegotiBot AI Agent...")
    print("=" * 50)
    
    # Test basic connection
    if test_gemini_connection():
        print("\n" + "=" * 50)
        # Test negotiation scenario
        test_negotiation_scenario()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")