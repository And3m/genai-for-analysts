"""
Generate synthetic IT support ticket training data.
Run: python data/generate_sample_data.py
Outputs: data/tickets.csv
"""

import csv
import os
import random

random.seed(42)

TEMPLATES = {
    "Hardware": [
        "My laptop screen is flickering and won't display properly.",
        "The office printer keeps jamming on the second tray.",
        "My keyboard stopped working after a spill.",
        "The monitor is showing vertical lines across the display.",
        "My mouse cursor is jumping around randomly.",
        "The docking station is not charging my laptop.",
        "Hard drive making clicking sounds — worried about data loss.",
        "Laptop fan is extremely loud and the device is overheating.",
    ],
    "Software": [
        "Excel crashes every time I open a file larger than 10MB.",
        "The CRM application gives a 500 error when submitting a form.",
        "Outlook calendar is not syncing with the shared team calendar.",
        "Adobe Acrobat won't open PDFs after the recent Windows update.",
        "The ERP system is running very slowly since the upgrade last night.",
        "Teams is not showing my status as available even though I'm logged in.",
        "The reporting tool is generating incorrect totals on the dashboard.",
        "Browser extensions are causing the internal portal to crash.",
    ],
    "Network": [
        "I cannot connect to the VPN from home — getting authentication error.",
        "The office WiFi drops every 10 minutes in the east wing.",
        "File shares on the server are not accessible from my machine.",
        "Video calls are very choppy and keep cutting out.",
        "Internet speed is extremely slow — tested at 2 Mbps.",
        "Cannot access the internal SharePoint site from the branch office.",
        "Firewall is blocking a legitimate business application.",
        "Remote desktop connection keeps timing out after 2 minutes.",
    ],
    "Access": [
        "I need access to the finance shared drive for the new project.",
        "My account was locked after entering the wrong password too many times.",
        "New employee needs Salesforce access set up — starts Monday.",
        "I cannot access the HR portal — says my account is inactive.",
        "Need admin rights to install approved software on my workstation.",
        "Two-factor authentication is not sending the SMS code to my phone.",
        "My login credentials stopped working after a password reset.",
        "Request access to the data warehouse for BI reporting.",
    ],
    "Billing": [
        "I was charged twice for the annual software licence renewal.",
        "The invoice for last month does not match the agreed contract price.",
        "Need a receipt for the IT equipment purchase from last week.",
        "Credit card was declined when trying to renew the cloud subscription.",
        "The cost centre code on the invoice is incorrect — needs to be updated.",
        "Overpayment on previous invoice — requesting a credit note.",
    ],
    "Other": [
        "Can you confirm the IT support hours over the holiday period?",
        "I need a recommendation for a good project management tool.",
        "How do I set up my out-of-office message in Outlook?",
        "What is the data retention policy for emails?",
        "Where can I find the approved software list?",
        "I'd like to request a laptop upgrade as part of the refresh cycle.",
    ],
}

rows = []
for label, templates in TEMPLATES.items():
    for _ in range(80 // len(templates) + 1):
        for template in templates:
            rows.append({"text": template, "label": label})

random.shuffle(rows)

output_path = os.path.join(os.path.dirname(__file__), "tickets.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["text", "label"])
    writer.writeheader()
    writer.writerows(rows[:400])  # keep dataset manageable

print(f"Generated {min(400, len(rows))} ticket samples at {output_path}")
