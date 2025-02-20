from typing import Optional

from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


class WebExplorerAgent(MultimodalWebSurfer):
    """
    Specialized web exploration agent for comprehensive information gathering.

    Capabilities:
    - Find and analyze web resources
    - Extract and summarize key information
    - Provide context-rich web research
    """

    def __init__(
        self,
        name: str = "WebExplorer",
        model_client: Optional[AzureOpenAIChatCompletionClient] = None,
        start_page: str = "https://www.google.com",
        headless: bool = True,
        animate_actions: bool = False,
        to_save_screenshots: bool = True,
        use_ocr: bool = False,
        debug_dir: str = "./files/debug",
    ):
        """
        Initialize the WebExplorer agent with advanced web surfing capabilities.

        Args:
            name (str): Name of the agent
            model_client (AzureOpenAIChatCompletionClient): OpenAI model client
            start_page (str): Initial web page for navigation
            headless (bool): Run browser in headless mode
            animate_actions (bool): Animate browser actions
            to_save_screenshots (bool): Save screenshots during web exploration
            use_ocr (bool): Use Optical Character Recognition
            debug_dir (str): Directory for debugging artifacts
        """
        super().__init__(
            name=name,
            model_client=model_client,
            start_page=start_page,
            headless=headless,
            animate_actions=animate_actions,
            to_save_screenshots=to_save_screenshots,
            use_ocr=use_ocr,
            debug_dir=debug_dir,
        )

    def custom_web_research(self, query: str, num_results: int = 5) -> list:
        """
        Perform custom web research with advanced filtering.

        Args:
            query (str): Search query
            num_results (int): Number of results to return

        Returns:
            list: Curated web research results
        """
        # Implement custom web research logic
        results = self.search(query)
        return results[:num_results]
