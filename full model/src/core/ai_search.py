import requests
import database
import json
import re
import os
import time

# Load .env manually to avoid dependencies
def load_env():
    try:
        # Walk up to find .env
        path = os.path.dirname(os.path.abspath(__file__))
        while path:
            env_path = os.path.join(path, '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                break
            parent = os.path.dirname(path)
            if parent == path: break
            path = parent
    except Exception as e:
        print(f"Error loading .env: {e}")

load_env()

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class AISearchService:
    def __init__(self, api_key: str = None):
        # Use provided key or fallback to global constant
        self.api_key = api_key or GROQ_API_KEY
        
        if not self.api_key:
             print("[AI Search] Warning: No API Key found in .env or provided.")
            
        self.model = "openai/gpt-oss-120b" # As requested by user
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_sql(self, user_query: str) -> str:
        """
        Generates a SQL query from a natural language user query using Groq API (via requests).
        """
        schema = database.get_schema_string()
        
        prompt = f"""Convert to SQLite query. Return ONLY raw SQL, no explanation.

Schema:
{schema}

Rules:
- Must start with SELECT
- **ALWAYS use `ORDER BY id DESC` to show latest data first**
- **ALWAYS select image columns when querying wagons: original_image_path, deblurred_image_path, cropped_number_path, anomaly_image_path**
- **When user asks about a specific inspection (by id/number), ALWAYS JOIN with wagons table to get wagon images**
- Check defects: defects != '' AND defects != '[]'
- Default LIMIT 10 unless "all" requested
- Return "ERROR: Cannot answer" if query doesn't match schema
 
Examples:
User: "Show wagons in last video"
SQL: SELECT w.id, w.wagon_index, w.ocr_text, w.defects, w.original_image_path, w.deblurred_image_path, w.cropped_number_path, w.anomaly_image_path FROM wagons w JOIN inspections i ON w.inspection_id = i.id ORDER BY i.id DESC LIMIT 10

User: "Give me info about inspection 5"
SQL: SELECT i.*, w.wagon_index, w.ocr_text, w.defects, w.original_image_path, w.deblurred_image_path, w.cropped_number_path, w.anomaly_image_path FROM inspections i LEFT JOIN wagons w ON w.inspection_id = i.id WHERE i.id = 5 LIMIT 10

User: "Count total wagons"
SQL: SELECT COUNT(*) FROM wagons

Query: "{user_query}"
SQL:"""
        
        try:
            print(f"[AI Search] generating SQL with model: {self.model}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 8192, # Groq uses max_tokens, not max_completion_tokens usually, but adhering to compatibility
                "top_p": 1,
                "stream": False # No streaming for simpler handling
            }
            
            # Using requests directly to avoid httpx dependency issues
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[AI Search] API Error: {response.text}")
                return f"ERROR: Groq API returned {response.status_code}. {response.text}"
                
            data = response.json()
            sql_query = data['choices'][0]['message']['content']
            
            # Remove markdown if present
            sql_query = re.sub(r"^```sql\s*", "", sql_query, flags=re.IGNORECASE)
            sql_query = re.sub(r"\s*```$", "", sql_query)
            
            print(f"[AI Search] ✓ Success")
            return sql_query.strip()
            
        except Exception as e:
            error_str = str(e)
            print(f"[AI Search] ✗ Failed: {error_str}")
            return f"ERROR: Groq generation failed. {error_str}"

    def process_results_with_images(self, results: list) -> list:
        """
        Processes results to convert local file paths to accessible URLs.
        """
        processed_results = []
        for row in results:
            new_row = dict(row)
            for key, val in new_row.items():
                # Check for image paths
                if isinstance(val, str) and ('path' in key.lower() or 'image' in key.lower()) and ('full model' in val or 'jpg' in val or 'png' in val):
                    # Convert absolute path to static URL (Case Insensitive)
                    parts = re.split(r'full model', val, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        rel_path = parts[-1].replace('\\', '/').lstrip('/')
                        new_row[key] = f"http://localhost:8000/static/{rel_path}"
                # Handle images that might just be relative paths already (fallback)
                elif isinstance(val, str) and (val.endswith('.jpg') or val.endswith('.png')) and not val.startswith('http') and not os.path.isabs(val):
                     new_row[key] = f"http://localhost:8000/static/{val}"

            processed_results.append(new_row)
        return processed_results

    def generate_natural_answer(self, user_query: str, sql_query: str, results: list) -> str:
        """
        Generates a natural language response based on the search results.
        """
        prompt = f"""You are a railway track inspection assistant. Answer the user's question based on the database results provided.

User Question: "{user_query}"
SQL Query Executed: {sql_query}
Database Results: {json.dumps(results, indent=2)}

Instructions:
1. Provide a direct, natural language answer.
2. Be professional and concise (industry standard).
3. If the result is a count, state it clearly.
4. **IMPORTANT: If images are present in the results (URLs starting with http), explicitly mention them!** 
   - Example: "I found an anomaly image for wagon 12. You can view it below."
   - Do not output the URL itself in the text, just refer to "the image" or "the photo". The UI will display the image automatically.
5. If no results found, say "I couldn't find any data matching that request."

Answer:"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 1024,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[AI Search] NL Generation Error: {response.text}")
                return "I found the data but couldn't generate a summary."
                
            data = response.json()
            answer = data['choices'][0]['message']['content']
            return answer.strip()
            
        except Exception as e:
            print(f"[AI Search] NL Gen Failed: {e}")
            return "I found the results but encountered an error generating the summary."

    def execute_search(self, user_query: str):
        """
        Executes a search for the user query and returns the results.
        """
        try:
            sql_query = self.generate_sql(user_query)
            
            if sql_query.startswith("ERROR"):
                return {"error": sql_query}
                
            print(f"[AI Search] Generated SQL: {sql_query}")
            
            raw_results = database.execute_read_only_query(sql_query)
            
            # Process images
            results = self.process_results_with_images(raw_results)
            
            # Generate Natural Language Answer
            nl_answer = self.generate_natural_answer(user_query, sql_query, results)
            
            return {
                "query": user_query,
                "sql": sql_query,
                "results": results,
                "count": len(results),
                "answer": nl_answer
            }
            
        except Exception as e:
            print(f"[AI Search] Error: {e}")
            return {"error": str(e)}
