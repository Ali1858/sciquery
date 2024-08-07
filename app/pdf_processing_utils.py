import os
import re
import json
from typing import List, Dict, Tuple, Optional

import pymupdf
from config import DEBUG

def is_int(s: str) -> bool:
    "Check if the input string can be converted to an integer."
    try:
        int(s)
        return True
    except ValueError:
        return False


def parse_reference(reference: str) -> Dict[str, str]:
    "Parse a reference string to extract authors, year, title, and publication details."
    
    # Extract authors
    authors_match = re.match(r'^(.*?)\.', reference)
    authors = authors_match.group(1) if authors_match else 'unknown'
    # Remove authors from the citation
    reference = re.sub(r'^.*?\.\s*', '', reference)
    
    # Extract year
    year_match = re.search(r'\b(19|20)\d{2}\b', reference)
    year = year_match.group(0) if year_match else 'unknown'
    # Remove year from the citation
    reference = re.sub(r'\b(19|20)\d{2}\b', '', reference)
    
    # Extract title
    title_match = re.match(r'(.*?)\.\s*', reference)
    title = title_match.group(1) if title_match else 'unknown'
    # Remove title from the citation
    reference = re.sub(r'^.*?\.\s*', '', reference)
    
    # Extract publication details
    publication = reference.strip()
    
    return {
        'authors': authors,
        'title': title,
        'year': year,
        'publication': publication
    }


def split_citations(reference: str) -> str:
    "Split reference text by citation and join them again by new line. This help regex to extract individual citations"
    pattern = re.compile(r'(?<=\.)(?=\s*\[\d+\])')
    parts = pattern.split(reference)
    return "\n".join([part.strip() for part in parts if part.strip()])


def extract_bibliography(text_blocks: List[str]) -> Tuple[Optional[int], Optional[Dict[str, Dict[str, str]]]]:
    """Extract bibliography from a list of text blocks.

    Returns:
        tuple: Tuple containing the index of the reference block and a dictionary of bibliography.
    """

    # List of possible reference section headings
    reference_headings = [
        r'^Reference\b', 
        r'^References\b', 
        r'^References:\b'
    ]
    # Compile the regex patterns
    reference_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in reference_headings]

    reference_block_found = False
    # Iterate through blocks and find the starting index of reference section
    for i, block in enumerate(text_blocks):
        for pattern in reference_patterns:
            if pattern.search(block):
                reference_block_found = True
                break
        if reference_block_found:
            block_idx = i
            break

    if not reference_block_found:
        return None, None
    
    references = split_citations(" ".join(text_blocks[block_idx:]))
    # Step 1: Check for NeurIPS style citations
    citation_pattern = re.compile(r'\[\d+\]') #[<int>]
    if not citation_pattern.search(references):
        return block_idx,None 
    
    # Step 2: Extract bibliography
    # Assuming the bibliography section starts with a citation key in the format [<int>]
    bibliography_pattern = re.compile(r'\[(\d+)\]\s+(.*?)\n(?=\[\d+\]\s+|\Z)', re.DOTALL) #pattern to match each citation. using ChatGPT 
    
    bibliography = {}
    for match in bibliography_pattern.finditer(references):
        citation_key = match.group(1)
        reference_detail = match.group(2).strip()
        bibliography[f'[{citation_key}]'] = parse_reference(reference_detail.replace('\n'," ")) #parse each metadata of a citation
    return block_idx,bibliography


def chunk_texts(sections: List[str], metadata: Dict[str,str], min_words: int = 500, buffer: int = 50) -> List[str]:
    "Split and combine sections of text into chunks based on a minimum word count."
    passage_delimeter = "\n"
    
    def word_count(text):
        return len(text.split())
    
    #split bigger section into small passages.
    def split_text(section):
        passages = section.split(passage_delimeter)
        heading = passages[0]
        current_chunk = ""
        chunks = []

        for passage in passages[1:]:
            if word_count(current_chunk+passage+passage_delimeter) <= min_words+buffer: # going little over min_words is ok, so that we avoid chunking passage itself.
                current_chunk += passage+passage_delimeter
            elif current_chunk:
                chunks.append(f'{heading}\n{current_chunk}'.strip())
                current_chunk = passage+passage_delimeter
           
        if current_chunk:
            chunks.append(f'{heading}\n{current_chunk}'.strip())
        return chunks

    # combine passage for bigger chunks.
    def combine_texts(small_passages,metadata):
        result_chunks = []
        current_chunk = ""

        for small_passage in small_passages:
            if word_count(current_chunk+small_passage+passage_delimeter+passage_delimeter) <= min_words+buffer: # going little over min_words is ok, so that we avoid chunking passage itself.
                current_chunk += small_passage+passage_delimeter+passage_delimeter
            elif current_chunk:
                result_chunks.append({"passage":current_chunk.strip(),"file_metadata":metadata})
                current_chunk = small_passage + passage_delimeter+passage_delimeter
        if current_chunk:
            result_chunks.append({"passage":current_chunk.strip(),"file_metadata":metadata})
        return result_chunks

    small_passages = []

    # Step 1: Separate section into small passages
    for section in sections:
        if word_count(section) <= min_words+buffer:
            small_passages.append(section)
        else:
            small_passages.extend(split_text(section))

    # Step 2: Combine small chunks into larger chunks
    combined_chunks = combine_texts(small_passages,metadata)

    return combined_chunks


