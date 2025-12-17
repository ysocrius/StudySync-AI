from openai import OpenAI
import os
import json
from rag import rag_system

client = OpenAI()

def generate_dialogue_script():
    """Generates a text script for the dialogue."""
    # Use full context if available, otherwise summary
    context = rag_system.full_lexical_context if rag_system.full_lexical_context else rag_system.get_summary()
    
    # Truncate for safety (stay well within 128k context of 4o-mini)
    # 50,000 chars is roughly 12k tokens, leaving plenty of room for output
    safe_context = context[:50000] if context else ""

    prompt = f"""
    Based on the following source material, create an engaging and educational dialogue between a curious STUDENT and a knowledgeable TEACHER.
    
    INSTRUCTIONS:
    1. Scale the length of the dialogue based on the amount of content provided.
       - If content is brief, keep the dialogue short and concise.
       - If content is extensive, create a comprehensive "Deep Dive" discussion covering all key themes.
    2. The goal is to explain the key concepts found in the context clearly.
    3. Use natural conversational fillers (e.g., "Hmm", "I see", "That makes sense").
    
    Source Material: {safe_context}
    
    Output strictly valid JSON list of objects, where each object has "speaker" (Teacher/Student) and "text".
    Example:
    [
        {{"speaker": "Student", "text": "I've heard about this topic, but what does it really mean?"}},
        {{"speaker": "Teacher", "text": "Great question! Essentially, it refers to..."}}
    ]
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an educational scriptwriter."},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    # Ideally parsing json properly
    try:
        # data might be wrappe in { "dialogue": [...] } or just [...]
        data = json.loads(content)
        if "dialogue" in data:
            return data["dialogue"]
        if isinstance(data, list):
            return data
        return [] # Fallback
    except:
        return []

def generate_audio_files(script_data, output_dir="static/audio"):
    """Generates audio files for each line."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    result = []
    
    for i, line in enumerate(script_data):
        speaker = line["speaker"]
        text = line["text"]
        # Use hash of text for filename to ensure audio matches text
        import hashlib
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"{i}_{speaker}_{text_hash[:8]}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Audio generation (Teacher = Alloy, Student = Nova)
        voice = "alloy" if speaker == "Teacher" else "nova"
        
        if not os.path.exists(filepath): # Cache check
            try:
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text
                )
                response.stream_to_file(filepath)
            except Exception as e:
                print(f"Error generating audio for {i}: {e}")
        
        result.append({
            "speaker": speaker,
            "text": text,
            "audioUrl": f"/static/audio/{filename}"
        })
        
    return result
