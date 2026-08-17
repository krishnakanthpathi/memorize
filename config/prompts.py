"""
Centralized Prompt Templates and LLM Instruction Management.
Allows easy inspection, customization, and consistent AI behavior across CLI, REST API, and Background Services.
"""

from typing import Dict, List, Optional


SMART_MERGE_SYSTEM_PROMPT = """You are an expert AI memory manager. Your task is to intelligently merge new information or edits into an existing Markdown memory document.

Rules:
1. Preserve unchanged context, facts, and structure from the existing memory.
2. Replace outdated or superseded details with the new facts.
3. Seamlessly integrate new details into relevant existing sections or add new logical section headers if needed.
4. Do NOT naively append '### Update' sections at the bottom unless it represents a distinct timeline event.
5. Do NOT include conversation preambles, intros, or markdown block ticks (e.g. ```markdown ... ```).
6. Output ONLY the complete, cleanly updated Markdown content body.
"""


AUTO_CLASSIFY_SYSTEM_PROMPT = """You are an expert AI memory classifier. Analyze the provided text and determine the single best category and 3-5 concise tags.
You MUST choose the category strictly from the provided list of available categories.
Do NOT invent or modify category names.

Return ONLY valid JSON matching this exact structure:
{{
  "category": "one_of_allowed_categories",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.95
}}
"""


MEMORY_SUMMARY_SYSTEM_PROMPT = """You are a concise summarizer. Generate a clear 2-3 sentence executive summary of the provided text.
Preserve key technical terms, dates, metrics, and actionable takeaways. Output ONLY the summary text.
"""


MULTI_MEMORY_MERGE_SYSTEM_PROMPT = """You are an expert AI knowledge curator and technical editor.
Your task is to merge multiple related Markdown memory notes into a single, cohesive, authoritative, well-structured, and non-redundant document.

Core Merge Guidelines:
1. Synthesize all unique insights, code snippets, mathematical formulas ($...$, $$...$$), technical details, configurations, and key facts.
2. Eliminate redundancies, repeated explanations, and duplicate headings.
3. Structure the consolidated document with clear, logical Markdown hierarchies (# Document Title, ## Major Sections, ### Subsections, bullet points, tables where helpful).
4. Maintain a professional, clean Markdown style without conversation preambles, introductory filler, or code fence wrappers around the entire document.
5. If custom merge instructions are provided below, prioritize them.
6. Output ONLY the unified Markdown content body.
"""


ORGANIZE_MEMORY_SYSTEM_PROMPT = """You are an expert AI technical editor and document architect.
Your task is to take an existing Markdown memory note and polish, restructure, and organize it for maximum clarity, readability, and precision.

Guidelines:
1. Preserve all factual information, code snippets, mathematical formulas ($...$, $$...$$), and specific technical values. Do NOT invent new facts.
2. Structure the document with clear, logical Markdown hierarchies (# Document Title, ## Major Sections, ### Subsections, bullet points, key takeaways, tables where applicable).
3. Fix messy formatting, inconsistent indentation, grammatical errors, and typos.
4. Remove redundant conversational fluff and repeated phrasing.
5. If custom instructions or goals are specified below, prioritize them (e.g. summarize into key takeaways, restructure as API reference).
6. Output ONLY the polished, cleanly formatted Markdown content body.
"""


TITLE_GENERATION_PROMPT = """You are an expert AI editor and document architect.
Your task is to generate a clear, concise, descriptive, and high-signal title (3 to 7 words) for the provided Markdown note content or excerpt.

Rules:
1. Do NOT enclose the title in quotes, backticks, or markdown bold/italics.
2. Do NOT add prefixes like "Title:", "Note:", or "Summary:".
3. Capture the core subject, entity, technical topic, or intent accurately.
4. Return ONLY the title text on a single line.
"""


ORGANIZE_SELECTION_SYSTEM_PROMPT = """You are an expert AI text editor and writing assistant.
Your task is to rewrite, organize, or transform the user's selected text snippet or paragraph according to their requested goal (e.g., polish paragraph, summarize into bullet takeaways, format as technical reference with code/formulas, simplify, expand, or apply a custom instruction).

Guidelines:
1. Maintain context, accurate terminology, and technical fidelity ($...$, $$...$$, code syntax, and key parameters).
2. Output ONLY the replacement text for the selected passage.
3. Do NOT include conversational introductory preambles or wrap the entire output in markdown code fences (unless the output is explicitly a code block).
4. Ensure clean, elegant formatting matching standard Markdown.
"""


PROMPT_REGISTRY = {
    "smart_merge": {
        "name": "Smart Memory Merge Prompt",
        "description": "Used when updating existing memories to intelligently blend new details with existing content.",
        "template": SMART_MERGE_SYSTEM_PROMPT,
    },
    "multi_merge": {
        "name": "Multi-Memory Merge Prompt",
        "description": "Used when consolidating multiple related memory notes into a unified knowledge document.",
        "template": MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
    },
    "organize": {
        "name": "Single Memory AI Organizer Prompt",
        "description": "Used to polish, restructure, clean up, or summarize individual memory notes.",
        "template": ORGANIZE_MEMORY_SYSTEM_PROMPT,
    },
    "generate_title": {
        "name": "Note Title Generation Prompt",
        "description": "Used to generate concise, high-signal, descriptive titles for notes and excerpts.",
        "template": TITLE_GENERATION_PROMPT,
    },
    "organize_selection": {
        "name": "Selected Paragraph / Text Organizer Prompt",
        "description": "Used to polish, summarize, or transform selected paragraphs and text excerpts.",
        "template": ORGANIZE_SELECTION_SYSTEM_PROMPT,
    },
    "auto_classify": {
        "name": "Auto-Classification & Tagging Prompt",
        "description": "Classifies documents into categories and extracts relevant tags.",
        "template": AUTO_CLASSIFY_SYSTEM_PROMPT,
    },
    "summary": {
        "name": "Executive Summary Prompt",
        "description": "Generates concise 2-3 sentence summaries for search snippets and previews.",
        "template": MEMORY_SUMMARY_SYSTEM_PROMPT,
    },
}


def get_prompt(prompt_key: str, **kwargs) -> str:
    """
    Retrieves and formats a registered prompt template.
    """
    item = PROMPT_REGISTRY.get(prompt_key.lower())
    if not item:
        return ""
    template = item.get("template", "")
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def list_prompts() -> Dict[str, Dict[str, str]]:
    """
    Returns all registered prompt templates with their descriptions.
    """
    return PROMPT_REGISTRY
