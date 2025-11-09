from loguru import logger
import sys
import os
import pytz
from typing import Dict, Any, Optional
from tzlocal import get_localzone
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.integrations.loguru import LoggingLevels

load_dotenv()
env_log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
print(f"Log level set to: {env_log_level}")
import sentry_sdk


class LogConfig:
    """Centralized logging configuration for the application"""

    def __init__(
        self, root_dir: str = None, timezone: str = None, log_level: str = "DEBUG"
    ):
        self.logger = logger
        self._configured: bool = False
        self.root_dir = root_dir or str(Path(__file__).parent.parent)
        self.logs_dir = os.path.join(self.root_dir, "logs")
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
        print(f"LogConfig initialized with root_dir: {self.root_dir}")
        print(f"Logs will be written to: {self.logs_dir}")
        if timezone:
            self.tz_name = pytz.timezone(timezone)
        else:
            try:
                # Get system's local timezone
                self.tz_name = get_localzone()
                print(f"Detected local timezone: {self.tz_name}")
            except Exception as e:
                # Fallback to America/Denver if detection fails
                print(
                    f"Could not detect timezone ({e}), falling back to America/Denver"
                )
                self.tz_name = pytz.timezone("America/Denver")

        self.log_level = log_level

        # Common format for all logs
        self.log_format = self._format_log

        # Format for detailed debugging
        self.debug_format = self._format_debug

        # Pretty format for structured data
        self.pretty_format = lambda record: self._format_record(record)
        sentry_sdk.init(
            dsn="https://586645b1744aa1be7b773837d822f918@o4510262831546368.ingest.us.sentry.io/4510262842490880",
            # Add data like request headers and IP for users, if applicable;
            # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
            traces_sample_rate=1.0,
            enable_logs=True,
            integrations=[
                LoguruIntegration(
                    level=LoggingLevels.INFO.value,  # Capture INFO and above as breadcrumbs
                    event_level=LoggingLevels.ERROR.value,  # Send ERROR logs as events
                    sentry_logs_level=LoggingLevels.INFO.value,  # Capture INFO and above as logs
                )
            ],
        )

    def set_logging_level(self, level: str):
        """Set the logging level dynamically"""
        self.log_level = level
        if self._configured:
            self.logger.remove()
            self.setup()
        print("\n" + "=" * 80)
        print(f"🤖 Logging level set to {level} 🤖")
        print("=" * 80)

    def _format_record(self, record: Dict[str, Any]) -> str:
        """Custom formatter for structured data"""

        def format_value(v):
            if isinstance(v, (dict, list)):
                return f"\n{str(v)}"
            elif isinstance(v, (int, float)):
                return f"{v:,}"
            return str(v)

        msg = record["message"]

        # Format any structured data
        if isinstance(msg, dict):
            formatted_dict = "\n".join(
                f"    {k}: {format_value(v)}" for k, v in msg.items()
            )
            msg = f"\n{formatted_dict}"
        elif isinstance(msg, (list, tuple)):
            formatted_list = "\n".join(f"    - {format_value(item)}" for item in msg)
            msg = f"\n{formatted_list}"

        return msg

    def _format_log(self, record):
        """Format log record with relative file path"""
        if record["file"].path == "<string>":
            rel_file = "inline"
        else:
            rel_file = os.path.relpath(record["file"].path, self.root_dir)
        return (
            f"<green>{record['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}</green> | "
            f"<level>{record['level']: <8}</level> | "
            f"<cyan>{rel_file}:{record['line']}</cyan> | "
            f"<level>{record['message']}</level>"
        )

    def _format_debug(self, record):
        """Format debug log record with relative file path"""
        if record["file"].path == "<string>":
            rel_file = "inline"
        else:
            rel_file = os.path.relpath(record["file"].path, self.root_dir)
        return (
            f"<green>{record['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}</green> | "
            f"<level>{record['level']: <8}</level> | "
            f"<cyan>{rel_file}:{record['line']}</cyan> | "
            f"Process: {record['process']} | Thread: {record['thread']} | "
            f"<level>{record['message']}</level>"
        )

    def setup(self, log_level="DEBUG"):
        """Set up logging configuration"""
        if log_level != "DEBUG":
            self.log_level = log_level
            print(f"Log level overridden to: {self.log_level}")

        if self._configured:
            return
        # Remove any existing handlers

        self.logger.remove()

        # Derive today's date in specified timezone
        today_str = self.today_str()

        # Clean up any date-stamped log files older than today
        # (run before adding new handlers)
        try:
            self._cleanup_old_dated_logs(today_str)
            print(
                f"[LogConfig] Old dated logs cleaned up before "
                f"setting up new logs for {today_str}"
            )
        except (
            Exception
        ) as e:  # pragma: no cover - defensive; logging not yet configured
            print(f"[LogConfig] Warning: cleanup failed: {e}")

        # Build dated filenames (pattern: YYYY_MM_DD_<name>.log)
        app_log_path = os.path.join(self.logs_dir, f"{today_str}_app.log")
        error_log_path = os.path.join(self.logs_dir, f"{today_str}_error.log")
        debug_log_path = os.path.join(self.logs_dir, f"{today_str}_debug.log")

        # Add console logging with standard format
        self.logger.add(
            sink=sys.stderr,
            level=self.log_level,
            format=self.log_format,
            enqueue=True,  # Thread-safe logging
            colorize=True,
        )

        # Primary application log
        self.logger.add(
            sink=app_log_path,
            level=self.log_level,
            format=self.log_format,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            enqueue=True,
        )

        # Error-only logs with more detail
        self.logger.add(
            sink=error_log_path,
            level="ERROR",
            format=self.debug_format,
            rotation="10 MB",
            retention="1 month",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

        # Debug logs with full detail (always enabled, regardless of main log level)
        self.logger.add(
            sink=debug_log_path,
            level="DEBUG",
            format=self.debug_format,
            rotation="100 MB",
            retention="3 days",
            compression="zip",
            enqueue=True,
        )
        self._configured = True
        self.logger.debug(
            f"Logging configured with dated files: {app_log_path}, "
            f"{error_log_path}, {debug_log_path}"
        )

    def today_str(self) -> str:
        """Return today's date string in the configured timezone (YYYY_MM_DD)."""

        dt = datetime.now(self.tz_name) if self.tz_name else datetime.now()
        return dt.strftime("%Y_%m_%d")

    def _parse_dated_prefix(self, filename: str) -> Optional[date]:
        """Parse a leading YYYY_MM_DD_ date from a filename into a date object.
        Returns None if pattern not matched or invalid.
        """
        try:
            parts = filename.split("_", 3)  # YYYY MM DD rest
            if len(parts) < 4:
                return None
            y, m, d = parts[0], parts[1], parts[2]
            if not (len(y) == 4 and len(m) == 2 and len(d) == 2):
                return None
            return date(int(y), int(m), int(d))
        except Exception:
            return None

    def _cleanup_old_dated_logs(self, today_str: str):
        """Delete log files whose leading date (YYYY_MM_DD_) is older than today.

        We only act on files that match our naming scheme to avoid deleting
        unrelated artifacts.
        """
        today_parts = today_str.split("_")
        today_dt = date(int(today_parts[0]), int(today_parts[1]), int(today_parts[2]))
        removed: list[str] = []
        for fname in os.listdir(self.logs_dir):
            if not fname.endswith(".log") and not fname.endswith(".log.zip"):
                continue
            f_date = self._parse_dated_prefix(fname)
            if f_date and f_date < today_dt:
                full_path = os.path.join(self.logs_dir, fname)
                try:
                    os.remove(full_path)
                    removed.append(fname)
                except Exception as e:
                    print(f"[LogConfig] Failed to remove old log {fname}: {e}")
        if removed:
            print(f"[LogConfig] Removed outdated log files: {', '.join(removed)}")


# Create global instance
log_config = LogConfig(log_level=env_log_level)
