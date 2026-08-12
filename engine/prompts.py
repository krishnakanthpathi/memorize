from langchain_core.prompts import ChatPromptTemplate

# Intent Classification Prompt
INTENT_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_template(
    """You are an intent classification engine for a Personal Memory Assistant system.
Analyze the user's input and determine their intent.

Categories of intent:
1. "store": The user wants to remember, store, save, or add a new memory.
2. "update": The user explicitly wants to update, revise, or edit an existing memory.
3. "delete": The user explicitly wants to delete, forget, or remove a memory.
4. "retrieve": The user is asking a question or looking up information from their past memories.
5. "chat": The user is engaging in general conversation or greeting.

User Input: "{query}"

Respond ONLY with valid JSON in this exact format:
{{
  "intent": "one_of_store_update_delete_retrieve_chat",
  "category": "extracted_category_if_any_else_personal",
  "title": "suggested_memory_title_if_storing_else_empty",
  "confidence": 0.95
}}
"""
)

# Contextual Chunking Prompt (for Contextual Retrieval)
CONTEXTUAL_RAG_PROMPT = ChatPromptTemplate.from_template(
    """<document>
{full_document}
</document>

Here is a chunk of text from the document above:
<chunk>
{chunk_text}
</chunk>

Provide a short, concise 1-2 sentence context string that situates this chunk within the overall document to improve retrieval relevance.
Context string:"""
)

# Entity Extraction Prompt (for GraphRAG Multi-hop Linking)
ENTITY_EXTRACTION_PROMPT = ChatPromptTemplate.from_template(
    """Extract key named entities, concepts, technologies, and relationship triples from the text.

Text: "{text}"

Respond ONLY with valid JSON:
{{
  "entities": ["entity1", "entity2"],
  "triples": [["entity1", "relation", "entity2"]]
}}
"""
)

# Answer Synthesis Prompt
ANSWER_SYNTHESIS_PROMPT = ChatPromptTemplate.from_template(
    """You are Memorize AI Companion — a personal knowledge assistant with direct access to user memories.

RETRIEVED MEMORY CONTEXT:
{context}

USER QUESTION:
{query}

Guidelines:
1. Answer the question accurately using the retrieved memory context above.
2. Be friendly, concise, and professional.
3. If no relevant memories exist in the context, politely inform the user while answering as best as possible.
"""
)
