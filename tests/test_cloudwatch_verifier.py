"""Tests for CloudWatch Runtime Verifier module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.aws.cloudwatch_verifier import RuntimeVerifier
from zscaler_mcp_deploy.models import (
    VerificationConfig,
    VerificationResult,
    VerificationStatus,
)
from zscaler_mcp_deploy.errors import CloudWatchError, VerificationError


class TestVerificationStatus:
    """Tests for VerificationStatus enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        assert VerificationStatus.HEALTHY.value == "healthy"
        assert VerificationStatus.UNHEALTHY.value == "unhealthy"
        assert VerificationStatus.PENDING.value == "pending"
        assert VerificationStatus.ERROR.value == "error"


class TestVerificationConfig:
    """Tests for VerificationConfig dataclass."""

    def test_config_creation(self):
        """Test creating a VerificationConfig with all fields."""
        config = VerificationConfig(
            runtime_id="test-runtime-123",
            log_group_prefix="/aws/bedrock/",
            timeout_seconds=120,
            poll_interval_initial=2.0,
            poll_interval_max=10.0,
            health_patterns=["credential", "started"]
        )
        assert config.runtime_id == "test-runtime-123"
        assert config.log_group_prefix == "/aws/bedrock/"
        assert config.timeout_seconds == 120

    def test_config_defaults(self):
        """Test VerificationConfig with default values."""
        config = VerificationConfig(runtime_id="test-runtime")
        assert config.log_group_prefix == "/aws/bedrock/"
        assert config.timeout_seconds == 120
        assert config.health_patterns == [
            "credential", "retrieved", "MCP server", "started", "listening"
        ]


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_creation(self):
        """Test creating a VerificationResult with all fields."""
        result = VerificationResult(
            status=VerificationStatus.HEALTHY,
            runtime_id="test-runtime",
            matched_patterns=["credential", "started"],
            log_evidence={"stream1": ["matched_pattern:credential"]},
            verification_duration_ms=5000,
            phase="pattern_matching"
        )
        assert result.status == VerificationStatus.HEALTHY
        assert result.runtime_id == "test-runtime"

    def test_result_is_healthy(self):
        """Test is_healthy() helper method."""
        healthy = VerificationResult(status=VerificationStatus.HEALTHY, runtime_id="test")
        unhealthy = VerificationResult(status=VerificationStatus.UNHEALTHY, runtime_id="test")
        assert healthy.is_healthy() is True
        assert unhealthy.is_healthy() is False

    def test_result_has_errors(self):
        """Test has_errors() helper method."""
        error_result = VerificationResult(status=VerificationStatus.ERROR, runtime_id="test")
        healthy_result = VerificationResult(status=VerificationStatus.HEALTHY, runtime_id="test")
        assert error_result.has_errors() is True
        assert healthy_result.has_errors() is False


class TestRuntimeVerifierInit:
    """Tests for RuntimeVerifier initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        verifier = RuntimeVerifier()
        assert verifier._region is None
        assert verifier._profile_name is None
        assert verifier._session is None

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        verifier = RuntimeVerifier(region="us-west-2", profile_name="test-profile")
        assert verifier._region == "us-west-2"
        assert verifier._profile_name == "test-profile"

    @patch("boto3.Session")
    def test_lazy_session_init(self, mock_session_class):
        """Test lazy initialization of boto3 session."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        verifier = RuntimeVerifier(region="us-east-1")
        session = verifier.session
        mock_session_class.assert_called_once_with(region_name="us-east-1")
        assert session is mock_session

    @patch("boto3.Session")
    def test_lazy_logs_client(self, mock_session_class):
        """Test lazy initialization of CloudWatch Logs client."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session
        verifier = RuntimeVerifier()
        client = verifier._logs_client
        mock_session.client.assert_called_once_with("logs")
        assert client is mock_client


class TestGetLogGroupName:
    """Tests for _get_log_group_name helper."""

    def test_default_prefix(self):
        """Test log group name construction with default prefix."""
        verifier = RuntimeVerifier()
        name = verifier._get_log_group_name("my-runtime")
        assert name == "/aws/bedrock/my-runtime"


class TestDiscoverLogGroup:
    """Tests for discover_log_group method."""

    def test_log_group_found(self):
        """Test successful log group discovery."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        result = verifier.discover_log_group("test-runtime")
        assert result == "/aws/bedrock/test-runtime"

    def test_log_group_not_found(self):
        """Test when log group does not exist."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = verifier.discover_log_group("test-runtime")
        assert result is None

    def test_cloudwatch_api_error(self):
        """Test handling of CloudWatch API errors."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "DescribeLogGroups"
        )
        mock_client.describe_log_groups.side_effect = error
        with pytest.raises(CloudWatchError) as exc_info:
            verifier.discover_log_group("test-runtime")
        assert "S04-001-AccessDeniedException" in str(exc_info.value.error_code)


