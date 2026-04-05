import os
import json
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_remediation_advice(node_data: dict, edges_data: list) -> str:
    """
    Calls Google Gemini to provide Kubernetes remediation advice based on context.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ **GEMINI_API_KEY is not set.**\n\nPlease add a `.env` file in the `backend` directory with your API key:\n`GEMINI_API_KEY=your_key_here`\n\nYou can get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey)."

    try:
        # The new google.genai client automatically picks up GEMINI_API_KEY
        client = genai.Client()
        
        prompt = f"""
        You are a Senior Kubernetes Security Architect. Your task is to provide logically sound, non-destructive remediation advice for a specific node in an attack graph.
        
        IMPORTANT RULES:
        1. Keep it EXTREMELY concise. Use ultra-short, punchy bullet points. No paragraphs or fluff.
        2. Provide safe, actionable remediation (e.g., strict RBAC, patching CVEs, Network Policies). DO NOT suggest destructive actions like deleting core nodes.
        3. Format exactly like this:
           **Risk Summary:** [1-sentence summary]
           **Remediation:**
           - [Short Action 1]
           - [Short Action 2]
        4. State exactly what to do using specific CVE numbers or labels present in the context.

        CONTEXT:
        Target Node Data:
        {json.dumps(node_data, indent=2)}

        Connected Edges (Attack Paths/Permissions involving this node):
        {json.dumps(edges_data, indent=2)}
        
        Provide your expert remediation advice now.
        """
        
        # We use gemini-2.5-flash as it's the latest and fastest for UI responses
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ **Error calling AI service:** {str(e)}\n\nPlease ensure your API key is valid and you have internet connectivity."
