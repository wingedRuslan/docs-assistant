# Documentation Assistant

## Browser-Based Documentation Crawler

Uses a browser-based approach ([crawler](./src/docs_assistant/utils/browser_docs_crawler.py)) to download documentation sites, including modern Single Page Applications (SPAs) that traditional crawlers can't handle.

* **SPA Support:** Properly renders JavaScript-heavy documentation sites by executing JavaScript in a real browser (e.g. autogen)
* **Works with Traditional Sites:** Also handles classic HTML documentation efficiently (e.g. pandas)
* **Navigation:** Navigates and downloads complete documentation structures

The crawler requires Playwright for browser automation:

```bash
# Install the crawler dependencies
pip install playwright
# Install browser binaries (required)
python -m playwright install
# Run docs crawler
python src/docs_assistant/utils/browser_docs_crawler.py -url https://microsoft.github.io/autogen/0.2/docs/ -output ./data/autogen_docs/
```

