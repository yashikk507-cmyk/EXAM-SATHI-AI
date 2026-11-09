
import re


def split_text(text, chunk_size=500, overlap=100):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    # Find all page markers and their positions
    page_pattern = r"\[Page (\d+)\]"
    matches = list(re.finditer(page_pattern, text))

    chunks = []

    # If no page markers exist, use normal chunking
    if not matches:
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start += chunk_size - overlap

        return chunks

    # Process each page separately
    for i, match in enumerate(matches):

        page_number = int(match.group(1))

        page_start = match.end()

        if i + 1 < len(matches):
            page_end = matches[i + 1].start()
        else:
            page_end = len(text)

        page_text = text[page_start:page_end].strip()

        # Split this page into smaller chunks
        start = 0

        while start < len(page_text):

            end = start + chunk_size
            content = page_text[start:end]

            if content.strip():

                chunk = f"[Page {page_number}]\n{content}"

                chunks.append(chunk)

            start += chunk_size - overlap

    return chunks
