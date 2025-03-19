"""
Browser-Based Documentation Crawler

Uses Playwright to crawl Single Page Applications (SPAs) by executing JavaScript
and extracting content and links from the fully rendered DOM.

This is particularly useful for modern documentation sites built with frameworks
like React, Vue, or Angular that require JavaScript to render content.
"""

import os
import argparse
import asyncio
import logging
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowserCrawler:
    """Crawler that uses a browser to properly render SPAs."""
    
    def __init__(self, base_url, output_dir, max_pages=100, wait_time=2, browser_type="chromium"):
        """
        Initialize the crawler.
        
        Args:
            base_url: Starting URL for crawling
            output_dir: Directory to save downloaded pages
            max_pages: Maximum number of pages to download
            wait_time: Time to wait for page to load (seconds)
            browser_type: Type of browser to use ("chromium", "firefox", or "webkit")
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.wait_time = wait_time
        self.browser_type = browser_type
        
        # Parse the base domain to limit crawling scope
        self.base_domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queued_urls = set()
        self.urls_to_visit = []
        
        # Start time for reporting
        self.start_time = None
    
    def get_file_path(self, url):
        """Convert URL to local file path."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Handle the root path
        if not path:
            return os.path.join(self.output_dir, "index.html")
        
        # Create path components
        file_path = os.path.join(self.output_dir, path)
        
        # Add .html extension if needed
        if not os.path.splitext(file_path)[1]:
            file_path += '.html'
        
        return file_path
    
    async def extract_links(self, page):
        """Extract all links from the current page."""
        # Wait for the page to be fully loaded with JavaScript execution
        await asyncio.sleep(self.wait_time)
        
        # Extract links from the fully rendered DOM
        links = await page.evaluate("""
            () => {
                // Find all links in the page
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .map(anchor => anchor.href)
                    .filter(href => href && href.startsWith('http'));
            }
        """)
        
        # Only keep links to the same domain and within our path scope
        filtered_links = []
        current_url = page.url
        current_base_url = current_url.split('#')[0]  # Remove any fragment from current URL
        
        for link in links:
            parsed = urlparse(link)
            
            # Only include links to the same domain
            if parsed.netloc != self.base_domain:
                continue
                
            # Check if the link is in the same path scope as our base_url
            if not link.startswith(self.base_url):
                continue
            
            # Get base link without fragment for visited check
            base_link = link.split('#')[0]

            # Skip fragment identifiers on the same page
            if base_link == current_base_url:
                continue

            # Add link if we haven't visited or queued its base URL
            if base_link not in self.visited_urls and base_link not in self.queued_urls:
                filtered_links.append(base_link)
                self.queued_urls.add(base_link)  
            
        
        logger.info(f"Found {len(filtered_links)} new links on {page.url}")
        return filtered_links
    
    async def save_page(self, page, url):
        """Save the fully rendered page content to a file."""
        file_path = self.get_file_path(url)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Get the fully rendered HTML content
        html_content = await page.content()
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"Saved: {file_path}")
        
        # [Optional] - save a screenshot for debugging or verification
        # screenshot_path = file_path.replace('.html', '.png')
        # await page.screenshot(path=screenshot_path, full_page=True)
    
    async def crawl(self):
        """Start the crawling process using a browser."""
        os.makedirs(self.output_dir, exist_ok=True)
        self.start_time = datetime.now()
        
        logger.info(f"Starting crawl from {self.base_url}")
        logger.info(f"Saving pages to {self.output_dir}")
        logger.info(f"Using {self.browser_type} browser")
        
        async with async_playwright() as p:
            # Select the browser type
            if self.browser_type == "firefox":
                browser_instance = p.firefox
            elif self.browser_type == "webkit":
                browser_instance = p.webkit
            else:
                browser_instance = p.chromium  # Default
            
            # Launch the browser
            browser = await browser_instance.launch()
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 Documentation Browser Crawler"
            )
            
            # Start with the base URL
            self.urls_to_visit = [self.base_url]
            self.queued_urls.add(self.base_url)
            page_count = 0
            
            try:
                while self.urls_to_visit and page_count < self.max_pages:
                    # Get the next URL
                    url = self.urls_to_visit.pop(0)
                    
                    # Skip if already visited
                    if url in self.visited_urls:
                        continue
                        
                    logger.info(f"Visiting {url} ({page_count + 1}/{self.max_pages})")
                    
                    try:
                        # Create a new page for each request to avoid state issues
                        page = await context.new_page()
                        
                        # Navigate to the URL with timeout and wait until network is idle
                        await page.goto(url, wait_until="networkidle")
                        
                        # Mark as visited
                        self.visited_urls.add(url)
                        page_count += 1
                        
                        # Save the page content
                        await self.save_page(page, url)
                        
                        # Extract links
                        new_links = await self.extract_links(page)
                        self.urls_to_visit.extend(new_links)
                        
                        # Close the page to free resources
                        await page.close()
                        
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                        
                        # Add to visited so we don't try again
                        self.visited_urls.add(url)
                        
                        # Close the page if it exists
                        try:
                            await page.close()
                        except:
                            pass
            
            finally:
                # Clean up resources
                await context.close()
                await browser.close()
        
        # Calculate elapsed time
        elapsed_time = datetime.now() - self.start_time
        
        # Create a summary report
        summary = {
            "base_url": self.base_url,
            "output_directory": self.output_dir,
            "pages_downloaded": len(self.visited_urls),
            "crawl_date": datetime.now().isoformat(),
            "elapsed_time_seconds": elapsed_time.total_seconds(),
            "visited_urls": sorted(list(self.visited_urls))
        }
        
        # Save the summary report
        summary_path = os.path.join(self.output_dir, "crawl_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Crawling complete. Downloaded {len(self.visited_urls)} pages in {elapsed_time}.")
        return self.visited_urls


async def crawl_docs(base_url, output_dir="./data/docs/", max_pages=100):
    """
    Helper function to crawl documentation using a BrowserCrawler.
    
    Args:
        base_url: Starting URL for the documentation
        output_dir: Directory to save documentation files
        max_pages: Maximum number of pages to download
    """
    crawler = BrowserCrawler(base_url, output_dir, max_pages)
    return await crawler.crawl()


if __name__ == "__main__":

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Browser-based documentation crawler for downloading documentation sites"
    )
    
    # Add arguments
    parser.add_argument(
        "--url", "-u", 
        required=True,
        help="Base URL of the documentation to crawl"
    )
    
    parser.add_argument(
        "--output", "-o", 
        default="./data/docs/",
        help="Directory to save downloaded documentation (default: ./data/docs/)"
    )
    
    parser.add_argument(
        "--max-pages", "-m", 
        type=int, 
        default=100,
        help="Maximum number of pages to download (default: 100)"
    )
        
    # Parse arguments
    args = parser.parse_args()
    
    # Run the crawler with provided arguments
    print(f"Starting crawler for: {args.url}")
    print(f"Saving to: {args.output}")
    
    asyncio.run(crawl_docs(
        base_url=args.url,
        output_dir=args.output,
        max_pages=args.max_pages,
        wait_time=args.wait_time
    ))
