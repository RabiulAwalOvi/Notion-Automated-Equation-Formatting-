
# Notion Equation Rendering Enhancement

This script enhances equation rendering in Notion by identifying LaTeX equations pasted into a Notion page and converting them into a format compatible with Notion's native equation blocks. It ensures proper handling of mathematical expressions, retaining formatting while addressing potential issues with colon placement and preserving text structure.

---

## **Purpose**

When pasting LaTeX equations into Notion, users often encounter rendering inconsistencies or formatting issues, particularly when transitioning between text and equations. This script solves these problems by:

1. **Automated Equation Conversion**: Converts various LaTeX equation formats (e.g., `$$...$$`, `\[...\]`, `\begin{equation}...\end{equation}`) into Notion's equation blocks.
2. **Colon Preservation**: Ensures colons before or after equations remain appropriately formatted.
3. **Seamless Integration**: Maintains the structure of Notion blocks, including text, equations, and other content.
4. **Recursive Processing**: Handles nested blocks and child blocks in complex Notion pages.

---

## **Integration with Notion**

### **Requirements**
1. A Notion integration with access to the target page.
2. Python installed on your system.
3. Dependencies: `requests` and `re`.

### **Setup**
1. Create a Notion integration and get its **API Key**.
2. Share the target Notion page with the integration's email.
3. Clone this repository and install dependencies:

   ```bash
   pip install requests


4. Update the following configuration in the script:
   - Replace `NOTION_API_KEY` with your Notion integration API key.
   - Replace `PAGE_URL` with the URL of the Notion page to process.

### **Running the Script**
Run the script using:

```bash
python <script_name>.py
```

The script will:
1. Parse the Notion page URL to extract the page ID.
2. Fetch all blocks from the page.
3. Identify blocks containing LaTeX equations needing updates.
4. Convert and update these blocks with Notion-compatible equation formats.

---

## **Code Overview**

### **Key Functions**
1. **`parse_page_url(notion_url: str) -> str`**  
   Extracts the page ID from the provided Notion URL.

2. **`get_all_blocks(block_id: str)`**  
   Recursively fetches all blocks (and their children) from a Notion page.

3. **`extract_block_content(block)`**  
   Extracts text and equation content from a block.

4. **`needs_equation_update(block)`**  
   Checks if a block contains LaTeX equations needing conversion.

5. **`update_block_equations(block)`**  
   Converts LaTeX equations to Notion's equation format, handling text and colons.

6. **`process_blocks(page_id: str)`**  
   Iterates through all blocks, updating equations where necessary.

### **Execution Flow**
The `main` function orchestrates the process:
- Parses the Notion page URL.
- Processes all blocks, updating equations as needed.
- Outputs completion status.

---

## **Limitations**
1. Assumes the Notion page is shared with the integration.
2. Only processes blocks with LaTeX equations in specific formats.
3. May require updates for new Notion API versions.

---

## **Example Use Case**
A user has a Notion page containing:

```
E=mc^2 is represented as:
\[ E = mc^2 \]
```

After running the script, it converts to:

```
E=mc^2 is represented as:
$$E = mc^2$$
```

This ensures equations render correctly in Notion.

---



This README file provides clear instructions on the purpose, setup, integration, and usage of the script while maintaining a professional tone for a GitHub repository. Let me know if you'd like further refinements!

`Slow process for LARGE Notion Page. Make It Faster If u are a devoloper and Let me Know`
