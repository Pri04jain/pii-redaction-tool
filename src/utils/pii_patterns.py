"""Regex patterns for PII detection"""
import re

class PIIPatterns:
    """Collection of regex patterns for detecting various PII types"""
    
    # Email patterns
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone patterns (international and US formats)
    PHONE_PATTERNS = [
        r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple US
        r'\+\d{2}\s?\d{10}',  # India format +91 9876543210
    ]
    
    # SSN patterns
    SSN_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # XXX-XX-XXXX
        r'\b\d{3}\s\d{2}\s\d{4}\b',  # XXX XX XXXX
        r'\b\d{9}\b',  # XXXXXXXXX (with context validation)
    ]
    
    # Credit card patterns
    CREDIT_CARD_PATTERNS = [
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 16 digits with separators
        r'\b\d{15,16}\b',  # 15-16 consecutive digits
    ]
    
    # IP Address patterns
    IP_ADDRESS_PATTERNS = [
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IPv4
        r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',  # IPv6
    ]
    
    # Date of Birth patterns
    DOB_PATTERNS = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # YYYY/MM/DD
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
    ]
    
    # Address patterns (basic)
    ADDRESS_PATTERNS = [
        r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way)',
        r'P\.?O\.?\s+Box\s+\d+',  # PO Box
    ]
    
    # ZIP Code patterns
    ZIP_PATTERNS = [
        r'\b\d{5}(?:-\d{4})?\b',  # US ZIP
        r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b',  # Canadian postal code
        r'\b\d{6}\b',  # Indian PIN code (with context)
    ]
    
    @classmethod
    def compile_patterns(cls):
        """Compile all patterns for efficient matching"""
        return {
            "email": re.compile(cls.EMAIL, re.IGNORECASE),
            "phone": [re.compile(p) for p in cls.PHONE_PATTERNS],
            "ssn": [re.compile(p) for p in cls.SSN_PATTERNS],
            "credit_card": [re.compile(p) for p in cls.CREDIT_CARD_PATTERNS],
            "ip_address": [re.compile(p) for p in cls.IP_ADDRESS_PATTERNS],
            "dob": [re.compile(p, re.IGNORECASE) for p in cls.DOB_PATTERNS],
            "address": [re.compile(p, re.IGNORECASE) for p in cls.ADDRESS_PATTERNS],
            "zip": [re.compile(p) for p in cls.ZIP_PATTERNS],
        }
    
    @staticmethod
    def validate_credit_card(number: str) -> bool:
        """Validate credit card using Luhn algorithm"""
        number = re.sub(r'[-\s]', '', number)
        if not number.isdigit():
            return False
        
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        try:
            return luhn_checksum(number) == 0
        except:
            return False
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IPv4 address"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    @staticmethod
    def validate_ssn(ssn: str) -> bool:
        """Basic SSN validation (format only, not real validation)"""
        ssn = re.sub(r'[-\s]', '', ssn)
        if len(ssn) != 9 or not ssn.isdigit():
            return False
        # Basic validation: not all zeros, not sequential
        if ssn == '000000000' or ssn == '123456789':
            return False
        return True
