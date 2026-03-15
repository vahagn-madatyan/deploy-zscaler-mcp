"""CloudWatch Runtime Verifier for Zscaler MCP Deployer.

Provides runtime health verification via CloudWatch Logs analysis,
with lazy boto3 initialization, log group/stream discovery, and
pattern matching for health indicators.
"""

import logging
import re
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

from ..models import VerificationConfig, VerificationResult, VerificationStatus
from ..errors import CloudWatchError, VerificationError

logger = logging.getLogger(__name__)


class RuntimeVerifier:
    """Verifier for Bedrock AgentCore runtime health via CloudWatch Logs.
    
    Discovers log groups and streams, filters log events, and pattern-matches
    for health indicators like credential injection success and MCP server
    initialization. Uses exponential backoff polling for log availability.
    
    Log group naming convention: /aws/bedrock/{runtime_id}
    """
    
    # Default health patterns to match in logs
    DEFAULT_HEALTH_PATTERNS = [
        "credential",
        "retrieved",
        "MCP server",
        "started",
        "listening"
    ]
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None
    ):
        """Initialize RuntimeVerifier.
        
        Args:
            region: AWS region (optional)
            profile_name: AWS profile name (optional)
            session: Pre-configured boto3 session (optional)
        """
        self._region = region
        self._profile_name = profile_name
        self._session = session
        self._client = None
    
    @property
    def session(self) -> boto3.Session:
        """Lazy initialization of boto3 session."""
        if self._session is None:
            if self._profile_name:
                self._session = boto3.Session(
                    profile_name=self._profile_name,
                    region_name=self._region
                )
            else:
                self._session = boto3.Session(region_name=self._region)
        return self._session
    
    @property
    def _logs_client(self):
        """Lazy initialization of CloudWatch Logs client."""
        if self._client is None:
            self._client = self.session.client("logs")
        return self._client
    
    def _get_log_group_name(self, runtime_id: str, prefix: str = "/aws/bedrock/") -> str:
        """Construct log group name for a runtime.
        
        Args:
            runtime_id: Runtime identifier
            prefix: Log group prefix (default: /aws/bedrock/)
            
        Returns:
            Full log group name
        """
        return f"{prefix}{runtime_id}"
    
    def discover_log_group(
        self,
        runtime_id: str,
        prefix: str = "/aws/bedrock/"
    ) -> Optional[str]:
        """Discover log group for a runtime.
        
        Uses describe_log_groups with prefix filter to find the log group.
        
        Args:
            runtime_id: Runtime identifier
            prefix: Log group prefix to filter by
            
        Returns:
            Log group name if found, None otherwise
            
        Raises:
            CloudWatchError: If CloudWatch API call fails
        """
        log_group_name = self._get_log_group_name(runtime_id, prefix)
        
        logger.info(f"Discovering log group: {log_group_name}")
        
        try:
            # Use describe_log_groups with prefix filter
            response = self._logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_name,
                limit=10
            )
            
            log_groups = response.get("logGroups", [])
            
            # Find exact match
            for group in log_groups:
                if group.get("logGroupName") == log_group_name:
                    logger.info(f"Found log group: {log_group_name}")
                    return log_group_name
            
            # Check for paginated results
            next_token = response.get("nextToken")
            while next_token:
                response = self._logs_client.describe_log_groups(
                    logGroupNamePrefix=log_group_name,
                    limit=10,
                    nextToken=next_token
                )
                
                for group in response.get("logGroups", []):
                    if group.get("logGroupName") == log_group_name:
                        logger.info(f"Found log group: {log_group_name}")
                        return log_group_name
                
                next_token = response.get("nextToken")
            
            logger.warning(f"Log group not found: {log_group_name}")
            return None
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to describe log groups: {error_code} - {error_message}")
            
            raise CloudWatchError(
                message=f"Failed to discover log group for runtime '{runtime_id}': {error_message}",
                error_code=f"S04-001-{error_code}",
                phase="log_group_discovery",
                context={
                    "runtime_id": runtime_id,
                    "log_group_name": log_group_name,
                    "aws_error_code": error_code,
                }
            )
    
    def discover_log_streams(
        self,
        log_group_name: str,
        limit: int = 10
    ) -> List[str]:
        """Discover log streams in a log group.
        
        Uses describe_log_streams to get recent log stream names.
        
        Args:
            log_group_name: Name of the log group
            limit: Maximum number of streams to return
            
        Returns:
            List of log stream names
            
        Raises:
            CloudWatchError: If CloudWatch API call fails
        """
        logger.info(f"Discovering log streams in: {log_group_name}")
        
        try:
            response = self._logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=limit
            )
            
            streams = [
                stream.get("logStreamName", "")
                for stream in response.get("logStreams", [])
            ]
            
            logger.info(f"Found {len(streams)} log streams")
            return streams
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to describe log streams: {error_code} - {error_message}")
            
            raise CloudWatchError(
                message=f"Failed to discover log streams in '{log_group_name}': {error_message}",
                error_code=f"S04-001-{error_code}",
                phase="stream_discovery",
                context={
                    "log_group_name": log_group_name,
                    "aws_error_code": error_code,
                }
            )
    
    def filter_log_events(
        self,
        log_group_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter log events from a log group.
        
        Uses filter_log_events to fetch recent log entries with optional
        pattern matching.
        
        Args:
            log_group_name: Name of the log group
            start_time: Start time for events (default: 1 hour ago)
            end_time: End time for events (default: now)
            limit: Maximum number of events to return
            pattern: CloudWatch filter pattern (optional)
            
        Returns:
            List of log event dictionaries
            
        Raises:
            CloudWatchError: If CloudWatch API call fails
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        if start_time is None:
            start_time = end_time - timedelta(hours=1)
        
        # Convert to milliseconds since epoch
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        logger.info(f"Filtering log events from {log_group_name} ({start_time} to {end_time})")
        
        try:
            filter_args = {
                "logGroupName": log_group_name,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": limit
            }
            
            if pattern:
                filter_args["filterPattern"] = pattern
            
            response = self._logs_client.filter_log_events(**filter_args)
            
            events = response.get("events", [])
            
            logger.info(f"Retrieved {len(events)} log events")
            return events
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to filter log events: {error_code} - {error_message}")
            
            raise CloudWatchError(
                message=f"Failed to filter log events in '{log_group_name}': {error_message}",
                error_code=f"S04-001-{error_code}",
                phase="event_fetching",
                context={
                    "log_group_name": log_group_name,
                    "aws_error_code": error_code,
                }
            )
    
    def match_patterns(
        self,
        events: List[Dict[str, Any]],
        patterns: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match health patterns against log events.
        
        Performs case-insensitive partial matching of patterns against
        log message content.
        
        Args:
            events: List of log event dictionaries
            patterns: List of patterns to match
            
        Returns:
            Dictionary mapping pattern to list of matching events
        """
        matches: Dict[str, List[Dict[str, Any]]] = {}
        
        for event in events:
            message = event.get("message", "")
            
            for pattern in patterns:
                # Case-insensitive partial match
                if pattern.lower() in message.lower():
                    if pattern not in matches:
                        matches[pattern] = []
                    matches[pattern].append(event)
        
        return matches
    
    def _poll_for_streams(
        self,
        log_group_name: str,
        timeout_seconds: int = 120,
        initial_interval: float = 2.0,
        max_interval: float = 10.0,
        backoff_factor: float = 2.0
    ) -> List[str]:
        """Poll for log streams with exponential backoff.
        
        AWS CloudWatch Logs can take time to create log streams after
        runtime startup. This method polls until streams are available
        or timeout is reached.
        
        Args:
            log_group_name: Name of the log group
            timeout_seconds: Maximum time to wait
            initial_interval: Initial polling interval
            max_interval: Maximum polling interval
            backoff_factor: Factor to increase interval each poll
            
        Returns:
            List of log stream names
            
        Raises:
            VerificationError: If timeout occurs before streams appear
        """
        logger.info(f"Polling for log streams in {log_group_name}")
        logger.info(f"Timeout: {timeout_seconds}s, initial interval: {initial_interval}s")
        
        start_time = time.time()
        interval = initial_interval
        poll_count = 0
        
        while True:
            poll_count += 1
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed >= timeout_seconds:
                logger.error(f"Stream polling timeout after {elapsed:.1f}s ({poll_count} polls)")
                raise VerificationError(
                    message=f"Timeout waiting for log streams in '{log_group_name}'",
                    error_code="S04-002-001",
                    phase="stream_discovery",
                    context={
                        "log_group_name": log_group_name,
                        "timeout_seconds": timeout_seconds,
                        "poll_count": poll_count,
                        "elapsed_seconds": elapsed,
                    }
                )
            
            try:
                streams = self.discover_log_streams(log_group_name)
                
                if streams:
                    logger.info(f"Found {len(streams)} streams after {elapsed:.1f}s")
                    return streams
                
                logger.debug(f"Poll {poll_count}: No streams yet (elapsed: {elapsed:.1f}s)")
                
            except CloudWatchError:
                # Re-raise with verification context
                raise
            
            # Wait before next poll with exponential backoff
            sleep_time = min(interval, max_interval)
            time.sleep(sleep_time)
            interval = min(interval * backoff_factor, max_interval)
    
    def verify_runtime(
        self,
        runtime_id: str,
        timeout_seconds: int = 120
    ) -> VerificationResult:
        """Verify runtime health via CloudWatch Logs analysis.
        
        This is the main verification method that orchestrates log group
        discovery, stream polling, event filtering, and pattern matching
        to determine runtime health.
        
        Args:
            runtime_id: Runtime identifier to verify
            timeout_seconds: Maximum time to wait for log availability
            
        Returns:
            VerificationResult with status and evidence
        """
        start_time = time.time()
        
        logger.info(f"Starting runtime verification for: {runtime_id}")
        
        try:
            # Step 1: Discover log group
            log_group_name = self.discover_log_group(runtime_id)
            
            if not log_group_name:
                duration_ms = int((time.time() - start_time) * 1000)
                return VerificationResult(
                    status=VerificationStatus.ERROR,
                    runtime_id=runtime_id,
                    error_reason=f"Log group not found for runtime '{runtime_id}'",
                    error_code="S04-001-001",
                    phase="log_group_discovery",
                    verification_duration_ms=duration_ms
                )
            
            # Step 2: Poll for log streams
            try:
                streams = self._poll_for_streams(
                    log_group_name,
                    timeout_seconds=timeout_seconds
                )
            except VerificationError as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return VerificationResult(
                    status=VerificationStatus.ERROR,
                    runtime_id=runtime_id,
                    error_reason=e.message,
                    error_code=e.error_code or "S04-002-001",
                    phase="stream_discovery",
                    verification_duration_ms=duration_ms
                )
            
            if not streams:
                duration_ms = int((time.time() - start_time) * 1000)
                return VerificationResult(
                    status=VerificationStatus.PENDING,
                    runtime_id=runtime_id,
                    error_reason="No log streams available yet",
                    phase="stream_discovery",
                    verification_duration_ms=duration_ms
                )
            
            # Step 3: Fetch log events
            events = self.filter_log_events(log_group_name)
            
            if not events:
                duration_ms = int((time.time() - start_time) * 1000)
                return VerificationResult(
                    status=VerificationStatus.PENDING,
                    runtime_id=runtime_id,
                    phase="event_fetching",
                    verification_duration_ms=duration_ms
                )
            
            # Step 4: Match health patterns
            pattern_matches = self.match_patterns(events, self.DEFAULT_HEALTH_PATTERNS)
            
            matched_patterns = list(pattern_matches.keys())
            
            # Build log evidence (stream name -> matched message indicators)
            log_evidence: Dict[str, List[str]] = {}
            for pattern, matching_events in pattern_matches.items():
                for event in matching_events:
                    stream_name = event.get("logStreamName", "unknown")
                    if stream_name not in log_evidence:
                        log_evidence[stream_name] = []
                    # Store pattern match indicator, not full message
                    log_evidence[stream_name].append(f"matched_pattern:{pattern}")
            
            # Determine status based on pattern matches
            duration_ms = int((time.time() - start_time) * 1000)
            
            if len(matched_patterns) >= 3:
                # Healthy: multiple health indicators found
                status = VerificationStatus.HEALTHY
            elif len(matched_patterns) >= 1:
                # Partial: some indicators found but not enough for full health
                status = VerificationStatus.UNHEALTHY
                error_reason = f"Partial health indicators found: {matched_patterns}"
            else:
                # No health indicators found
                status = VerificationStatus.UNHEALTHY
                error_reason = "No health indicators found in logs"
            
            return VerificationResult(
                status=status,
                runtime_id=runtime_id,
                matched_patterns=matched_patterns,
                error_reason=error_reason if status == VerificationStatus.UNHEALTHY else None,
                log_evidence=log_evidence,
                verification_duration_ms=duration_ms,
                phase="pattern_matching"
            )
            
        except CloudWatchError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return VerificationResult(
                status=VerificationStatus.ERROR,
                runtime_id=runtime_id,
                error_reason=e.message,
                error_code=e.error_code,
                phase=e.phase,
                verification_duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"Unexpected error during verification of {runtime_id}")
            return VerificationResult(
                status=VerificationStatus.ERROR,
                runtime_id=runtime_id,
                error_reason=f"Unexpected error: {str(e)}",
                error_code="S04-002-004",
                phase="verification",
                verification_duration_ms=duration_ms
            )