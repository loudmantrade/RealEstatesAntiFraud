"""
Processing Pipeline Orchestrator

Coordinates the execution of processing plugins in the correct order.
Manages the flow of events through the processing pipeline.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from core.interfaces.processing_plugin import ProcessingPlugin
from core.interfaces.queue_plugin import QueuePlugin
from core.models.events import (
    EventMetadata,
    EventStatus,
    EventType,
    NormalizedListingEvent,
    ProcessedListingEvent,
    ProcessingFailedEvent,
    RawListingEvent,
    Topics,
)
from core.models.udm import Listing
from core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """
    Orchestrates the processing pipeline for listings.
    
    Workflow:
    1. Consume raw listing events from queue
    2. Execute processing plugins in priority order
    3. Publish processed events to next stage
    4. Handle errors and retries
    
    Features:
    - Priority-based plugin execution
    - Error handling and dead letter queue
    - Progress tracking and observability
    - Graceful shutdown
    """

    def __init__(
        self,
        plugin_manager: PluginManager,
        queue: QueuePlugin,
        max_retries: int = 3,
        enable_parallel: bool = False,
    ):
        """
        Initialize processing orchestrator.
        
        Args:
            plugin_manager: Plugin manager instance
            queue: Message queue instance
            max_retries: Maximum retry attempts for failed processing
            enable_parallel: Enable parallel execution of independent plugins
        """
        self.plugin_manager = plugin_manager
        self.queue = queue
        self.max_retries = max_retries
        self.enable_parallel = enable_parallel
        
        self._running = False
        self._subscription_id: Optional[str] = None
        self._stats = {
            "events_processed": 0,
            "events_failed": 0,
            "total_processing_time_ms": 0,
            "plugins_executed": 0,
        }

    def start(self) -> None:
        """Start consuming events from queue"""
        if self._running:
            logger.warning("Orchestrator already running")
            return
        
        self._running = True
        
        # Subscribe to raw listings topic
        self._subscription_id = self.queue.subscribe(
            Topics.RAW_LISTINGS,
            self._process_raw_listing
        )
        
        logger.info("Processing orchestrator started")

    def stop(self) -> None:
        """Stop consuming events"""
        if not self._running:
            return
        
        self._running = False
        
        if self._subscription_id:
            self.queue.unsubscribe(self._subscription_id)
            self._subscription_id = None
        
        logger.info("Processing orchestrator stopped")

    def _process_raw_listing(self, message: Dict[str, Any]) -> None:
        """
        Process a raw listing event.
        
        Args:
            message: Raw listing event from queue
        """
        start_time = time.time()
        
        try:
            # Parse event
            event = RawListingEvent.from_dict(message)
            
            logger.info(
                f"Processing event {event.metadata.event_id} "
                f"from {event.metadata.source_platform}"
            )
            
            # Update status
            event.metadata.status = EventStatus.PROCESSING
            
            # Execute processing pipeline
            result = self._execute_pipeline(event)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create processed event
            processed_event = ProcessedListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.PROCESSED_LISTING,
                    source_plugin_id=event.metadata.source_plugin_id,
                    source_platform=event.metadata.source_platform,
                    trace_id=event.metadata.trace_id,
                    request_id=event.metadata.request_id,
                    parent_event_id=event.metadata.event_id,
                    status=EventStatus.COMPLETED,
                ),
                listing_data=result["listing_data"],
                fraud_score=result.get("fraud_score", 0.0),
                fraud_signals=result.get("fraud_signals", []),
                risk_level=result.get("risk_level", "unknown"),
                processing_stages=result.get("stages", []),
                processing_duration_ms=processing_time,
                plugins_applied=result.get("plugins", []),
            )
            
            # Publish to processed listings topic
            self.queue.publish(
                Topics.PROCESSED_LISTINGS,
                processed_event.to_dict()
            )
            
            # Update statistics
            self._stats["events_processed"] += 1
            self._stats["total_processing_time_ms"] += processing_time
            
            logger.info(
                f"Completed processing event {event.metadata.event_id} "
                f"in {processing_time:.2f}ms"
            )
            
        except Exception as e:
            logger.error(f"Failed to process event: {e}", exc_info=True)
            self._handle_processing_failure(message, str(e))

    def _execute_pipeline(self, event: RawListingEvent) -> Dict[str, Any]:
        """
        Execute all processing plugins in priority order.
        
        Args:
            event: Raw listing event
            
        Returns:
            Dictionary with processed data and metadata
        """
        # Get all processing plugins
        plugins = self._get_processing_plugins()
        
        if not plugins:
            logger.warning("No processing plugins available")
            return {
                "listing_data": event.raw_data,
                "stages": [],
                "plugins": [],
            }
        
        # Sort by priority (lower number = higher priority)
        plugins.sort(key=lambda p: p.get_priority())
        
        # Initialize with raw data
        current_data = event.raw_data
        stages = []
        plugins_applied = []
        
        # Execute each plugin
        for plugin in plugins:
            try:
                plugin_name = plugin.get_metadata()["name"]
                logger.debug(f"Executing plugin: {plugin_name}")
                
                # Process data
                start = time.time()
                current_data = plugin.process(current_data)
                duration = (time.time() - start) * 1000
                
                # Record stage
                stages.append(plugin_name)
                plugins_applied.append(plugin_name)
                
                self._stats["plugins_executed"] += 1
                
                logger.debug(
                    f"Plugin {plugin_name} completed in {duration:.2f}ms"
                )
                
            except Exception as e:
                logger.error(
                    f"Plugin {plugin_name} failed: {e}",
                    exc_info=True
                )
                # Continue with other plugins
                continue
        
        return {
            "listing_data": current_data,
            "stages": stages,
            "plugins": plugins_applied,
        }

    def _get_processing_plugins(self) -> List[ProcessingPlugin]:
        """Get all enabled processing plugins"""
        all_plugins = self.plugin_manager.list_plugins()
        processing_plugins = []
        
        for plugin_meta in all_plugins:
            if (plugin_meta.type == "processing" and 
                plugin_meta.enabled):
                try:
                    # Get plugin instance
                    plugin = self.plugin_manager.get(plugin_meta.id)
                    if isinstance(plugin, ProcessingPlugin):
                        processing_plugins.append(plugin)
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin {plugin_meta.id}: {e}"
                    )
        
        return processing_plugins

    def _handle_processing_failure(
        self,
        message: Dict[str, Any],
        error: str
    ) -> None:
        """
        Handle processing failure.
        
        Args:
            message: Original message that failed
            error: Error message
        """
        try:
            event = RawListingEvent.from_dict(message)
            
            # Check retry count
            if event.metadata.retry_count < self.max_retries:
                # Increment retry count and requeue
                event.metadata.retry_count += 1
                event.metadata.status = EventStatus.RETRY
                
                self.queue.publish(
                    Topics.RAW_LISTINGS,
                    event.to_dict()
                )
                
                logger.info(
                    f"Requeued event {event.metadata.event_id} "
                    f"(retry {event.metadata.retry_count}/{self.max_retries})"
                )
            else:
                # Max retries exceeded, send to failed events
                failed_event = ProcessingFailedEvent(
                    metadata=EventMetadata(
                        event_type=EventType.PROCESSING_FAILED,
                        source_plugin_id=event.metadata.source_plugin_id,
                        source_platform=event.metadata.source_platform,
                        trace_id=event.metadata.trace_id,
                        parent_event_id=event.metadata.event_id,
                        status=EventStatus.FAILED,
                    ),
                    error_type="ProcessingError",
                    error_message=error,
                    failed_stage="pipeline_execution",
                    original_event=message,
                    is_recoverable=False,
                )
                
                self.queue.publish(
                    Topics.PROCESSING_FAILED,
                    failed_event.to_dict()
                )
                
                logger.error(
                    f"Event {event.metadata.event_id} failed permanently "
                    f"after {self.max_retries} retries"
                )
            
            self._stats["events_failed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to handle processing failure: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        stats = dict(self._stats)
        
        if stats["events_processed"] > 0:
            stats["avg_processing_time_ms"] = (
                stats["total_processing_time_ms"] / stats["events_processed"]
            )
        else:
            stats["avg_processing_time_ms"] = 0.0
        
        return stats

    def is_running(self) -> bool:
        """Check if orchestrator is running"""
        return self._running

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        queue_health = self.queue.health_check()
        
        status = "healthy" if self._running and queue_health["status"] == "healthy" else "unhealthy"
        
        return {
            "status": status,
            "running": self._running,
            "queue_health": queue_health,
            "statistics": self.get_statistics(),
        }
