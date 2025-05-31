import os
import json
import re
import zipfile

# === Step 1: Unzip the archive ===
def unzip_archive(zip_path, extract_to='unzipped_vapt'):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

# === Step 2: Extract relevant data from markdown ===
def parse_markdown(md_text):
    def get(pattern, default=''):
        match = re.search(pattern, md_text, re.DOTALL)
        return match.group(1).strip() if match else default

    return {
        "title": get(r"# \[(.*?)\] - (.*?)\n", "Unknown"),
        "component_name": get(r"Components:\s*(.*)"),
        "risk_rating": get(r"\*Risk Rating\*:\s*(.*)"),
        "likelihood": get(r"\*Likelihood\*:\s*(.*)"),
        "potential_impact": get(r"\*Impact:\*\s*(.*?)\n\n", get(r"\*Potential Impact\*:\s*(.*)")),
        "owasp": get(r"OWASP.*?:\s*(.*)"),
        "cvss": get(r"CVSS.*?:\s*(.*)"),
        "description": get(r"\*Description:\*\s*(.*?)\n\n"),
        "steps_to_reproduce": get(r"\*Steps to Reproduce\*:\s*(.*?)\n(?:\*|!|Labels:|Org Severity:)", "").replace("•", "-"),
        "status": get(r"Status:\s*(.*)"),
        "severity": get(r"Org Severity:\s*(.*)")
    }

# === Step 3: Walk through markdown files and convert ===
def convert_markdowns_to_json(folder):
    findings = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), "r", encoding="ISO-8859-1") as f:
                    content = f.read()
                    finding = parse_markdown(content)
                    findings.append(finding)
    return findings

# === Step 4: Run it all ===
if __name__ == "__main__":
    zip_file_path = "Archive3.zip"  # or full path
    extracted_folder = unzip_archive(zip_file_path)

    findings = convert_markdowns_to_json(extracted_folder)

    with open("Archive3.json", "w", encoding="ISO-8859-1") as f:
        json.dump(findings, f, indent=2)

    print(f"[+] Converted {len(findings)} markdown files into JSON!")
