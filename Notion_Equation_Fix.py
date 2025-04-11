import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# Configuration
# ==========================
NOTION_API_KEY = "INSERT YOUR INTEGRATION API KEY HERE"
PAGE_URL = "Insert the Notion Page URL Here"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def parse_page_url(notion_url: str) -> str:
    """Extract Notion page ID from URL."""
    match = re.search(r'[0-9a-fA-F]{32}', notion_url.replace("-", ""))
    if match:
        raw_id = match.group(0)
        return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    raise ValueError("Invalid Notion URL.")

def get_all_blocks(block_id: str):
    """Recursively fetch all blocks in a page."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    all_blocks = []
    has_more, start_cursor = True, None
    
    while has_more:
        params = {"start_cursor": start_cursor} if start_cursor else {}
        response = requests.get(url, headers=HEADERS, params=params).json()
        results = response.get('results', [])
        
        for block in results:
            all_blocks.append(block)
            if block.get('has_children', False):
                all_blocks.extend(get_all_blocks(block['id']))
        
        has_more = response.get('has_more', False)
        start_cursor = response.get('next_cursor')
    
    return all_blocks

def extract_block_content(block):
    """Extract combined text content from a block."""
    content = []
    block_type = block.get('type', 'paragraph')

    if block_type in [
        'paragraph', 'heading_1', 'heading_2', 'heading_3',
        'quote', 'bulleted_list_item', 'numbered_list_item'
    ]:
        for rt in block.get(block_type, {}).get('rich_text', []):
            if rt.get('type') == 'text':
                content.append(rt['text']['content'])
            elif rt.get('type') == 'equation':
                content.append(f"$${rt['equation']['expression']}$$")

    return ''.join(content)

def needs_equation_update(block):
    """Check if block contains LaTeX equations needing conversion."""
    if block['type'] in ['image', 'video', 'audio', 'file']:
        return False

    content = extract_block_content(block)
    patterns = [
        r'\$\$.*?\$\$',  # $$ ... $$
        r'\\\[.*?\\\]',  # \[ ... \]
        r'\\\(.*?\\\)',  # \( ... \)
        r'\\begin\{equation\}.*?\\end\{equation\}',
        r'\\begin\{align\*?\}.*?\\end\{align\*?\}'
    ]
    return any(re.search(p, content, re.DOTALL) for p in patterns)

def create_text_element(text):
    """Create a properly formatted text element."""
    return {
        "type": "text",
        "text": {"content": text},
        "annotations": {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default"
        }
    }

def update_block_equations(block):
    """Convert LaTeX equations to Notion format."""
    block_type = block['type']
    original_content = extract_block_content(block)
    new_rich_text = []
    
    # Unified equation pattern with capture groups
    equation_pattern = re.compile(
        r'(?s)(\$\$(.*?)\$\$|\\\[(.*?)\\\]|\\\((.*?)\\\)|'
        r'\\begin\{equation\}(.*?)\\end\{equation\}|'
        r'\\begin\{align\*?\}(.*?)\\end\{align\*?\})'
    )
    
    last_pos = 0
    for match in equation_pattern.finditer(original_content):
        start, end = match.start(), match.end()
        
        # Add preceding text if any
        if start > last_pos:
            text_segment = original_content[last_pos:start]
            if text_segment.strip():
                new_rich_text.append(create_text_element(text_segment))
        
        # Extract matched equation text
        expr = next((g for g in match.groups()[1:] if g), '').strip()
        new_rich_text.append({
            "type": "equation",
            "equation": {"expression": expr}
        })
        
        last_pos = end

    # Add remaining text
    if last_pos < len(original_content):
        text_segment = original_content[last_pos:]
        if text_segment.strip():
            new_rich_text.append(create_text_element(text_segment))
    
    # Build the updated block payload
    new_block_payload = {
        "type": block_type,
        block_type: {
            "rich_text": new_rich_text
        }
    }
    # If the original block has children object, preserve them
    if "children" in block.get(block_type, {}):
        new_block_payload[block_type]["children"] = block[block_type]["children"]
    
    return new_block_payload

def patch_single_block(block, max_retries=3, initial_backoff=0.5):
    """
    Send a PATCH request for a single block with retry on 409 Conflict.
    """
    updated_block = update_block_equations(block)
    backoff = initial_backoff

    for attempt in range(max_retries):
        try:
            response = requests.patch(
                f"https://api.notion.com/v1/blocks/{block['id']}",
                headers=HEADERS,
                json=updated_block
            )
            # If 409, we do a backoff and retry
            if response.status_code == 409:
                msg = f"409 Conflict. Retrying block {block['id']} (attempt {attempt+1}/{max_retries})..."
                print(msg)
                time.sleep(backoff)
                backoff *= 2
                continue

            response.raise_for_status()
            return f"Successfully updated block: {block['id']}"
        
        except requests.exceptions.RequestException as ex:
            # If it's not 409 or we exhaust attempts, fail
            msg = f"Failed to update block {block['id']}: {ex}"
            # If we've not used up our retries, keep going
            if attempt < max_retries - 1:
                print(f"{msg} -> Retrying in {backoff} seconds.")
                time.sleep(backoff)
                backoff *= 2
            else:
                return msg

    return f"Failed to update block {block['id']} after {max_retries} retries."

def process_blocks(page_id: str, max_workers=50):
    """Process all blocks and update them in parallel."""
    blocks = get_all_blocks(page_id)
    blocks_to_update = [b for b in blocks if needs_equation_update(b)]

    if not blocks_to_update:
        print("No blocks need equation conversion.")
        return

    results = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(patch_single_block, block): block 
            for block in blocks_to_update
        }
        
        for future in as_completed(future_map):
            block = future_map[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(f"Failed to update block {block['id']}: {e}")
    
    # Print results
    for r in results:
        print(r)

def main():
    """Main entry point."""
    page_id = parse_page_url(PAGE_URL)
    print(f"Processing page: {page_id}")
    process_blocks(page_id, max_workers=5)
    print("Equation conversion complete!")

if __name__ == "__main__":
    main()
