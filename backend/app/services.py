REQUIRED_DOCS = {"Bank Statement", "Payslip", "Identity Document"}

def calculate_risk(app, customer, docs):
    # Explainable demo scoring; not a real credit model.
    score = 50
    reasons = []
    if app.credit_score >= 750:
        score -= 18; reasons.append("Strong credit score")
    elif app.credit_score < 650:
        score += 22; reasons.append("Low credit score")
    income_monthly = max(customer.annual_income / 12, 1)
    dti = app.monthly_debt / income_monthly
    if dti > .45:
        score += 20; reasons.append("High debt-to-income ratio")
    elif dti < .25:
        score -= 8; reasons.append("Low debt-to-income ratio")
    lti = app.amount / max(customer.annual_income, 1)
    if lti > 1.2:
        score += 18; reasons.append("High loan-to-income ratio")
    verified = {d.document_type for d in docs if d.verification_status == "Verified"}
    missing = sorted(REQUIRED_DOCS - verified)
    if missing:
        score += min(18, len(missing)*6); reasons.append("Missing/unverified required documents")
    if customer.kyc_status != "Verified":
        score += 12; reasons.append("KYC not verified")
    score = max(0, min(100, round(score)))
    band = "Low" if score < 35 else "Medium" if score < 65 else "High"
    return score, band, reasons, missing

def underwriting_brief(app, customer, docs):
    score, band, reasons, missing = calculate_risk(app, customer, docs)
    doc_types = ", ".join(sorted({d.document_type for d in docs})) or "none"
    return (
        f"AI-assisted underwriting brief (demo): {customer.full_name} requests "
        f"{app.product} of ₹{app.amount:,.0f} for {app.tenure_months} months. "
        f"Credit score: {app.credit_score}. Annual income: ₹{customer.annual_income:,.0f}. "
        f"Risk band: {band} ({score}/100). Factors: {', '.join(reasons) or 'No material flags'}. "
        f"Documents on file: {doc_types}. "
        f"Missing verified documents: {', '.join(missing) if missing else 'none'}. "
        "This output is decision support only; a human reviewer must make the final decision."
    )
