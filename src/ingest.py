import os
from unstructured.partition.pdf import partition_pdf
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_pdf_elements(file_path, output_image_dir):
    print(f"--- Parsing {file_path} ---")

    # 1. Extract Raw Elements (No chunking yet)
    # We removed 'chunking_strategy="by_title"' so we get the raw pieces first.
    raw_pdf_elements = partition_pdf(
        filename=file_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        image_output_dir_path=output_image_dir,
    )

    # 2. Separate Tables from Text
    # We want to keep tables whole, but split the long text.
    raw_text = ""
    table_elements = []

    for element in raw_pdf_elements:
        if "Table" in str(type(element)):
            table_elements.append(str(element))
        else:
            # Combine all other text (titles, paragraphs) into one long string
            raw_text += str(element) + "\n\n"

    # 3. Apply LangChain Splitter (The "Brain" of the operation)
    # This is where we define the overlap to catch the missing details.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,      # Big enough to hold a full financial section
        chunk_overlap=400,    # 400 chars overlap ensures no sentence is lost between chunks
        separators=["\n\n", "\n", " ", ""]
    )

    text_elements = text_splitter.split_text(raw_text)

    print(f"--- Found {len(text_elements)} text chunks and {len(table_elements)} tables ---")
    return text_elements, table_elements
