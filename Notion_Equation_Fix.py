
import requests
import re

# ==========================
# Configuration
# ==========================
NOTION_API_KEY = "Insert Your Notion Integration API Key Here"
PAGE_URL = "Enter your page URL here"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def parse_page_url(notion_url: str) -> str:
    """Extract Notion page ID from URL"""
    match = re.search(r'[0-9a-fA-F]{32}', notion_url.replace("-", ""))
    if match:
        raw_id = match.group(0)
        return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    raise ValueError("Invalid Notion URL.")

def get_all_blocks(block_id: str):
    """Recursively fetch all blocks in a page"""
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
    """Extract combined text content from a block"""
    content = []
    block_type = block.get('type', 'paragraph')
    
    if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 
                     'quote', 'bulleted_list_item', 'numbered_list_item']:
        for rt in block.get(block_type, {}).get('rich_text', []):
            if rt.get('type') == 'text':
                content.append(rt['text']['content'])
            elif rt.get('type') == 'equation':
                content.append(f"$${rt['equation']['expression']}$$")
    
    return '\n'.join(content)

def needs_equation_update(block):
    """Check if block contains LaTeX equations needing conversion"""
    if block['type'] in ['image', 'video', 'audio', 'file']:
        return False
    
    content = extract_block_content(block)
    patterns = [
        r'\$\$.*?\$\$',
        r'\\\[.*?\\\]',
        r'\\\(.*?\\\)',
        r'\\begin\{equation\}.*?\\end\{equation\}',
        r'\\begin\{align\*?\}.*?\\end\{align\*?\}'
    ]
    return any(re.search(p, content, re.DOTALL) for p in patterns)

def create_text_element(text):
    """Create properly formatted text element"""
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
    """Convert LaTeX equations to Notion format with colon preservation"""
    block_type = block['type']
    original_content = extract_block_content(block)
    new_rich_text = []
    
    equation_pattern = re.compile(
        r'(?s)(\$\$(.*?)\$\$|\\\[(.*?)\\\]|\\\((.*?)\\\)|'
        r'\\begin\{equation\}(.*?)\\end\{equation\}|'
        r'\\begin\{align\*?\}(.*?)\\end\{align\*?\})'
    )
    
    last_pos = 0
    for match in equation_pattern.finditer(original_content):
        start, end = match.start(), match.end()
        full_match = match.group(0)
        
        # Handle text before equation
        if start > last_pos:
            pre_text = original_content[last_pos:start]
            
            # Check for trailing colon
            if pre_text.endswith(':'):
                new_rich_text.append(create_text_element(pre_text[:-1]))
                new_rich_text.append(create_text_element(':'))
            else:
                new_rich_text.append(create_text_element(pre_text))
        
        # Extract equation content
        expr = next((g for g in match.groups()[1:] if g), '').strip()
        new_rich_text.append({
            "type": "equation",
            "equation": {"expression": expr}
        })
        
        last_pos = end
    
    # Handle remaining text after last equation
    if last_pos < len(original_content):
        post_text = original_content[last_pos:]
        
        # Handle leading colon
        if post_text.startswith(':'):
            if new_rich_text and new_rich_text[-1]['type'] == 'text':
                new_rich_text[-1]['text']['content'] += ':'
                post_text = post_text[1:]
            else:
                new_rich_text.append(create_text_element(':'))
                post_text = post_text[1:]
        
        if post_text:
            new_rich_text.append(create_text_element(post_text))
    
    # Preserve original block structure
    return {
        "type": block_type,
        block_type: {
            "rich_text": new_rich_text,
            **({} if block_type == 'paragraph' else 
               block[block_type].get('children', {}))
        }
    }

def process_blocks(page_id: str):
    """Process all blocks while preserving formatting and media"""
    blocks = get_all_blocks(page_id)
    
    for block in blocks:
        if not needs_equation_update(block):
            continue
            
        try:
            updated_block = update_block_equations(block)
            response = requests.patch(
                f"https://api.notion.com/v1/blocks/{block['id']}",
                headers=HEADERS,
                json=updated_block
            )
            response.raise_for_status()
            print(f"Updated block: {block['id']}")
        except Exception as e:
            print(f"Error updating block {block['id']}: {str(e)}")

def main():
    """Main execution flow"""
    page_id = parse_page_url(PAGE_URL)
    print(f"Processing page: {page_id}")
    process_blocks(page_id)
    print("Operation completed. Check your Notion page!")

if __name__ == "__main__":
    main()
