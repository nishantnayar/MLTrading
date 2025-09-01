"""
Sequential Task Runner
Alternative to concurrent execution to prevent connection pool exhaustion
"""

import asyncio
import time
from typing import List, Callable, Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger("mltrading.sequential_runner")


class SequentialTaskRunner:
    """
    Sequential task runner that processes tasks one at a time to prevent
    database connection pool exhaustion.

    Alternative to ConcurrentTaskRunner for connection-intensive workflows.
    """

    def __init__(self, max_workers: int = 1, batch_size: int = 10):
        """
        Initialize sequential runner.

        Args:
            max_workers: Always 1 for true sequential processing
            batch_size: Number of tasks to process before connection cleanup
        """
        self.max_workers = 1  # Force sequential
        self.batch_size = batch_size
        self.completed_tasks = 0

    async def map(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        Process items sequentially to avoid connection conflicts.

        Args:
            func: Function to apply to each item
            items: List of items to process

        Returns:
            List of results in same order as input
        """
        results = []
        total_items = len(items)

        logger.info(f"Starting sequential processing of {total_items} items")

        for i, item in enumerate(items):
            try:
                start_time = time.time()

                # Process item
                result = await self._run_task(func, item)
                results.append(result)

                elapsed = time.time() - start_time
                self.completed_tasks += 1

                logger.info(f"Completed {i + 1}/{total_items} - {item} in {elapsed:.2f}s")

                # Periodic cleanup to prevent connection buildup
                if self.completed_tasks % self.batch_size == 0:
                    await self._cleanup_connections()

                # Small delay to prevent overwhelming the database
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Task failed for {item}: {e}")
                results.append(None)  # Maintain result order

        logger.info(
            f"Sequential processing completed: {len([r for r in results if r is not None])}/{total_items} successful")
        return results

    async def _run_task(self, func: Callable, item: Any) -> Any:
        """Run a single task"""
        if asyncio.iscoroutinefunction(func):
            return await func(item)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                return await loop.run_in_executor(executor, func, item)

    async def _cleanup_connections(self):
        """Periodic cleanup to prevent connection leaks"""
        logger.debug(f"Performing connection cleanup after {self.batch_size} tasks")
        # Small delay to allow connections to be returned to pool
        await asyncio.sleep(0.5)


class BatchSequentialRunner:
    """
    Processes tasks in small sequential batches for better throughput
    while still avoiding connection pool exhaustion.
    """

    def __init__(self, batch_size: int = 5, delay_between_batches: float = 1.0):
        """
        Initialize batch sequential runner.

        Args:
            batch_size: Size of each sequential batch
            delay_between_batches: Delay between batches (seconds)
        """
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches

    async def process_batches(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        Process items in sequential batches.

        Args:
            func: Function to apply to each item
            items: List of items to process

        Returns:
            List of results in same order as input
        """
        all_results = []
        total_items = len(items)

        # Split into batches
        batches = [items[i:i + self.batch_size] for i in range(0, total_items, self.batch_size)]

        logger.info(f"Processing {total_items} items in {len(batches)} sequential batches of {self.batch_size}")

        for batch_num, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_num + 1}/{len(batches)} ({len(batch)} items)")

            # Process this batch sequentially
            batch_results = []
            for item in batch:
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(item)
                    else:
                        loop = asyncio.get_event_loop()
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            result = await loop.run_in_executor(executor, func, item)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Task failed for {item}: {e}")
                    batch_results.append(None)

            all_results.extend(batch_results)

            # Delay between batches to allow connection cleanup
            if batch_num < len(batches) - 1:  # Don't delay after last batch
                logger.debug(f"Waiting {self.delay_between_batches}s before next batch")
                await asyncio.sleep(self.delay_between_batches)

        successful = len([r for r in all_results if r is not None])
        logger.info(f"Batch sequential processing completed: {successful}/{total_items} successful")

        return all_results


# Factory function to choose appropriate runner


def get_safe_task_runner(total_tasks: int, connection_sensitive: bool = True) -> Any:
    """
    Get appropriate task runner based on task characteristics.

    Args:
        total_tasks: Total number of tasks to process
        connection_sensitive: Whether tasks are database connection intensive

    Returns:
        Appropriate task runner instance
    """
    if connection_sensitive:
        if total_tasks <= 20:
            return SequentialTaskRunner(batch_size=10)
        else:
            return BatchSequentialRunner(batch_size=5, delay_between_batches=2.0)
    else:
        # For non-connection intensive tasks, can use higher concurrency
        from prefect.task_runners import ConcurrentTaskRunner
        return ConcurrentTaskRunner(max_workers=min(4, max(1, total_tasks // 10)))
