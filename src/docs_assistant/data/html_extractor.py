import os
import re
import logging
import html2text
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HTMLContentExtractor:
    """Extract readable content from HTML files."""

    # Extraction modes
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    LLM_ONLY = "llm_only"
    
    def __init__(self, input_dir, output_dir, extraction_mode="hybrid", min_content_length=250):
        """
        Initialize the extractor.
        
        Args:
            input_dir (str): Directory containing HTML files
            output_dir (str): Directory to save extracted text files
            extraction_mode (str): One of "rule_based", "hybrid", or "llm_only"
            min_content_length (int): Minimum length for valid content extraction
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.extraction_mode = extraction_mode
        self.min_content_length = min_content_length
        self.openai_calls = 0
        
        # Initialize OpenAI client if needed
        if extraction_mode in [self.HYBRID, self.LLM_ONLY]:
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Initialize HTML2Text converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0  # No wrapping
        self.h2t.ignore_images = False
        self.h2t.protect_links = True
        self.h2t.unicode_snob = True

        logger.info(f"Initialized HTML Content Extractor with mode: {extraction_mode}")

    
    def extract_content_rule_based(self, html_content):
        """
        Extract content from HTML using rule-based approach (via html tags).
        
        Args:
            html_content (str): HTML content
        
        Returns:
            str: Extracted text content
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove irrelevant elements
        for element in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
            element.decompose()
        
        # Find main content using multiple strategies
        content = None
        
        # Strategy 1: Try semantic HTML5 tags
        for tag in ['article', 'main', 'div[role="main"]']:
            if tag.startswith('div'):
                try:
                    attr, value = re.findall(r'(\w+)\[(\w+)="(\w+)"\]', tag)[0][0:2]
                    content = soup.find(attr, {value: True})
                except (IndexError, ValueError):
                    continue
            else:
                content = soup.find(tag)
            
            if content and len(content.get_text(strip=True)) > 100:
                break
        
        # Strategy 2: Try common content classes
        if not content:
            for class_name in ['content', 'document-content', 'markdown', 'theme-doc-markdown']:
                content = soup.find(class_=class_name)
                if content and len(content.get_text(strip=True)) > 100:
                    break
        
        # Strategy 3: Get div with most content
        if not content:
            divs = soup.find_all('div')
            if divs:
                content = max(divs, key=lambda x: len(x.get_text(strip=True)))
        
        # Strategy 4: Fallback to body
        if not content or len(content.get_text(strip=True)) < 100:
            content = soup.body
        
        # Convert to markdown text
        markdown_content = self.h2t.handle(str(content))
        
        # Clean up the text
        cleaned_text = re.sub(r'\n{3,}', '\n\n', markdown_content)  # Remove excessive newlines
        
        return cleaned_text
    
    def extract_content_openai(self, html_content):
        """
        Extract content from HTML using OpenAI LLM call.
        
        Args:
            html_content (str): HTML content
        
        Returns:
            str: Extracted text content
        """
        try:
            
            # Make OpenAI API call
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant to extract the main content from HTML file. "
                                  "Extract only the valuable content - ignore navigation bars, headers, footers, "
                                  "and other UI elements. Format the content in Markdown."
                    },
                    {
                        "role": "user",
                        "content": f"Here is the HTML content. Please extract just the main content, "
                                   f"formatted as Markdown:\n\n{html_content}"
                    }
                ]
            )
            self.openai_calls += 1
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return ""
    
