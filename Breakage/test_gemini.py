import os
from google import genai

# Set API key
GEMINI_API_KEY = "AIzaSyCnpRCQlbUnmEmPC77_P-gYXX2qG8eiTg4"
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

def test_gemini_api():
    """Test the Gemini API integration"""
    try:
        # Initialize Gemini client
        client = genai.Client()
        
        # Test prompt
        test_prompt = "Please provide a brief HR summary for an employee with moderate job satisfaction and low burnout. Keep it to 2-3 sentences."
        
        print("Testing Gemini API...")
        print(f"Prompt: {test_prompt}")
        
        # Generate content using Gemini 2.5 Flash model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=test_prompt
        )
        
        print("\nResponse:")
        print(response.text)
        print("\n✅ Gemini API test successful!")
        
    except Exception as e:
        print(f"❌ Error testing Gemini API: {str(e)}")

if __name__ == "__main__":
    test_gemini_api() 