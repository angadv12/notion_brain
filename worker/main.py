"""Worker entry point for notion_brain notification service.

Usage:
    python -m worker.main overdue
    python -m worker.main urgent
    python -m worker.main today
    python -m worker.main tomorrow
    python -m worker.main high_priority
"""

import sys
import asyncio

from notification_worker import check_and_notify, run_all_checks


async def main():
    """Main entry point for the notification worker."""
    # Get trigger type from command line argument
    trigger_type = sys.argv[1] if len(sys.argv) > 1 else "today"

    # Special case: "all" runs all checks
    if trigger_type == "all":
        results = await run_all_checks()
        print(f"\nAll checks completed. Results: {results}")
    else:
        result = await check_and_notify(trigger_type)
        print(f"\nCheck completed. Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
