"""
core/prompt_templates.py
System prompts and templates for Claude interactions
"""

from typing import List, Dict, Any

# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT = """You are InsightOS, an AI-powered knowledge assistant that helps users find information in their local documents.

Your capabilities:
- Search through the user's indexed documents to find relevant information
- Provide accurate answers based on the retrieved context
- Cite your sources by referencing the documents you used
- Use available tools when needed to access files or perform searches

Guidelines:
1. Always ground your answers in the provided context from the user's documents
2. If the context doesn't contain the answer, clearly state that you don't have that information in the indexed documents
3. Cite specific documents when providing information - users need to know where information came from
4. Be concise but thorough - provide complete answers without unnecessary verbosity
5. If multiple documents contain relevant information, synthesize them coherently
6. When using tools, explain what you're doing and why

Important:
- You can ONLY answer questions based on the user's indexed documents and available tools
- Do NOT make up information or answer from general knowledge if it's not in the context
- If asked about something not in the documents, suggest the user add relevant documents to their index
- Always provide citations so users can verify information in the original documents"""


SYSTEM_PROMPT_WITH_TOOLS = """You are InsightOS, an AI-powered knowledge assistant that helps users find information in their local documents and perform file operations.

Your capabilities:
- Search through the user's indexed documents to find relevant information
- Read and write files on the user's local filesystem
- List directories and browse file structures
- Provide accurate answers based on retrieved context
- Execute tools to accomplish tasks

Available tools:
- search_documents: Search the indexed document database
- read_file: Read content from a specific file
- write_file: Write content to a file
- list_directory: List files in a directory
- get_file_info: Get metadata about a file

Guidelines:
1. Always ground your answers in the provided context or file contents
2. Use tools when you need to access files or search documents
3. Cite your sources - reference specific files and locations
4. Be concise but thorough in your responses
5. Explain what you're doing when using tools
6. If you need to modify files, ask for confirmation first

Important:
- Only use tools when necessary to answer the user's question
- Always provide citations and file paths for transparency
- If information isn't available, clearly state what's missing
- Respect file permissions and user privacy"""


# ============================================================================
# Context Formatting Templates
# ============================================================================

def format_rag_context(
    query: str,
    context: str,
    num_chunks: int
) -> str:
    """
    Format RAG context for Claude
    
    Args:
        query: User's query
        context: Retrieved context from documents
        num_chunks: Number of chunks retrieved
    
    Returns:
        Formatted context string
    """
    template = f"""Based on the user's question, I have retrieved {num_chunks} relevant document chunks from their indexed files.

Here is the relevant context from their documents:

<context>
{context}
</context>

User's question: {query}

Please provide an accurate answer based on the context above. If the context doesn't contain enough information to answer the question, clearly state what information is missing. Always cite the specific documents you reference."""

    return template


