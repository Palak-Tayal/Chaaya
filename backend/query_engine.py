import os
from openai import OpenAI

# Initialize Ollama client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

MODEL_NAME = "llama3.1:8b"  # or "llama3.1:8b", "mistral", etc.

def query_perspective(messages_list, question, person, use_openai=True):
    # Filter messages from this person
    person_messages = [m for m in messages_list if m['sender'] == person]
    
    if not person_messages:
        return {'type': 'no_results', 'message': f"No messages from {person} found.", 'sources': []}
    
    # Take recent messages as style examples
    try:
        # Sort by timestamp (approximate)
        person_messages.sort(key=lambda x: x['timestamp'], reverse=True)
    except:
        pass
    
    sample_size = min(10, len(person_messages))
    style_messages = person_messages[:sample_size]  # most recent
    
    sources = [{'text': msg['message'], 'timestamp': msg['timestamp'], 'sender': msg['sender']}
               for msg in style_messages]
    
    if not use_openai or not client:
        return {'type': 'retrieval', 'sources': sources}
    
    # Create style examples text
    style_examples = "\n".join([f"- {src['text']}" for src in sources])
    
    # System message to set role
    system_message = f"""You are an AI that helps someone grieving by imagining how their deceased loved one would comfort them. 
You will be given examples of {person}'s actual messages to understand their unique voice: their typical phrases, emojis, language mix, and warmth.
Your task is to write a comforting response to the user's current message **in the exact style of {person}**, using the examples as a guide.
Do not add generic platitudes or stray from {person}'s voice. Keep the response concise (2–4 sentences) and natural."""
    
    user_prompt = f"""**Examples of {person}'s messages:**
{style_examples}

**User's current message:** "{question}"

**Now write a short, deeply comforting response as if you are {person} speaking to the user.** 
- Start with a phrase like "If I were here, I would..." or "I would hold you close and say..."
- Use {person}'s tone, phrases, and emojis from the examples.
- Stay focused on comforting the user, not giving advice or unrelated content.
- Do not mention that this is an AI simulation.

Write the response now:
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=250
        )
        answer = response.choices[0].message.content.strip()
        return {'type': 'generated', 'answer': answer, 'sources': sources}
    except Exception as e:
        print(f"Ollama error: {e}")
        return {'type': 'retrieval', 'sources': sources, 'error': str(e)}