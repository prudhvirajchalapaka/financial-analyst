import os
from unstructured.partition.pdf import partition_pdf
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_pdf_elements(file_path: str, output_image_dir: str) -> tuple[list[str], list[str]]:
    """
    Parse PDF and extract text elements and tables.
    
    Args:
        file_path: Path to the PDF file
        output_image_dir: Directory to save extracted images
        
    Returns:
        Tuple of (text_chunks, table_elements)
    """
    print(f"--- Parsing {file_path} ---")

    # Extract Raw Elements
    raw_pdf_elements = partition_pdf(
        filename=file_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        image_output_dir_path=output_image_dir,
    )

    # Separate Tables from Text
    raw_text = ""
    table_elements = []

    for element in raw_pdf_elements:
        if "Table" in str(type(element)):
            table_elements.append(str(element))
        else:
            raw_text += str(element) + "\n\n"

    # Apply LangChain Splitter for optimal chunk sizes
    # Optimized for financial reports: keep paragraphs together, split by sentences if needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,      # Slightly smaller to be more precise
        chunk_overlap=300,    # Good overlap for context
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    text_elements = text_splitter.split_text(raw_text)

    # Filter out very short chunks which are often noise (headers/footers)
    text_elements = [t for t in text_elements if len(t) > 100]

    print(f"--- Found {len(text_elements)} text chunks and {len(table_elements)} tables ---")
    return text_elements, table_elements
