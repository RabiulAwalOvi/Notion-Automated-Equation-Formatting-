# Notion Equation Formatter

Automatically convert LaTeX equations in Notion pages to proper KaTeX formatting for seamless integration of AI-generated content.

## Features
- 🔍 Scans Notion pages for LaTeX equations
- 🔄 Converts `\(...\)`, `\[...\]`, and `equation`/`align` environments to Notion-compatible `$$...$$` format
- ⚡ Processes blocks in parallel for faster conversion
- 🔄 Preserves original text formatting while updating equations

## Prerequisites
- Python 3.6+
- Notion account
- [Notion Integration](https://www.notion.so/my-integrations) with:
  - **Internal Integration Token**
  - Page permissions granted to your integration

## Setup Instructions

1. **Create Notion Integration**
   - Go to [My Integrations](https://www.notion.so/my-integrations)
   - Create new integration named "Equation_Fixer"
   - Copy your **Internal Integration Secret**

2. **Prepare Notion Page**
   - Create a dedicated page (e.g., "Eqn_Fix")
   - Share the page with your integration via `•••` → `Add connections`

3. **Configure Script**
   ```python
   # ==========================
   # Configuration
   # ==========================
   NOTION_API_KEY = "your_integration_secret_here"
   PAGE_URL = "your_notion_page_url_here"
   ```

## Installation
```bash
git clone https://github.com/yourusername/notion-equation-formatter.git
cd notion-equation-formatter
pip install requests
```

## Usage
1. Paste AI-generated content into your dedicated Notion page using `Ctrl/Cmd+Shift+V`
2. Run the script:
   ```bash
   python notion_equation_formatter.py
   ```
3. Wait for processing (typically 5-30 seconds depending on content length)
4. Copy fixed content to your final notes location

## How It Works
1. **Page Analysis**  
   Fetches all blocks from the target Notion page through the API

2. **Equation Detection**  
   Identifies blocks containing LaTeX equations using regex patterns

3. **Format Conversion**  
   - Converts inline equations (`\(...\)`) to `$$...$$`
   - Converts display equations (`\[...\]`, `equation`/`align` environments) to `$$...$$`
   - Preserves text formatting and non-equation content

4. **Parallel Processing**  
   Updates blocks concurrently using thread pooling for faster processing

## Limitations
- Complex LaTeX macros may require manual adjustment
- Rate limited by Notion's API (≈3-5 requests/second)
- Equations in nested blocks (e.g., toggle lists) might need multiple runs

## Troubleshooting
- `401 Unauthorized`: Verify integration secret and page sharing
- `404 Not Found`: Check page URL formatting
- Equations not updating: Ensure content was pasted as unformatted text

**Pro Tip:** Use this with AI-generated STEM content from ChatGPT/Claude for seamless technical note-taking in Notion! 🚀
