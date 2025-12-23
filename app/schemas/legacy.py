from typing import Dict, Any

def normalize_legacy_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes legacy data formats before strict Pydantic validation.
    Mainly handles Float -> Integer Pence conversions for older exports.
    """
    if "automation_rules" in data:
        for r in data["automation_rules"]:
            if "trigger_value" in r and r["trigger_value"] is not None: r["trigger_value"] = int(r["trigger_value"] * 100)
            if "transfer_value" in r and r["transfer_value"] is not None: r["transfer_value"] = int(r["transfer_value"] * 100)
    if "tax_limits" in data:
        for t in data["tax_limits"]:
            if "amount" in t and t["amount"] is not None: t["amount"] = int(t["amount"] * 100)
    if "accounts" in data:
        for a in data["accounts"]:
            if "starting_balance" in a: a["starting_balance"] = int(float(a["starting_balance"]) * 100)
            if "original_loan_amount" in a and a["original_loan_amount"]: a["original_loan_amount"] = int(float(a["original_loan_amount"]) * 100)
    if "costs" in data:
        for c in data["costs"]:
            if "value" in c: c["value"] = int(float(c["value"]) * 100)
    
    # Future sanitization (e.g. missing fields) can go here
    
    return data
