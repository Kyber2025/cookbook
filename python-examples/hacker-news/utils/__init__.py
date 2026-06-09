"""Hacker News digest utilities.

Submodules are imported directly (e.g. `from utils.hn import scrape_front_page`,
`from utils.llm import enrich_stories`) so that import-free helpers like
`utils.extract` can be reused by the standalone runner without pulling in the
Intuned runtime.
"""
