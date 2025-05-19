"""
Batch processing utilities for AgenticFleet.

This module provides tools for batching similar operations to improve performance.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BatchProcessor:
    """
    Batch similar operations for improved performance.

    This processor collects operations of the same type and processes
    them in a batch to reduce overhead.
    """

    def __init__(self, batch_size: int = 10, max_wait_time: float = 0.1):
        """
        Initialize batch processor.

        Args:
            batch_size: Maximum batch size
            max_wait_time: Maximum time to wait for batch to fill in seconds
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_items: Dict[str, List[Any]] = {}
        self.pending_futures: Dict[str, Dict[str, asyncio.Future]] = {}
        self.batch_processor_tasks: Dict[str, asyncio.Task] = {}

    async def add_item(self, batch_type: str, item: Any, processor_func: Callable[[List[Any]], Any]) -> Any:
        """
        Add item to a batch for processing.

        Args:
            batch_type: Type of batch this item belongs to
            item: The item to process
            processor_func: Function to process the batch

        Returns:
            Any: Result of processing this item
        """
        # Initialize batch type if not exists
        if batch_type not in self.pending_items:
            self.pending_items[batch_type] = []
            self.pending_futures[batch_type] = {}
            # Start batch processor task
            self.batch_processor_tasks[batch_type] = asyncio.create_task(
                self._process_batch(batch_type, processor_func)
            )

        # Create future for this item's result
        result_future = asyncio.Future()
        item_id = str(id(item))
        self.pending_futures[batch_type][item_id] = result_future

        # Add item to pending batch
        self.pending_items[batch_type].append((item_id, item))

        # Wait for result
        return await result_future

    async def _process_batch(self, batch_type: str, processor_func: Callable[[List[Any]], Any]) -> None:
        """
        Process a batch of items when ready.

        Args:
            batch_type: Type of batch to process
            processor_func: Function to process the batch
        """
        while True:
            # Wait for batch to fill or timeout
            if not self.pending_items[batch_type]:
                await asyncio.sleep(0.01)  # Tiny sleep to prevent CPU spinning
                continue

            # Wait for batch to reach size or timeout
            start_time = time.time()
            while (
                len(self.pending_items[batch_type]) < self.batch_size and time.time() - start_time < self.max_wait_time
            ):
                await asyncio.sleep(0.01)

                # If no pending items, reset timer
                if not self.pending_items[batch_type]:
                    start_time = time.time()

            # Process current batch
            current_batch = self.pending_items[batch_type].copy()
            self.pending_items[batch_type] = []

            if not current_batch:
                continue

            try:
                # Extract items for processing
                item_ids, items = zip(*current_batch)

                # Process batch
                results = await processor_func(items)

                # Set results to futures
                for item_id, result in zip(item_ids, results):
                    future = self.pending_futures[batch_type].pop(item_id, None)
                    if future and not future.done():
                        future.set_result(result)
            except Exception as e:
                # Handle processing error by failing all futures
                logger.error(f"Batch processing error for {batch_type}: {str(e)}", exc_info=True)
                for item_id, _ in current_batch:
                    future = self.pending_futures[batch_type].pop(item_id, None)
                    if future and not future.done():
                        future.set_exception(e)

    def stop(self) -> None:
        """Stop all batch processing tasks."""
        for batch_type, task in self.batch_processor_tasks.items():
            task.cancel()

            # Set exceptions for any remaining futures
            for future in self.pending_futures[batch_type].values():
                if not future.done():
                    future.set_exception(asyncio.CancelledError("Batch processor stopped"))

        # Clear all data
        self.pending_items.clear()
        self.pending_futures.clear()
        self.batch_processor_tasks.clear()


# Common batch processors


class MessageBatchProcessor:
    """
    Batch processor specifically for handling message processing.
    """

    def __init__(self, processor_func: Callable[[List[Any]], List[Any]], batch_size: int = 20):
        """
        Initialize message batch processor.

        Args:
            processor_func: Function to process batches of messages
            batch_size: Maximum batch size
        """
        self.batch_processor = BatchProcessor(batch_size=batch_size)
        self.processor_func = processor_func

    async def process_message(self, message: Any) -> Any:
        """
        Process a message, potentially as part of a batch.

        Args:
            message: The message to process

        Returns:
            Any: The processing result
        """
        # Determine batch type based on message type
        batch_type = type(message).__name__

        return await self.batch_processor.add_item(
            batch_type=batch_type, item=message, processor_func=self.processor_func
        )

    def stop(self) -> None:
        """Stop all batch processing."""
        self.batch_processor.stop()


# Global batch processor instance
_global_batch_processor = BatchProcessor()


def get_global_batch_processor() -> BatchProcessor:
    """
    Get the global batch processor instance.

    Returns:
        BatchProcessor: Global batch processor instance
    """
    return _global_batch_processor


async def batch_execute(
    items: List[Any], func: Callable[[Any], Any], batch_size: int = 10, concurrency_limit: Optional[int] = None
) -> List[Any]:
    """
    Execute a function on multiple items with batching and concurrency control.

    Args:
        items: List of items to process
        func: Function to execute on each item
        batch_size: Size of batches to process
        concurrency_limit: Maximum number of concurrent tasks

    Returns:
        List[Any]: Results for each item
    """
    if not items:
        return []

    # Default concurrency limit to 2x CPU count if not specified
    if concurrency_limit is None:
        concurrency_limit = min(20, len(items))

    # Create batches
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    # Process batches with concurrency limit
    semaphore = asyncio.Semaphore(concurrency_limit)

    async def process_batch(batch: List[Any]) -> List[Any]:
        async with semaphore:
            tasks = [asyncio.create_task(func(item)) for item in batch]
            return await asyncio.gather(*tasks, return_exceptions=True)

    # Process all batches
    batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])

    # Flatten results
    results = []
    for batch_result in batch_results:
        results.extend(batch_result)

    return results
