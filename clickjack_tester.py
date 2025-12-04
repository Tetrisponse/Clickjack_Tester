import os
import webbrowser
import requests
import argparse
import datetime
import sys

# --- TEMPLATES ---
HTML_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="en-US">
<head>
    <meta charset="UTF-8">
    <title>Clickjacking Test: {url}</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 20px; }}
        .status-box {{ padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
        .vulnerable {{ background-color: #ffcccc; border: 2px solid red; color: #900; }}
        .safe {{ background-color: #ccffcc; border: 2px solid green; color: #006600; }}
        iframe {{ border: 2px dashed #ccc; width: 1000px; height: 500px; }}
        .note {{ font-size: 0.8em; color: #666; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="status-box {css_class}">
        <h3>{message}</h3>
    </div>
    <iframe src="{url}"></iframe>
    <p class="note">Target: {url}</p>
</body>
</html>
"""

def parse_arguments():
    """Handles command line arguments."""
    parser = argparse.ArgumentParser(description="Clickjacking PoC Generator")
    
    # -u argument (Single URL mode) - NEW!
    parser.add_argument(
        '-u', '--url', 
        type=str, 
        help='Check a single URL (ignores input file if provided)'
    )

    # -i argument (Input file)
    parser.add_argument(
        '-i', '--input', 
        type=str, 
        default='target_urls.txt',
        help='Input text file containing URLs (default: target_urls.txt)'
    )
    
    # -o argument (Output file)
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        help='Optional output text file to save a summary of results'
    )

    # -b argument (Batch size)
    parser.add_argument(
        '-b', '--batch', 
        type=int, 
        default=5,
        help='Number of URLs to open before pausing (default: 5)'
    )
    
    return parser.parse_args()

def get_urls_from_file(filename):
    """Reads URLs from a text file."""
    if not os.path.exists(filename):
        print(f"[-] Error: The input file '{filename}' was not found.")
        return []

    valid_urls = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            clean_url = line.strip()
            if clean_url:
                valid_urls.append(clean_url)
    return valid_urls

def check_security_headers(url):
    """
    Checks the URL for X-Frame-Options or CSP headers.
    Returns: True (Safe), False (Vulnerable), None (Error)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        xfo = response.headers.get('X-Frame-Options', '').upper()
        csp = response.headers.get('Content-Security-Policy', '').lower()
        
        is_safe = False
        
        if xfo in ['DENY', 'SAMEORIGIN']:
            is_safe = True
            
        if 'frame-ancestors' in csp:
            is_safe = True

        return is_safe

    except requests.exceptions.RequestException as e:
        print(f"[-] Could not connect to {url}: {e}")
        return None 

def generate_poc():
    # 1. Parse Arguments
    args = parse_arguments()
    input_file = args.input
    output_file = args.output
    batch_size = args.batch
    single_url = args.url

    # 2. Determine Source of URLs
    # If -u is provided, we create a list of one and ignore the file.
    if single_url:
        print(f"--- Single URL Mode: {single_url} ---")
        urls = [single_url]
        input_source_name = "Single URL Argument"
    else:
        # Otherwise, fall back to the file
        urls = get_urls_from_file(input_file)
        input_source_name = input_file
        if not urls:
            if not os.path.exists(input_file):
                 pass 
            else:
                print("[-] No URLs found in file.")
            return
        print(f"--- Batch Mode: {len(urls)} URLs from '{input_file}' ---")

    
    results_log = []

    # Enumerate allows us to track the current index (i)
    for i, url in enumerate(urls):
        
        # --- BATCH PAUSE LOGIC ---
        # Only pause if we are processing a list (length > 1) and hit the limit
        if len(urls) > 1 and i > 0 and i % batch_size == 0:
            print(f"\n[!] Paused after {i} URLs to prevent browser overload.")
            try:
                input("    Press Enter to continue scanning (or Ctrl+C to stop)...")
            except KeyboardInterrupt:
                print("\n\n[-] Scan cancelled by user.")
                break

        # Ensure scheme
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        print(f"[*] Testing: {url}...")
        
        is_safe = check_security_headers(url)
        
        if is_safe is None:
            log_entry = f"{url} - ERROR (Connection Failed)"
            print(f"    Skipping generation for {url} due to connection error.")
            results_log.append(log_entry)
            continue

        if is_safe:
            msg = "Hooray, I am not vulnerable to clickjacking! Good job!"
            css = "safe"
            filename = f"SAFE_{url.replace('://', '_').replace('/', '_')}.html"
            print("    Result: Protected.")
            results_log.append(f"{url} - SAFE")
        else:
            msg = ("I am vulnerable to clickjacking! Please fix me by adding the needed "
                   "security headers: X-Frame-Options: DENY and Content-Security-Policy: frame-ancestors 'none'")
            css = "vulnerable"
            filename = f"VULN_{url.replace('://', '_').replace('/', '_')}.html"
            print("    Result: VULNERABLE.")
            results_log.append(f"{url} - VULNERABLE")

        # Create HTML
        html_content = HTML_TEMPLATE.format(url=url, message=msg, css_class=css)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Trigger Browser
        webbrowser.open('file://' + os.path.realpath(filename))

    # 3. Write Summary to Output File (Optional)
    if output_file and results_log:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"Clickjacking Scan Report\n")
                f.write(f"Scan Time: {timestamp}\n")
                f.write(f"Input Source: {input_source_name}\n")
                f.write("--------------------------------------------------\n")
                for line in results_log:
                    f.write(line + "\n")
            print(f"\n[+] Summary results saved to: {output_file}")
        except IOError as e:
            print(f"\n[-] Error writing to output file: {e}")

    print("\n--- Done! ---")

if __name__ == "__main__":
    generate_poc()
