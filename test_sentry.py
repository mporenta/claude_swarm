#!/usr/bin/env python3
"""
Test script to verify Sentry SDK integration.
Sends various types of events to Sentry for testing.

IMPORTANT: Get your DSN from Sentry web interface:
1. Go to http://localhost
2. Login with mike.porenta@goaptive.com / admin
3. Click on "Projects" in the left sidebar
4. Click on "internal" project (or create a new one)
5. Go to Settings > Client Keys (DSN)
6. Copy the DSN and set it as SENTRY_DSN environment variable

Or run this script with DSN as argument:
    python test_sentry.py "http://YOUR_KEY@localhost:9000/1"
"""

import os
import sys
import time
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

local_dsn = "http://80183f105e4f5cd83800b501a978f9b5@localhost:9000/1"
# Get DSN from command line argument, environment variable, or use placeholder
if len(sys.argv) > 1:
    SENTRY_DSN = sys.argv[1]
elif os.getenv("SENTRY_DSN"):
    SENTRY_DSN = os.getenv("SENTRY_DSN")
elif local_dsn:
    SENTRY_DSN = local_dsn
else:
    print("=" * 60)
    print("❌ ERROR: SENTRY_DSN not provided")
    print("=" * 60)
    print("\nPlease provide DSN in one of these ways:")
    print("\n1. As command line argument:")
    print("   python test_sentry.py 'http://YOUR_KEY@localhost:9000/1'")
    print("\n2. As environment variable:")
    print("   export SENTRY_DSN='http://YOUR_KEY@localhost:9000/1'")
    print("   python test_sentry.py")
    print("\n3. In .env file:")
    print("   SENTRY_DSN=http://YOUR_KEY@localhost:9000/1")
    print("\nTo get your DSN:")
    print("  1. Go to http://localhost")
    print("  2. Login: mike.porenta@goaptive.com / admin")
    print("  3. Click 'Projects' → 'internal'")
    print("  4. Settings → Client Keys (DSN)")
    print("=" * 60)
    sys.exit(1)

print(f"Initializing Sentry with DSN: {SENTRY_DSN}")

# Initialize Sentry
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=1.0,
    environment="test",
    send_default_pii=False,
    enable_tracing=True,
    integrations=[
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        ),
    ],
)

print("✅ Sentry SDK initialized successfully")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_breadcrumbs():
    """Test breadcrumb functionality"""
    print("\n📍 Testing breadcrumbs...")

    sentry_sdk.add_breadcrumb(
        category="test",
        message="Test breadcrumb 1",
        level="info",
        data={"test_id": 1, "status": "started"},
    )

    sentry_sdk.add_breadcrumb(
        category="test",
        message="Test breadcrumb 2",
        level="debug",
        data={"test_id": 2, "status": "processing"},
    )

    print("   ✓ Breadcrumbs added")


def test_context():
    """Test context setting"""
    print("\n🔧 Testing context...")

    sentry_sdk.set_context(
        "test_context",
        {
            "test_run": "sentry_integration_test",
            "timestamp": time.time(),
            "user": "mike.porenta@goaptive.com",
        },
    )

    sentry_sdk.set_context(
        "metrics", {"input_tokens": 1000, "output_tokens": 500, "total_cost": 0.015}
    )

    print("   ✓ Context data set")


def test_performance_span():
    """Test performance monitoring with spans"""
    print("\n⚡ Testing performance spans...")

    with sentry_sdk.start_span(op="test.operation", name="test_operation") as span:
        span.set_data("operation_type", "test")
        span.set_data("complexity", "simple")

        # Simulate some work
        time.sleep(0.1)

        print("   ✓ Performance span created")


def test_logging_integration():
    """Test logging integration"""
    print("\n📝 Testing logging integration...")

    logger.info("This is an INFO log message")
    logger.warning("This is a WARNING log message")

    print("   ✓ Logging messages sent")


def test_custom_event():
    """Test custom event capture"""
    print("\n📨 Testing custom event...")

    sentry_sdk.capture_message("Custom test message from Sentry SDK test", level="info")

    print("   ✓ Custom message sent")


def test_exception_capture():
    """Test exception capture"""
    print("\n🚨 Testing exception capture...")

    try:
        # Intentionally cause an exception
        _ = 1 / 0
    except ZeroDivisionError as e:
        sentry_sdk.set_context(
            "error_context", {"operation": "division", "attempted_divisor": 0}
        )
        sentry_sdk.capture_exception(e)
        print("   ✓ Exception captured and sent to Sentry")


def test_user_context():
    """Test user context setting"""
    print("\n👤 Testing user context...")

    sentry_sdk.set_user(
        {"email": "mike.porenta@goaptive.com", "username": "mike.porenta"}
    )

    print("   ✓ User context set")


def test_tags():
    """Test tag functionality"""
    print("\n🏷️  Testing tags...")

    sentry_sdk.set_tag("test_run", "integration_test")
    sentry_sdk.set_tag("environment", "docker_local")
    sentry_sdk.set_tag("component", "claude_swarm")

    print("   ✓ Tags set")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Sentry SDK Integration Test")
    print("=" * 60)

    # Run all test functions
    test_breadcrumbs()
    test_context()
    test_user_context()
    test_tags()
    test_performance_span()
    test_logging_integration()
    test_custom_event()
    test_exception_capture()

    # Send a final message to wrap everything up
    print("\n📤 Sending final test message...")
    sentry_sdk.capture_message(
        "Sentry SDK integration test completed successfully", level="info"
    )

    # Flush events to ensure they're sent
    print("\n⏳ Flushing events to Sentry...")
    sentry_sdk.flush(timeout=5)

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n📊 Check your Sentry dashboard at: http://localhost")
    print("   Login: mike.porenta@goaptive.com / admin")
    print("\nYou should see:")
    print("  • 2 issues (custom message + exception)")
    print("  • Breadcrumbs in the event details")
    print("  • Performance transaction data")
    print("  • User context and tags")
    print("=" * 60)


if __name__ == "__main__":
    main()
