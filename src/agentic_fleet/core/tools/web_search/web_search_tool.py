"""
Web Search Tool Module.

This module provides tools for performing web searches and analyzing
search results to gather relevant information for decision making.
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SearchResult(BaseModel):
    """Represents a single search result."""

    url: str
    title: str
    snippet: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    relevance_score: float = 0.0
    metadata: dict[str, Any] = {}


class WebSearchTool:
    """
    Tool for performing web searches and analyzing search results
    to gather relevant information for decision making.
    """

    def __init__(
        self, max_results: int = 5, search_depth: int = 1, min_relevance_score: float = 0.7
    ) -> None:
        """
        Initialize the Web Search Tool.

        Args:
            max_results: Maximum number of search results to process
            search_depth: Depth of search (1 for direct results, 2 for following links)
            min_relevance_score: Minimum relevance score for including results
        """
        self.max_results = max_results
        self.search_depth = search_depth
        self.min_relevance_score = min_relevance_score
        self.search_history: list[dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)

    async def search(self, query: str) -> list[SearchResult]:
        """
        Perform a web search for the given query.

        Args:
            query: Search query string

        Returns:
            List of SearchResult objects
        """
        # Record search in history
        search_record = {"query": query, "timestamp": datetime.now(), "results": []}

        try:
            # Perform initial search
            results = await self._execute_search(query)

            # Score and filter results
            scored_results = await self._score_results(query, results)
            filtered_results = [
                r for r in scored_results if r.relevance_score >= self.min_relevance_score
            ][: self.max_results]

            # If search depth > 1, follow links and analyze content
            if self.search_depth > 1:
                detailed_results = await self._analyze_content(filtered_results)
            else:
                detailed_results = filtered_results

            # Update search history
            search_record["results"] = [result.model_dump() for result in detailed_results]
            self.search_history.append(search_record)

            return detailed_results

        except Exception as e:
            search_record["error"] = str(e)
            self.search_history.append(search_record)
            raise

    async def _execute_search(self, query: str) -> list[SearchResult]:
        """
        Execute the search using available search APIs.

        Args:
            query: Search query string

        Returns:
            List of initial SearchResult objects
        """
        results = []

        # Use multiple search APIs for comprehensive results
        async with httpx.AsyncClient() as client:
            # Example: Use a search API (implementation would use actual API)
            response = await client.get("https://api.search.example", params={"q": query})

            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    results.append(
                        SearchResult(
                            url=item["url"],
                            title=item["title"],
                            snippet=item["snippet"],
                            source="search_api",
                            metadata={"raw_item": item},
                        )
                    )

        return results

    async def _score_results(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """
        Score search results based on relevance to query.

        Args:
            query: Original search query
            results: List of search results to score

        Returns:
            List of scored SearchResult objects
        """
        if not results:
            return []

        # Prepare documents for TF-IDF
        documents = [query] + [f"{r.title} {r.snippet}" for r in results]

        # Calculate TF-IDF matrices
        tfidf_matrix = self.vectorizer.fit_transform(documents)

        # Calculate similarity between query and each result
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        # Assign scores to results
        for result, score in zip(results, similarities, strict=False):
            result.relevance_score = float(score)

        return sorted(results, key=lambda x: x.relevance_score, reverse=True)

    async def _analyze_content(self, results: list[SearchResult]) -> list[SearchResult]:
        """
        Analyze the content of search results in more detail.

        Args:
            results: List of search results to analyze

        Returns:
            List of SearchResult objects with detailed analysis
        """

        async def analyze_url(result: SearchResult) -> SearchResult:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(result.url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")

                        # Extract main content
                        main_content = soup.find("main") or soup.find("article")
                        if main_content:
                            # Update result with detailed content
                            result.metadata.update(
                                {
                                    "detailed_content": main_content.get_text(),
                                    "word_count": len(main_content.get_text().split()),
                                    "links": [
                                        a["href"]
                                        for a in main_content.find_all("a")
                                        if "href" in a.attrs
                                    ],
                                }
                            )
            except Exception as e:
                result.metadata["analysis_error"] = str(e)

            return result

        # Analyze all results concurrently
        tasks = [analyze_url(result) for result in results]
        detailed_results = await asyncio.gather(*tasks)

        return detailed_results

    def get_search_history(self) -> list[dict[str, Any]]:
        """
        Get the history of searches performed.

        Returns:
            List of search records
        """
        return self.search_history

    def clear_history(self) -> None:
        """Clear the search history."""
        self.search_history.clear()

    def get_recent_searches(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get the most recent searches.

        Args:
            limit: Maximum number of recent searches to return

        Returns:
            List of recent search records
        """
        return sorted(self.search_history, key=lambda x: x["timestamp"], reverse=True)[:limit]
