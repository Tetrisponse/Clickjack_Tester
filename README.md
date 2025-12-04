# Clickjack Tester

A lightweight, automated toolkit for testing URLs for Clickjacking vulnerabilities. This tool checks for security headers (`X-Frame-Options` and `Content-Security-Policy`) and generates visual Proof-of-Concept (PoC) HTML files for client demonstration.

## Features

- **Single URL or Batch Mode**: Test a single site on the fly or scan a list of hundreds.

- **Automated Header Analysis**: Checks for `X-Frame-Options` (DENY/SAMEORIGIN) and `Content-Security-Policy` (frame-ancestors).

- **Dynamic PoC Generation**:

  - Vulnerable: Generates a red "VULNERABLE" HTML page that embeds the target.

  - Safe: Generates a green "SAFE" HTML page confirming protection.

- **Browser Integration**: Automatically opens the generated PoC files in your default browser for immediate verification.

- **Smart Pausing**: Prevents browser crashes during large scans by pausing after a set number of tabs.

- **Reporting**: Optionally saves a summary scan log to a text file.

- **Cleanup Utility**: Includes a script to quickly delete generated PoC files.

## Prerequisites

- Python 3.x

- `requests` library

## Installation
- Clone this repository or download the scripts.

- Install the required Python library:
```
Bash
pip install requests
```

## Usage

### 1. The Scanner (`clickjack_tester.py`)
The scanner logic is simple: If you provide a single URL (`-u`), it checks that. If you don't, it looks for a list of URLs (`-i`).

**A. Single URL Mode (Spot Check)**
  
Use the `-u` flag to test one specific URL immediately. This ignores any input files.
  
```
Bash
python clickjack_tester.py -u https://google.com
```

**B. Batch Mode (List of URLs)**
By default, the script looks for a file named `target_urls.txt` in the same directory.
```
Bash
python clickjack_tester.py
```

Custom Input File: Specify your own list of URLs (one per line).
```
Bash
python clickjack_tester.py -i my_clients.txt
```

**C. Advanced Options**
Save a Report (`-o`): Save a timestamped log of the scan results (SAFE/VULNERABLE/ERROR) to a text file. Works in both Single and Batch modes.
```
Bash
python clickjack_tester.py -u example.com -o check_result.txt
```

Adjust Batch Size (`-b`): To prevent opening too many browser tabs at once, the script pauses every 5 URLs by default. You can change this limit.
```
Bash
# Pause after every 10 URLs
python clickjack_tester.py -i list.txt -b 10
```

### 2. The Cleanup Tool (`cleanup.py`)
The scanner generates many `.html` files (e.g., `SAFE_google_com.html`, `VULN_example_com.html`). Use this script to delete them all instantly.
```
Bash
python cleanup.py
```

## Input File Format
Your input file (e.g., `target_urls.txt`) should contain one URL per line. The script will automatically add `http://` if it is missing.
```
Plaintext
https://www.google.com
http://example.com
stackoverflow.com
```

## How It Works
The script sends a generic `HTTP GET` request to the target URL and inspects the response headers:

`X-Frame-Options`: Checks if set to `DENY` or `SAMEORIGIN`.

`Content-Security-Policy`: Checks for the presence of the frame-ancestors directive.

If either is present, the site is marked SAFE. If both are missing, it is marked VULNERABLE.

Note: This tool uses a "Same-Origin Policy" workaround. Since a parent HTML file cannot check if an iframe loaded successfully, we perform the check in Python first, then generate the HTML file with the appropriate message ("Hooray" vs "Vulnerable").

## Disclaimer
This tool is intended for security professionals and systems administrators to test systems they own or have explicit permission to test. Do not use this tool on unauthorized targets.
