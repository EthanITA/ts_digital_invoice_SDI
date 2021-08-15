import json

with open("cred") as f:
    company_info = json.load(f)
    email, password, VAT_number = company_info["email"], company_info["password"], company_info["VAT_number"]