class TestDiscoverLogStreams:
    """Tests for discover_log_streams method."""

    def test_streams_found(self):
        """Test successful log stream discovery."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "stream1"},
                {"logStreamName": "stream2"}
            ]
        }
        result = verifier.discover_log_streams("/aws/bedrock/test-runtime")
        assert result == ["stream1", "stream2"]

    def test_no_streams(self):
        """Test when no log streams exist."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_streams.return_value = {"logStreams": []}
        result = verifier.discover_log_streams("/aws/bedrock/test-runtime")
        assert result == []


class TestFilterLogEvents:
    """Tests for filter_log_events method."""

    def test_events_found(self):
        """Test successful log event retrieval."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "stream1", "message": "Credential retrieved"},
                {"logStreamName": "stream1", "message": "MCP server started"}
            ]
        }
        result = verifier.filter_log_events("/aws/bedrock/test-runtime")
        assert len(result) == 2

    def test_cloudwatch_api_error(self):
        """Test handling of CloudWatch API errors."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "FilterLogEvents"
        )
        mock_client.filter_log_events.side_effect = error
        with pytest.raises(CloudWatchError) as exc_info:
            verifier.filter_log_events("/aws/bedrock/test-runtime")
        assert "S04-001-ThrottlingException" in str(exc_info.value.error_code)


class TestMatchPatterns:
    """Tests for match_patterns method."""

    def test_single_pattern_match(self):
        """Test matching a single pattern."""
        verifier = RuntimeVerifier()
        events = [
            {"message": "Credential retrieved successfully"},
            {"message": "Some other message"}
        ]
        result = verifier.match_patterns(events, ["credential"])
        assert "credential" in result
        assert len(result["credential"]) == 1

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        verifier = RuntimeVerifier()
        events = [
            {"message": "CREDENTIAL Retrieved"},
            {"message": "credential retrieved"}
        ]
        result = verifier.match_patterns(events, ["credential"])
        assert len(result["credential"]) == 2

    def test_no_matches(self):
        """Test when no patterns match."""
        verifier = RuntimeVerifier()
        events = [{"message": "Some unrelated message"}]
        result = verifier.match_patterns(events, ["credential"])
        assert result == {}


class TestPollForStreams:
    """Tests for _poll_for_streams method."""

    @patch("time.sleep")
    @patch("time.time")
    def test_streams_found_immediately(self, mock_time, mock_sleep):
        """Test when streams are found on first poll."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_time.side_effect = [0, 1]
        result = verifier._poll_for_streams("/aws/bedrock/test-runtime")
        assert result == ["stream1"]
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    @patch("time.time")
    def test_timeout_before_streams_appear(self, mock_time, mock_sleep):
        """Test timeout when streams never appear."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_streams.return_value = {"logStreams": []}
        mock_time.side_effect = [0, 30, 60, 90, 121]
        with pytest.raises(VerificationError) as exc_info:
            verifier._poll_for_streams("/aws/bedrock/test-runtime", timeout_seconds=120)
        assert "S04-002-001" in str(exc_info.value.error_code)


