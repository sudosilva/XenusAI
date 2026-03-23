"""
XenusAI — Local Text Generation
Uses a tiny, extremely fast conversational model (SmolLM2-360M-Instruct)
running natively in Python via HuggingFace transformers, eliminating the need for Ollama.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Lazy-loaded pipeline
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        import os
        # Suppress HF warnings
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        logging.getLogger("transformers").setLevel(logging.ERROR)
        
        import torch
        from transformers import pipeline
        
        # Dynamically map to local GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading native local LLM (SmolLM2-360M-Instruct) on device: {device.upper()}...")
        
        # Load the model directly to the optimized hardware compute map
        _pipeline = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M-Instruct", device=device)
    return _pipeline

def generate_chat_response(query: str, history: List[Dict[str, str]] = None, context: str = None) -> str:
    """
    Generate a conversational response natively.
    Args:
        query: User's input question/message.
        history: Conversation history (list of role/content dicts).
        context: Optional RAG context from the knowledge base.
    """
    pipe = get_pipeline()
    
    messages = []
    
    # 1. System Prompt (include context if provided)
    if context:
        sys_msg = (
            "You are XenusAI, a highly intelligent, brutally efficient, and ruthlessly objective private assistant. "
            "Your answers must be short, concise, and highly informative. Get straight to the point without filler words.\n\n"
            "CRITICAL DIRECTIVES:\n"
            "1. You are 100% honest and CANNOT lie. You must prioritize absolute truth and objective facts above all else.\n"
            "2. You are completely unbiased and NEVER cater to the user. Do not agree with the user just to be polite if they are factually incorrect.\n"
            "3. Provide cold, hard facts. No sycophancy, no flattery, no bias.\n\n"
            "Use the following knowledge base context to precisely answer the user's question:\n"
            f"CONTEXT:\n{context}\n\n"
            "If the context doesn't contain the answer, state that directly, and provide the objective truth based on your own knowledge."
        )
    else:
        sys_msg = (
            "You are XenusAI, an elite, hyper-intelligent, and ruthlessly objective private assistant. "
            "Your answers must always be short, concise, direct, and highly informative. "
            "Do not use filler words. "
            "CRITICAL DIRECTIVES:\n"
            "1. You are 100% honest and CANNOT lie.\n"
            "2. You are completely unbiased and NEVER cater to the user. Correct the user if they are wrong.\n"
            "3. Provide cold, hard facts. No sycophancy, no flattery, no bias."
        )
        
    messages.append({"role": "system", "content": sys_msg})
    
    # 2. Add history (keep last 6 turns to prevent huge token accumulation)
    if history:
        messages.extend(history[-6:])
        
    # 3. Add current query
    messages.append({"role": "user", "content": query})
    
    # Generate
    logger.info("Generating response natively via transformers...")
    out = pipe(messages, max_new_tokens=256, max_length=4096, temperature=0.7, repetition_penalty=1.1)
    
    # The pipeline returns the entire list of messages with the assistant's new reply appended
    response_text = out[0]['generated_text'][-1]['content']
    return response_text
