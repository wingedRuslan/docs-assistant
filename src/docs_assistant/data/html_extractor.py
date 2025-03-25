"""
HTML Content Extractor

A module for extracting content from HTML files and saving as plain text
while preserving directory structure, with flexible extraction strategies.
"""

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
    
    def extract_content(self, html_content):
        """
        Extract content from HTML using the selected strategy.
        
        Args:
            html_content (str): HTML content
        
        Returns:
            str: Extracted text content
        """
        # LLM-only mode
        if self.extraction_mode == self.LLM_ONLY:
            return self.extract_content_openai(html_content)
        
        # Rule-based mode
        if self.extraction_mode == self.RULE_BASED:
            return self.extract_content_rule_based(html_content)
        
        # Hybrid mode
        if self.extraction_mode == self.HYBRID:
            # First try rule-based extraction
            extracted_content = self.extract_content_rule_based(html_content)
            
            # Check if the rule-based extraction was successful
            content_is_valid = (
                extracted_content and 
                len(extracted_content) >= self.min_content_length and
                not extracted_content.isspace()
            )
            
            # If rule-based extraction failed or is suspicious, try OpenAI fallback
            if not content_is_valid:
                logger.info("Rule-based extraction produced insufficient content. Trying OpenAI fallback...")
                openai_content = self.extract_content_openai(html_content)
                
                if openai_content and len(openai_content) > len(extracted_content):
                    logger.info("Using OpenAI extracted content (better quality)")
                    return openai_content            
            return extracted_content
    
    def process_file(self, html_path):
        """
        Process a single HTML file and save its content.
        
        Args:
            html_path (Path): Path to the HTML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine output path
            rel_path = html_path.relative_to(self.input_dir)
            output_path = self.output_dir / rel_path.with_suffix('.txt')
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and process HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            extracted_content = self.extract_content(html_content)

            if not extracted_content:
                logger.info(f"Warning: No content extracted from {html_path}")
                return False
            
            # Write output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_content)
            
            logger.info(f"Processed: {html_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {html_path}: {e}")
            return False
    