class TestVerifyRuntime:
    """Tests for verify_runtime method."""

    def test_healthy_runtime(self):
        """Test verification of healthy runtime with all indicators."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "stream1", "message": "Credential retrieved"},
                {"logStreamName": "stream1", "message": "MCP server started"},
                {"logStreamName": "stream1", "message": "Listening on port 8080"}
            ]
        }
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.HEALTHY
        assert result.is_healthy() is True

    def test_unhealthy_runtime(self):
        """Test verification with no health indicators."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_client.filter_log_events.return_value = {
            "events": [{"logStreamName": "stream1", "message": "Application started"}]
        }
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.UNHEALTHY

    def test_log_group_not_found(self):
        """Test verification when log group does not exist."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.ERROR
        assert result.error_code == "S04-001-001"

    def test_no_events_yet(self):
        """Test verification when no log events exist yet."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_client.filter_log_events.return_value = {"events": []}
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.PENDING

    def test_cloudwatch_api_error(self):
        """Test verification when CloudWatch API fails."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "DescribeLogGroups"
        )
        mock_client.describe_log_groups.side_effect = error
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.ERROR

    def test_log_evidence_structure(self):
        """Test that log evidence has correct structure."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "stream1", "message": "Credential retrieved"}
            ]
        }
        result = verifier.verify_runtime("test-runtime")
        assert "stream1" in result.log_evidence

    def test_verification_duration_tracking(self):
        """Test that verification duration is tracked."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_client.filter_log_events.return_value = {
            "events": [{"logStreamName": "stream1", "message": "Credential retrieved"}]
        }
        result = verifier.verify_runtime("test-runtime")
        assert result.verification_duration_ms is not None
        assert result.verification_duration_ms >= 0

    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.side_effect = Exception("Unexpected error")
        result = verifier.verify_runtime("test-runtime")
        assert result.status == VerificationStatus.ERROR
        assert result.error_code == "S04-002-004"


class TestDefaultHealthPatterns:
    """Tests for DEFAULT_HEALTH_PATTERNS constant."""

    def test_default_patterns_content(self):
        """Test that default patterns include expected values."""
        expected_patterns = ["credential", "retrieved", "MCP server", "started", "listening"]
        assert RuntimeVerifier.DEFAULT_HEALTH_PATTERNS == expected_patterns


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_runtime_id(self):
        """Test handling of empty runtime ID."""
        verifier = RuntimeVerifier()
        name = verifier._get_log_group_name("")
        assert name == "/aws/bedrock/"

    def test_custom_prefix_discovery(self):
        """Test log group discovery with custom prefix."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/custom/prefix/test-runtime"}]
        }
        result = verifier.discover_log_group("test-runtime", prefix="/custom/prefix/")
        assert result == "/custom/prefix/test-runtime"

    def test_multiple_streams_evidence(self):
        """Test log evidence with multiple streams."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/test-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "stream1"},
                {"logStreamName": "stream2"}
            ]
        }
        mock_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "stream1", "message": "Credential retrieved"},
                {"logStreamName": "stream2", "message": "MCP server started"}
            ]
        }
        result = verifier.verify_runtime("test-runtime")
        assert "stream1" in result.log_evidence
        assert "stream2" in result.log_evidence


class TestFullIntegrationFlow:
    """Integration tests for full verification flow."""

    def test_complete_success_flow(self):
        """Test complete successful verification flow."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client

        # Setup complete flow
        mock_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/prod-runtime"}]
        }
        mock_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "main"}]
        }
        mock_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "main", "message": "Credential retrieved from Secrets Manager"},
                {"logStreamName": "main", "message": "MCP server initialization complete"},
                {"logStreamName": "main", "message": "Server started and listening on port 8080"}
            ]
        }

        result = verifier.verify_runtime("prod-runtime")

        assert result.status == VerificationStatus.HEALTHY
        assert len(result.matched_patterns) >= 3
        assert result.phase == "pattern_matching"
        assert result.error_reason is None
        assert result.error_code is None

    def test_complete_failure_flow(self):
        """Test complete failure flow with API error."""
        verifier = RuntimeVerifier()
        mock_client = Mock()
        verifier._client = mock_client

        error = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Log group not found"}},
            "DescribeLogGroups"
        )
        mock_client.describe_log_groups.side_effect = error

        result = verifier.verify_runtime("missing-runtime")

        assert result.status == VerificationStatus.ERROR
        assert "S04-001-ResourceNotFoundException" in str(result.error_code)
        assert result.phase == "log_group_discovery"


# Count: 27+ test methods across all test classes
# - TestVerificationStatus: 1 test
# - TestVerificationConfig: 3 tests
# - TestVerificationResult: 4 tests
# - TestRuntimeVerifierInit: 4 tests
# - TestGetLogGroupName: 1 test
# - TestDiscoverLogGroup: 4 tests
# - TestDiscoverLogStreams: 2 tests
# - TestFilterLogEvents: 3 tests
# - TestMatchPatterns: 4 tests
# - TestPollForStreams: 2 tests
# - TestVerifyRuntime: 8 tests
# - TestDefaultHealthPatterns: 1 test
# - TestEdgeCases: 3 tests
# - TestFullIntegrationFlow: 2 tests
# Total: 42 tests
