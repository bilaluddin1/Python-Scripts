import requests



headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer ",
    'X-Csrftoken': '',
    'Cookie': '__Host-grv_app_session=; __Host-grv_app_session_subject=; csrftoken=; sessionid='
}

data = {
"test": "70",
        "thread_id": 0,
        "url": "",
        "push_to_jira": "False",
        "reporter": 1,
        "unique_id_from_tool": "FINDING_0001",
        "vuln_id_from_tool": "",
        "title": "",
        "active": "False",
        "verified": "True",
        "found_by":[32],
        "numerical_severity": 1.1,
        "description": "",
        "impact": "",
        "severity_justification": "",
        "sla_start_date": "2024-03-01",
        "last_edited_time": "2024-03-01",
        "references": "",
        "component_name": "",
        "severity": ""
}

response = requests.post(
    "https://yourdomain.com/api/v2/findings/",
    json=d,
    headers=headers,
    verify=False  # ⚠️ Disable SSL verification if Burp is using self-signed cert
)

print(response.status_code)
print(response.text)
