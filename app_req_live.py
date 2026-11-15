"""Backward compatibility wrapper for app_req_live.py (req_live thread).

Delegates CLI batch scraping to scripts/batch_scrape.py with thread='req_live'.
Maintains full compatibility with run_scrape_req_live.bat.
"""

import sys
from scripts.batch_scrape import run_batch_scrape

if __name__ == "__main__":
    cli_start = None
    cli_end = None
    if len(sys.argv) == 2:
        try:
            cli_start = int(sys.argv[1])
            cli_end = cli_start
        except ValueError:
            pass
    elif len(sys.argv) >= 3:
        try:
            cli_start = int(sys.argv[1])
            cli_end = int(sys.argv[2])
        except ValueError:
            pass

    run_batch_scrape(
        thread_key="req_live",
        num_pages=10,
        start_page=cli_start,
        end_page=cli_end,
    )
