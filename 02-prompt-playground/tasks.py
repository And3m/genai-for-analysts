"""
Predefined business task templates for the prompt playground.
Each task defines: instruction, example_input, examples (for few-shot), and role (for role prompting).
"""

TASK_TEMPLATES = {
    "Customer Feedback Classification": {
        "description": "Classify customer feedback into: Positive, Negative, or Neutral. Extract the primary topic.",
        "instruction": "Classify the customer feedback below into one of: Positive, Negative, or Neutral. Also identify the primary topic (e.g., Delivery, Product Quality, Customer Service, Pricing). Return format: Classification: <label> | Topic: <topic>",
        "example_input": "I ordered the laptop stand last Tuesday and it arrived two days late. The packaging was damaged but thankfully the product itself is fine. I'm not sure I'd order again.",
        "role": "a customer experience analyst specializing in NPS and CSAT analysis",
        "examples": [
            {
                "input": "The onboarding team was incredibly helpful. Got me set up in under an hour!",
                "output": "Classification: Positive | Topic: Customer Service",
            },
            {
                "input": "Charged twice for the same order. Still waiting for a refund after two weeks.",
                "output": "Classification: Negative | Topic: Billing",
            },
            {
                "input": "Package arrived on time. Product is what I expected.",
                "output": "Classification: Neutral | Topic: Delivery",
            },
        ],
    },
    "Invoice Entity Extraction": {
        "description": "Extract structured fields from invoice text: vendor, date, total amount, and line items.",
        "instruction": "Extract the following fields from the invoice text: Vendor Name, Invoice Date, Total Amount, and Line Items (as a list). Return as structured JSON.",
        "example_input": "INVOICE\nVendor: Apex Office Supplies Ltd.\nDate: 15 March 2024\nItem 1: Printer cartridges x4 — $48.00\nItem 2: A4 paper (5 reams) — $32.50\nShipping: $8.00\nTotal: $88.50",
        "role": "an accounts payable specialist with expertise in invoice processing and ERP systems",
        "examples": [
            {
                "input": "TechRent Inc. | Invoice Date: Jan 5 2024 | Laptop rental 3 months $900 | Total: $900",
                "output": '{"vendor": "TechRent Inc.", "date": "2024-01-05", "total": 900.00, "line_items": [{"description": "Laptop rental 3 months", "amount": 900.00}]}',
            }
        ],
    },
    "Support Ticket Categorization": {
        "description": "Categorize IT support tickets by type and urgency level.",
        "instruction": "Categorize this support ticket by Type (Hardware / Software / Network / Access / Other) and Urgency (Critical / High / Medium / Low). Provide a one-sentence recommended first action. Format: Type: <type> | Urgency: <urgency> | Action: <action>",
        "example_input": "Hi team, my laptop won't connect to the VPN since this morning's Windows update. I have a client call in 2 hours and need access to the shared drive urgently. — Priya",
        "role": "an ITIL-certified IT service desk manager prioritizing tickets for a 50-person enterprise team",
        "examples": [
            {
                "input": "The office printer keeps jamming. Non-urgent, just annoying.",
                "output": "Type: Hardware | Urgency: Low | Action: Schedule a technician visit during off-peak hours to inspect the printer feed mechanism.",
            },
            {
                "input": "Production database is down. All orders are failing. URGENT.",
                "output": "Type: Software | Urgency: Critical | Action: Escalate immediately to the database admin team and initiate the incident response protocol.",
            },
        ],
    },
}
