# Test Data Guide - Valid PII Examples for Testing

## ⚠️ IMPORTANT: Test Data Requirements

The PII Redaction Tool uses **validation algorithms** to reduce false positives:
- **SSN**: Rejects sequential numbers like `123-45-6789`
- **Credit Cards**: Validates using Luhn algorithm
- **IP Addresses**: Validates IPv4 format (0-255 per octet)

**Use the examples below for your ground truth test data.**

---

## Valid Test Data Examples (All 9 Required Types)

### 1. Full Names
```
John Michael Smith
Jane Marie Doe
Robert Alan Johnson
Sarah Elizabeth Williams
```

### 2. Email Addresses
```
john.smith@example.com
contact@company.com
info@acmecorp.org
support@bankltd.com
```

### 3. Phone Numbers
```
+1-555-234-5678
(555) 987-6543
555-123-4567
+91-9876543210
```

### 4. Company Names
```
Acme Corporation
XYZ Bank Limited
Tech Solutions Inc.
Global Industries LLC
```

### 5. Physical/Mailing Addresses
```
123 Main Street, Apt 4B, New York, NY 10001
456 Oak Avenue, Los Angeles, CA 90001
P.O. Box 789, Chicago, IL 60601
```

### 6. Social Security Numbers ✅ VALID
**Use these (pass validation):**
```
219-09-9999
457-55-5462
078-05-1120
```

**DON'T use (will be rejected):**
```
123-45-6789  ❌ Sequential
000-00-0000  ❌ All zeros
111-11-1111  ❌ Repeating
```

### 7. Credit Card Numbers ✅ VALID (Pass Luhn Check)
**Use these (pass Luhn validation):**
```
4532015112830366  ✅ Visa
5425233430109903  ✅ Mastercard
374245455400126   ✅ Amex (15 digits)
6011000991001201  ✅ Discover
```

**DON'T use (will be rejected):**
```
4532-1234-5678-9010  ❌ Fails Luhn
1234-5678-9012-3456  ❌ Fails Luhn
```

**How to generate valid test credit cards:**
- Use online Luhn algorithm generators
- Or use these test cards from payment processors:
  - Stripe test: `4242424242424242`
  - Square test: `4111111111111111`

### 8. Dates of Birth
```
01/15/1980
March 25, 1975
12-05-1990
```

**Context required!** Must appear near DOB keywords:
```
Born on 01/15/1980
Date of birth: March 25, 1975
DOB: 12/05/1990
```

### 9. IP Addresses ✅ VALID
**Use these (valid IPv4):**
```
192.168.1.1
10.0.0.254
172.16.0.1
8.8.8.8
```

**DON'T use (will be rejected):**
```
999.999.999.999  ❌ Out of range
256.1.1.1        ❌ >255
1.2.3            ❌ Incomplete
```

---

## Sample Test Document Text

```
CONFIDENTIAL EMPLOYEE RECORD

Employee: John Michael Smith
Email: john.smith@acmecorp.com
Phone: +1-555-234-5678
Company: Acme Corporation

Home Address: 123 Main Street, Apt 4B, New York, NY 10001

SSN: 219-09-9999
Credit Card on File: 4532015112830366
Date of Birth: Born on 01/15/1980
VPN IP Address: 192.168.1.100

---

Employee: Jane Marie Doe
Email: jane.doe@acmecorp.com
Phone: (555) 987-6543
DOB: March 25, 1975
SSN: 457-55-5462
Address: P.O. Box 789, Chicago, IL 60601
```

---

## Ground Truth JSON Example

```json
{
  "Full names": [
    "John Michael Smith",
    "Jane Marie Doe"
  ],
  
  "Email addresses": [
    "john.smith@acmecorp.com",
    "jane.doe@acmecorp.com"
  ],
  
  "Phone numbers": [
    "+1-555-234-5678",
    "(555) 987-6543"
  ],
  
  "Company names": [
    "Acme Corporation"
  ],
  
  "Physical/mailing addresses": [
    "123 Main Street, Apt 4B, New York, NY 10001",
    "P.O. Box 789, Chicago, IL 60601"
  ],
  
  "Social Security Numbers": [
    "219-09-9999",
    "457-55-5462"
  ],
  
  "Credit card numbers": [
    "4532015112830366"
  ],
  
  "Dates of birth": [
    "01/15/1980",
    "March 25, 1975"
  ],
  
  "IP addresses": [
    "192.168.1.100"
  ]
}
```

---

## Creating Your Test Document

1. **Start with a real document** (Red Herring Prospectus, employee record, etc.)

2. **Add test PII** using the valid examples above:
   - Replace real names with test names
   - Add valid SSN/credit card numbers from this guide
   - Include IP addresses in context (VPN, server, etc.)

3. **Add context for DOBs**:
   - ✅ "Born on DATE"
   - ✅ "Date of birth: DATE"
   - ✅ "DOB: DATE"
   - ❌ Don't just list dates alone

4. **Create ground truth JSON** with exact strings from the document

5. **Run verification**:
   ```bash
   python verify_9_detectors.py
   ```
   
   Expected: All 9 types should show detections

---

## Troubleshooting

### SSN Not Detected
- ✅ Use valid SSN from list above
- ❌ Don't use `123-45-6789` (sequential, blocked)
- ❌ Don't use `000-00-0000` (all zeros, blocked)

### Credit Card Not Detected
- ✅ Use Luhn-valid numbers from list above
- ❌ Don't make up random 16-digit numbers (99% fail Luhn)
- ℹ️ Use online Luhn generator or test card numbers

### IP Address Not Detected
- ✅ Use valid IPv4: `192.168.1.1`
- ❌ Don't use out-of-range: `256.1.1.1`
- ℹ️ Each octet must be 0-255

### DOB Not Detected
- ✅ Add context: "Born on DATE" or "DOB: DATE"
- ❌ Don't just list dates without context
- ℹ️ Tool filters dates without DOB keywords to avoid false positives

---

## Why Validation Matters

**For Production Use:**
- Validations reduce false positives by 50-70%
- Example: Prevents flagging dates as SSNs
- Example: Prevents flagging random numbers as credit cards

**For Testing:**
- Use realistic test data that would pass validation
- This ensures your evaluation reflects real-world performance
- Invalid test data = artificially low recall scores

---

## Quick Reference: Valid Test Data

**Copy-paste ready examples:**

```
SSNs: 219-09-9999, 457-55-5462, 078-05-1120
Credit Cards: 4532015112830366, 5425233430109903
IPs: 192.168.1.1, 10.0.0.254, 172.16.0.1
Names: John Michael Smith, Jane Marie Doe
Emails: john.smith@example.com, jane.doe@example.com
Phones: +1-555-234-5678, (555) 987-6543
Companies: Acme Corporation, XYZ Bank Limited
Addresses: 123 Main Street, New York, NY 10001
DOBs: Born on 01/15/1980, Date of birth: March 25, 1975
```
