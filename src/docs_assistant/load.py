from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langchain_core.documents import Document
from typing import List, Set, Optional


def get_docs_urls(base_url: str = "https://microsoft.github.io/autogen/0.2/docs/",
                  max_urls: Optional[int] = None) -> List[str]:
    """
    Extract all URLs from a documentation website using LangChain's AsyncChromiumLoader.
    
    Args:
        base_url: The base URL of the documentation site.
        max_urls: Maximum number of URLs to collect. If None, collects all URLs.
        
    Returns:
        List of all URLs found starting with the base_url.
    """
    to_visit = [base_url]
    visited: Set[str] = set()
    queued: Set[str] = {base_url}
    base_domain = urlparse(base_url).netloc
    
    while to_visit:
        
        # Check if reached the maximum number of URLs
        if max_urls is not None and len(visited) >= max_urls:
            break

        # Get next batch of URLs
        current_batch = to_visit[:10]
        to_visit = to_visit[10:]
        
        # Skip already visited URLs
        current_batch = [url for url in current_batch if url not in visited]
        if not current_batch:
            continue
        
        # Load pages with AsyncChromiumLoader
        loader = AsyncChromiumLoader(current_batch, user_agent="DocsAssistant")
        docs = loader.load()
        
        for doc in docs:
            current_url = doc.metadata.get('source')
            visited.add(current_url)

            # Extract links from HTML
            soup = BeautifulSoup(doc.page_content, 'html.parser')
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                full_url = urljoin(current_url, href)

                # Remove fragment and normalize URL
                full_url = full_url.split('#')[0]
                if full_url.endswith('/'):
                    full_url = full_url[:-1]
                
                # New URL?
                if full_url in visited or full_url in queued:
                    continue
                
                # Only keep URLs from same site and matching base pattern
                if (full_url.startswith(base_url) and urlparse(full_url).netloc == base_domain):
                    to_visit.append(full_url)
                    queued.add(full_url)
    
    # If max_urls is specified, return no. urls as requested
    if max_urls is not None and len(visited) > max_urls:
        return sorted(list(visited))[:max_urls]
    return sorted(list(visited))


def load_docs(base_url: str = "https://microsoft.github.io/autogen/0.2/docs/",
              max_urls: Optional[int] = None) -> List[Document]:
    """
    Load documentation content from docs website.

    Args:
        base_url: The base URL of the documentation site to crawl.
        max_urls: Maximum number of URLs to collect. If None, collects all docs URLs.
    
    Returns:
        List of Document objects containing the content of all documentation pages.
    """
    docs_urls = get_docs_urls(base_url, max_urls)
    return DoclingLoader(
        file_path=docs_urls,
        export_type=ExportType.MARKDOWN,
    ).load()

