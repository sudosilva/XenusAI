"""
XenusAI — Intelligent Response Engine
No external LLM dependencies — pure local intelligence via embeddings + native HuggingFace transformers text generation.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Minimum score to consider a ChromaDB result relevant for RAG
MIN_RELEVANCE_SCORE = 0.25

def generate_response(query: str, history: List[Dict[str, str]] = None, n_results: int = None) -> dict:
    """
    Generate an intelligent conversational response using local LLM + RAG.

    Args:
        query: The user's input.
        history: Conversation history list of {"role": "...", "content": "..."}.
        n_results: Number of results to retrieve.

    Returns:
        Dict with keys:
            - type: 'knowledge' or 'conversational'
            - message: the actual generated response text from the LLM
            - results: list of search results used as context (empty if conversational)
    """
    from retrieval.search import search
    from config import LLM_NUM_RESULTS
    from retrieval.generator import generate_chat_response
    from retrieval.auto_fetcher import AutoFetcher

    n = n_results or LLM_NUM_RESULTS
    
    # 0. Conversational Intent Classifier — skip RAG entirely for casual chat
    import re
    query_lower = query.strip().lower()
    query_lower_clean = re.sub(r'[^a-z\s]', '', query_lower)
    
    # Common conversational patterns that should NEVER trigger knowledge search
    GREETINGS = {
        'hello', 'hi', 'hey', 'howdy', 'sup', 'yo', 'heya', 'hiya',
        'good morning', 'good afternoon', 'good evening', 'good night',
        'whats up', 'what is up', 'how are you', 'how are you doing',
        'how is it going', 'hows it going', 'how do you do',
        'nice to meet you', 'hey there', 'hi there', 'hello there',
        'thanks', 'thank you', 'thx', 'bye', 'goodbye', 'see you',
        'lol', 'haha', 'lmao', 'ok', 'okay', 'cool', 'nice', 'great',
        'who are you', 'what are you', 'what can you do', 'help',
        'tell me about yourself', 'introduce yourself',
    }
    
    is_conversational = False
    # Check exact match
    if query_lower_clean in GREETINGS:
        is_conversational = True
    # Check if the query starts with a greeting
    elif any(query_lower_clean.startswith(g) for g in GREETINGS):
        is_conversational = True
    # Very short queries (< 5 words) that don't look like technical questions
    elif len(query_lower.split()) <= 4 and not any(kw in query_lower for kw in ['code', 'error', 'bug', 'how to', 'what is', 'explain', 'write', 'create', 'build', 'fix', 'debug', 'install', 'setup']):
        is_conversational = True
    
    if is_conversational:
        try:
            response_text = generate_chat_response(query=query, history=history, context="")
            return {
                "type": "conversational",
                "message": response_text,
                "results": [],
            }
        except Exception as e:
            return {
                "type": "conversational",
                "message": "Hey! How can I help you today?",
                "results": [],
            }
    
    # 1. First search the local knowledge base
    raw_results = search(query, n_results=n)
    
    # 2. Advanced Autonomous Learning Protocol (AALP)
    should_fetch = False
    if not raw_results:
        should_fetch = True
    else:
        top_score = raw_results[0].get("score", 0)
        if top_score < 0.35:
            should_fetch = True
            
    if should_fetch:
        logger.info(f"Knowledge deficiency detected. Triggering AutoFetcher for '{query}'.")
        fetcher = AutoFetcher()
        success = fetcher.fetch_and_ingest(query)
        
        # If we successfully learned it, re-query the memory banks!
        if success:
            logger.info("Re-querying local vector store with newly acquired knowledge...")
            raw_results = search(query, n_results=n)
            
    # Filter by absolute relevance threshold
    relevant_chunks = [r for r in raw_results if r.get("score", 0) >= MIN_RELEVANCE_SCORE]
    
    # 3. Build context string (CRITICAL PERFORMANCE FIX)
    context_str = ""
    if relevant_chunks:
        top_chunks = relevant_chunks[:2]
        docs = [f"[Source: {r['source']}]\n{r['document']}" for r in top_chunks]
        context_str = "\n\n".join(docs)
        
        if len(context_str) > 1500:
            context_str = context_str[:1500] + "...\n(Context truncated for speed)"
        
    # 4. Generate response via local HuggingFace SmolLM2
    try:
        response_text = generate_chat_response(query=query, history=history, context=context_str)
        
        if relevant_chunks:
            return {
                "type": "knowledge",
                "message": response_text,
                "results": relevant_chunks,
            }
        else:
            return {
                "type": "conversational",
                "message": response_text,
                "results": [],
            }
            
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return {
            "type": "error",
            "message": f"Failed to generate response natively: {e}",
            "results": [],
        }
