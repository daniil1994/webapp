# Craftum.com Header Parser

Simple script for parsing and analyzing HTTP headers from craftum.com.

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Parse headers from craftum.com (default):

```bash
python parse_craftum_headers.py
```

Parse headers from a custom URL:

```bash
python parse_craftum_headers.py https://example.com
```

## Output

The script will:
1. Display all HTTP headers in the console
2. Show security-related headers separately
3. Save the complete header data to `craftum_headers.json`

## Features

- Fetches and displays all HTTP headers
- Highlights important security headers
- Saves results to JSON file for further analysis
- Supports custom URLs via command line argument
- Includes timestamp and status code information

## Example Output

```
Fetching headers from: https://craftum.com
------------------------------------------------------------

Status Code: 200
Timestamp: 2026-02-09 12:00:00
URL: https://craftum.com

============================================================
HTTP HEADERS:
============================================================
Content-Type: text/html; charset=utf-8
Server: nginx
...

============================================================

SECURITY HEADERS:
------------------------------------------------------------
Content-Security-Policy: ...
Strict-Transport-Security: ...
...

✓ Headers saved to: craftum_headers.json
```
