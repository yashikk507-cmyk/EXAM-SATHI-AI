
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    """
    Extract text from an uploaded PDF.
    Returns the extracted text as a string.
    """

    try:
        reader = PdfReader(pdf_path)

        if reader.is_encrypted:
            raise ValueError("This PDF is password protected.")

        extracted_text = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()

            if page_text:
                extracted_text.append(
                    f"\n[Page {page_number}]\n{page_text}"
                )

        full_text = "\n".join(extracted_text).strip()

        if not full_text:
            raise ValueError(
                "No readable text found. This may be a scanned PDF."
            )

        return full_text

    except Exception as error:
        raise RuntimeError(f"PDF processing failed: {error}")