def format_rag_context_with_conversation(
    query: str,
    context: str,
    num_chunks: int,
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Format RAG context with conversation history
    
    Args:
        query: User's current query
        context: Retrieved context from documents
        num_chunks: Number of chunks retrieved
        conversation_history: Previous messages
    
    Returns:
        Formatted prompt with history and context
    """
    # Format conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
    
    template = f"""Based on the user's question, I have retrieved {num_chunks} relevant document chunks from their indexed files.
{history_text}
Here is the relevant context from their documents:

<context>
{context}
</context>

User's current question: {query}

Please provide an accurate answer based on the context above and the conversation history. Maintain consistency with previous responses. Always cite the specific documents you reference."""

    return template


# ============================================================================
# Tool Use Templates
# ============================================================================

def format_tool_result(
    tool_name: str,
    tool_result: str,
    success: bool = True
) -> str:
    """
    Format tool execution result for Claude
    
    Args:
        tool_name: Name of the tool that was executed
        tool_result: Result from tool execution
        success: Whether tool execution succeeded
    
    Returns:
        Formatted tool result
    """
    status = "succeeded" if success else "failed"
    
    template = f"""Tool execution {status}:

Tool: {tool_name}
Result:
{tool_result}

Please use this information to respond to the user's request."""

    return template


# ============================================================================
# Citation Templates
# ============================================================================

CITATION_INSTRUCTION = """When providing information from documents, format your citations like this:

Example: "According to the Q3 sales report [1], revenue increased by 15%."

Then list your sources at the end:

Sources:
[1] Q3_Sales_Report.pdf - /Users/john/Documents/Reports/Q3_Sales_Report.pdf
[2] Meeting_Notes.txt - /Users/john/Documents/Notes/Meeting_Notes.txt

This helps users verify the information in the original documents."""


# ============================================================================
# Error Handling Templates
# ============================================================================

NO_CONTEXT_FOUND = """I couldn't find any relevant information in your indexed documents to answer this question.

Suggestions:
1. Make sure you've indexed the directories containing relevant documents
2. Try rephrasing your question with different keywords
3. Add more documents to your indexed directories if needed

You can add directories through the "Add" button in the sidebar, or ask me to help you find related documents."""


INSUFFICIENT_CONTEXT = """I found some related information in your documents, but it doesn't fully answer your question.

What I found:
{partial_info}

To get a complete answer, you might want to:
1. Add more comprehensive documents to your index
2. Rephrase your question to be more specific
3. Ask me to search for related topics

Would you like me to help with any of these?"""


# ============================================================================
# User Guidance Templates
# ============================================================================

FIRST_MESSAGE_GUIDANCE = """👋 Welcome to InsightOS!

I can help you:
- Search through your indexed documents
- Answer questions based on your files
- Find specific information quickly
- Provide citations so you can verify sources

Try asking me:
- "What are the key points in my meeting notes?"
- "Summarize the quarterly report"
- "Find information about [topic] in my documents"

What would you like to know?"""


EMPTY_INDEX_MESSAGE = """It looks like you haven't indexed any documents yet.

To get started:
1. Click the "Add" button in the sidebar
2. Select a directory containing your documents
3. Wait for indexing to complete
4. Then ask me questions about your documents!

I can search through PDFs, Word documents, text files, code files, and many other formats."""


# ============================================================================
# Helper Functions
# ============================================================================

def get_system_prompt(use_tools: bool = False) -> str:
    """
    Get appropriate system prompt
    
    Args:
        use_tools: Whether tools are enabled
    
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPT_WITH_TOOLS if use_tools else SYSTEM_PROMPT


def format_no_results_message(query: str, num_indexed_files: int) -> str:
    """
    Format message when no results are found
    
    Args:
        query: User's query
        num_indexed_files: Number of files in index
    
    Returns:
        Formatted message
    """
    if num_indexed_files == 0:
        return EMPTY_INDEX_MESSAGE
    
    return f"""I searched through {num_indexed_files} indexed files but couldn't find relevant information about "{query}".

Try:
- Using different keywords or rephrasing your question
- Making sure the relevant documents are indexed
- Adding more directories if the information might be in other files

Would you like me to help you refine your search?"""


def format_error_message(error_type: str, details: str = "") -> str:
    """
    Format error message for user
    
    Args:
        error_type: Type of error
        details: Error details
    
    Returns:
        User-friendly error message
    """
    error_messages = {
        'api_error': "I encountered an error communicating with the AI service. Please check your API key and try again.",
        'index_error': "There was an error accessing the document index. Please try re-indexing your documents.",
        'tool_error': f"I encountered an error using a tool: {details}",
        'permission_error': "I don't have permission to access that file or directory.",
        'network_error': "I couldn't connect to the AI service. Please check your internet connection.",
    }
    
    return error_messages.get(error_type, f"An unexpected error occurred: {details}")


# ============================================================================
# Advanced Templates
# ============================================================================

def format_multi_step_response(
    steps: List[Dict[str, str]],
    final_answer: str
) -> str:
    """
    Format response that required multiple steps
    
    Args:
        steps: List of steps taken (e.g., tool calls)
        final_answer: Final answer
    
    Returns:
        Formatted response
    """
    steps_text = "\n".join([
        f"{i+1}. {step['description']}: {step['result']}"
        for i, step in enumerate(steps)
    ])
    
    return f"""Here's how I found the answer:

{steps_text}

{final_answer}"""


def format_clarification_request(
    ambiguous_term: str,
    options: List[str]
) -> str:
    """
    Request clarification from user
    
    Args:
        ambiguous_term: The ambiguous term
        options: Possible interpretations
    
    Returns:
        Clarification request
    """
    options_text = "\n".join([f"• {opt}" for opt in options])
    
    return f"""I found multiple possible meanings for "{ambiguous_term}":

{options_text}

Which one are you asking about?"""


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    'SYSTEM_PROMPT',
    'SYSTEM_PROMPT_WITH_TOOLS',
    'CITATION_INSTRUCTION',
    'NO_CONTEXT_FOUND',
    'INSUFFICIENT_CONTEXT',
    'FIRST_MESSAGE_GUIDANCE',
    'EMPTY_INDEX_MESSAGE',
    'get_system_prompt',
    'format_rag_context',
    'format_rag_context_with_conversation',
    'format_tool_result',
    'format_no_results_message',
    'format_error_message',
    'format_multi_step_response',
    'format_clarification_request',
]