def manage_bib_json(json_file_path: str, operations: Dict[str, Dict[str, Dict[str, str]]]):
    """
    Manage Bibliograph JSON file: create if it doesn't exist, add/update a key-value pair, or delete a key.

    Args:
        json_file_path (str): Path to the JSON file.
        operations (Dict[str, Dict[str, str]]): Dictionary specifying the operations to be performed.
            {
                "add_or_update": {"key": "value"},
                "delete": {"key": ""}
            }
    """
    
    # Ensure the JSON file exists
    if not os.path.exists(json_file_path):
        with open(json_file_path, 'w') as file:
            json.dump({}, file)
    
    # Load the existing data from the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Perform add or update operations
    if "add_or_update" in operations:
        for key, value in operations["add_or_update"].items():
            data[key] = value
    
    # Perform delete operations
    if "delete" in operations:
        for key in operations["delete"].keys():
            if key in data:
                del data[key]
    
    # Save the updated data back to the JSON file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_sections(pdf_path: str) -> Tuple[List[str], Optional[Dict[str, Dict[str, str]]], Optional[Dict[str, str]]]:
    "Extract text sections from a PDF document, process them, and return sections, bibliography and file metadata."
    processed_blocks = [""]
    doc = pymupdf.open(pdf_path)
    metadata = {"title":doc.metadata["title"], "pdf_path": pdf_path}

    for page in doc: # iterate the document pages
        blocks = page.get_text('blocks',flags=16)
        tabs = page.find_tables()  # detect the tables

        for block in blocks:
            if block[6] != 1: #ignore image blocks
                text_bbox = pymupdf.Rect(block[:4]) #bounding box of a text block

                intersect_with_table = False
                for tab in tabs:
                    table_bbox = pymupdf.Rect(tab.bbox) #bounding box of a table
                    if table_bbox.intersects(text_bbox):
                            intersect_with_table = True
                            break
                
                txt = block[4].replace("\n"," ")
                txt = txt.strip()        
                if intersect_with_table:
                    table_txt = block[4].replace('\n','* ').strip()
                    if table_txt == "* ".join([ x if x is not None else '' for x in tab.header.names]).strip(): #First heading cell
                        processed_blocks.append(f'Header: {table_txt} ')
                    else: #other concat to previous block
                        processed_blocks[len(processed_blocks)-1] += f'Cell: {table_txt} '
                elif len(txt.replace('\n',' ')) != 0 and not is_int(txt):
                    processed_blocks.append(txt)

    ref_block_idx,bibliography_dict = extract_bibliography(processed_blocks)
    if ref_block_idx:
        processed_blocks = processed_blocks[:ref_block_idx]

    first_section_found = False
    sections = []
    pattern = r'^(?:\d+(\.\d+)*)? [A-Z][a-zA-Z0-9\s\-():,]*$' #patter for [Number like 1 or 1.1 or 1.1.1 etc] #space [first capital letter][alphabets,numbers,few symbols]
    
    # We will split at section and passage level to avoid irrelevant chunks.
    # https://medium.com/@anuragmishra_27746/five-levels-of-chunking-strategies-in-rag-notes-from-gregs-video-7b735895694d#b123
    for txt in processed_blocks:
        if re.match(pattern,txt):
            heading = re.sub(r'^(?:\d+(\.\d+)*)? ', '', txt).strip() # remove section numbers
            sections.append(f'## {heading}')
            first_section_found = True
        elif first_section_found and (txt[0].islower() or not txt[0].isalnum()):
            sections[len(sections)-1] += f' {txt}' # No new line because most likely this block is part of previous passage
        elif first_section_found:
            sections[len(sections)-1] += f'\n{txt}' # new line because most likely a new passage.
            
    if DEBUG:
        print(f'Block extraction completed: PDF document at path {pdf_path} contains {len(processed_blocks)} blocks and {len(sections)} sections')
    return sections, bibliography_dict, metadata


def display_chunk(chunks: List[str]) -> None:
    "Display chunks"
    for i, chunk in enumerate(chunks):
        chunk = chunk["passage"]
        count = len(chunk.split())
        print(f"Chunk {i + 1} (Words: {count}):")
        print(chunk)
        print("-" * 50)
