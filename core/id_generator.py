import secrets


def generate_memory_id() -> str:
    """
    Generates a unique memory ID formatted as 'mem_' followed by 12 random hex characters.
    Example: 'mem_a3f89b12c4d5'
    """
    random_hex = secrets.token_hex(6)  # 6 bytes = 12 hex characters
    return f"mem_{random_hex}"


def generate_chunk_id(memory_id: str, chunk_index: int) -> str:
    """
    Generates a unique ID for a vector chunk associated with a memory.
    Example: 'mem_a3f89b12c4d5_chunk_0'
    """
    return f"{memory_id}_chunk_{chunk_index}"
