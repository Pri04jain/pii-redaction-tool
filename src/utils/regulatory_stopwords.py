"""Stopwords for filtering false positive organization detections"""

# Regulatory bodies and institutional terms that should not be flagged as organizations
REGULATORY_STOPWORDS = {
    # Indian regulatory bodies
    'sebi', 'rbi', 'irdai', 'pfrda', 'fssai', 'npci', 'nsdl', 'cdsl',
    
    # Stock exchanges
    'bse', 'nse', 'mcx', 'ncdex', 'stock exchange', 'stock exchanges',
    
    # Generic institutional terms
    'companies act', 'securities act', 'sebi act', 'listing regulations',
    'rta', 'cdp', 'scsb', 'syndicate', 'broker', 'registrar',
    'depository', 'depositories', 'roc', 'registrar of companies',
    
    # IPO/Securities terms
    'brlm', 'book running lead manager', 'book running lead managers',
    'underwriter', 'underwriters', 'underwriting', 'underwriting agreement',
    'anchor investor', 'anchor investors', 
    'promoter selling shareholder', 'promoter selling shareholders',
    'qualified institutional buyer', 'qualified institutional buyers',
    'qib', 'qibs', 'rii', 'retail individual investor',
    'retail individual investors', 'hni', 'high net worth individual',
    'asba', 'application supported by blocked amount',
    'red herring prospectus', 'draft red herring prospectus',
    'drhp', 'rhp', 'prospectus',
    'book building', 'book building process',
    'price band', 'issue price', 'bidder', 'bidders',
    'mutual fund', 'mutual funds',
    'registrar and share transfer agent', 'registrar and share transfer agents',
    'depository participant', 'depository participants',
    
    # Government entities (generic)
    'government', 'government of india', 'central government',
    'state government', 'ministry', 'department',
    
    # Generic organizational terms
    'authority', 'commission', 'board', 'council', 'committee',
    'act', 'exchange', 'regulation', 'rules',
    
    # Financial terms that get misclassified
    'equity', 'shares', 'shareholders', 'securities',
    'public issue', 'ipo', 'offer', 'offering',
}

# Common words that appear with organization patterns but aren't orgs
GENERIC_ORG_WORDS = {
    'act', 'exchange', 'commission', 'board', 'authority',
    'rules', 'regulation', 'regulations', 'code', 'agreement',
    'circular', 'notification', 'guidelines',
    'investor', 'investors', 'shareholder', 'shareholders',
    'bidder', 'bidders', 'participant', 'participants',
}


def is_regulatory_term(text: str) -> bool:
    """
    Check if text is a regulatory/institutional term
    
    Args:
        text: Text to check
    
    Returns:
        True if it's a regulatory term that shouldn't be flagged
    """
    text_lower = text.lower().strip()
    
    # Direct match in stopwords
    if text_lower in REGULATORY_STOPWORDS:
        return True
    
    # Single-word generic terms
    if len(text.split()) == 1 and text_lower in GENERIC_ORG_WORDS:
        return True
    
    # Phrases containing specific regulatory terms
    regulatory_phrases = [
        'act', 'regulation', 'rules', 'code', 'prospectus',
        'underwriter', 'underwriting', 'investor', 'shareholder',
        'bidder', 'participant', 'registrar',
    ]
    
    for phrase in regulatory_phrases:
        if phrase in text_lower:
            # But allow actual company names like "ABC Corporation Act" (rare)
            # Only filter if it ENDS with the regulatory term or is mostly regulatory
            if (text_lower.endswith(phrase) or 
                text_lower.endswith(phrase + 's') or
                text_lower.startswith(phrase + ' ')):
                
                # Exception: Don't filter bank/company names
                if not any(company_word in text_lower for company_word in 
                          ['bank', 'limited', 'ltd', 'corporation', 'corp', 'company', 'inc']):
                    return True
    
    return False
