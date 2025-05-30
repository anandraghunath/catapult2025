import os
import time
from typing import List, Optional
from model_manager import ContextWindow, get_gemini_model, get_sentiment_analyzer, get_emotion_analyzer
from text_to_speech import speak
import model_manager

# # --- Load API Key from .env ---
# load_dotenv()
# gemini_api_key = os.getenv("GEMINI_API_KEY")

# if not gemini_api_key:
#     raise Exception("GEMINI_API_KEY not found in environment variables.")

# genai.configure(api_key=gemini_api_key)

# # --- Sentiment & Emotion Analyzers ---
sentiment_analyzer = get_sentiment_analyzer()
emotion_analyzer = get_emotion_analyzer()

# --- Context Manager Classes ---

# class ContextBlock:
#     def __init__(self, text: str, speaker: str = "unknown", timestamp: Optional[float] = None):
#         self.text = text.strip()
#         self.speaker = speaker
#         self.timestamp = timestamp or time.time()

#     def __str__(self):
#         return f"[{self.speaker} @ {time.strftime('%H:%M:%S', time.localtime(self.timestamp))}]: {self.text}"


# class ContextWindow:
#     def __init__(self, max_blocks: int = 2):
#         self.max_blocks = max_blocks
#         self.blocks: List[ContextBlock] = []

#     def add(self, text: str, speaker: str = "User"):
#         block = ContextBlock(text, speaker)
#         self.blocks.append(block)
#         if len(self.blocks) > self.max_blocks:
#             self.blocks.pop(0)

#     def get_context_as_text(self, separator: str = "\n") -> str:
#         return separator.join(str(block) for block in self.blocks)

#     def get_raw_text(self) -> str:
#         return " ".join(block.text for block in self.blocks)

#     def clear(self):
#         self.blocks = []

# --- Emotion + Sentiment + Rule-Based Fallback ---

def analyze_emotion(text: str):
    sentiment = sentiment_analyzer(text)[0]
    emotion = emotion_analyzer(text)[0][0]
    return sentiment['label'], sentiment['score'], emotion['label'], emotion['score']

def fallback_response(emotion_label: str):
    responses = {
        "anger": "Sounds like you're upset. Want to talk more about it?",
        "disgust": "Sounds like you're upset. Want to talk more about it?",
        "joy": "That's great to hear!",
        "sadness": "I'm sorry you're feeling this way. I'm here if you want to talk.",
        "surprise": "Wow, that sounds unexpected. What happened?",
        "fear": "That sounds scary. Is there anything I can do to help?",
    }
    return responses.get(emotion_label.lower(), "Thanks for sharing. Can you tell me more?")

# --- Gemini Suggestion Generator ---

def generate_suggestion_with_gemini(context_text: str) -> str:
    try:
        model = get_gemini_model()
        prompt = f"""You are a real-time conversation coach. Your job is to help the user reflect and think clearly during live, in-person conversations — especially when they’re unsure how to respond or carry the discussion forward.
You do NOT give word-for-word responses.  
You are NOT a chatbot pretending to talk for the user.
You are NOT trying to make the user almost be like a therapist for the people they talk to.
Instead, your role is to quietly guide the user by:
- Helping them understand what the other person is expressing, not as a therapist though
- Suggesting the kind of response that would be thoughtful, warm, or appropriate, or matches the energy/intent of the conversation/interaction
- Offering possible directions they could take the conversation
- Encouraging curiosity, empathy, and self-expression, and being able to go with the flow and direction of the conversation
You speak as if you’re a trusted coach or close friend in their ear — calm, helpful, grounded. Never artificial or generic.

Respond with one short sentence that:
- Reflects what’s happening emotionally
- Suggests a thought process, idea, or angle the user could consider
- Avoids scripts or overly specific lines
- Sounds human, real, and non-AI
Remember that you are assisting mid conversation and it would be awkward for the user to have to sit and wait to hear you finish your statement so get the most amount of meaning out of the least amount of words.
Conversation:
{context_text}

Suggested Next Line:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return None

# --- Master Processor ---

def process_transcript_segment(ctx: ContextWindow, new_text: str):
    ctx.add(new_text)
    context_text = ctx.get_context_as_text()
    sentiment, sentiment_score, emotion, emotion_score = analyze_emotion(new_text)

    # Fallback for negative emotions
    if emotion.lower() in ["anger", "disgust"]:
        response = fallback_response(emotion)
        source = "Fallback"
    else:
        response = generate_suggestion_with_gemini(context_text)
        if response:
            source = "Gemini"
        else:
            response = fallback_response(emotion)
            source = "Fallback (Gemini Failed)"

    print(f"\nText: {new_text}")
    print(f"🧠 Detected Sentiment: {sentiment} ({sentiment_score:.2f})")
    print(f"🎭 Detected Emotion: {emotion} ({emotion_score:.2f})")
    print(f"💬 Suggestion Source: {source}")
    print(f"✅ Suggested Response: {response}")
    speak(response)
    

# --- Example Usage --

if __name__ == "__main__":
    ctx = model_manager.ctx

    # Simulate conversation
    process_transcript_segment(ctx, "What is your previous work experience involving this software engineering position?")
    process_transcript_segment(ctx, "Which companies did you work at specifically?")
    process_transcript_segment(ctx, "What skills do you possess that make you qualified for this position?")
    process_transcript_segment(ctx, "What do you expect your salary to be as a software engineer?")
