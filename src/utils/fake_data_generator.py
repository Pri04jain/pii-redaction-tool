"""Generate consistent fake data for PII replacement"""
from faker import Faker
import random
import hashlib
from typing import Dict, Any

class FakeDataGenerator:
    """Generate and maintain consistent fake data for PII replacement"""
    
    def __init__(self, seed: int = None):
        """Initialize generator with optional seed for reproducibility"""
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        
        # Cache for consistent replacements
        self.replacement_cache: Dict[str, str] = {}
        
    def _get_hash(self, original: str) -> int:
        """Generate consistent hash for original value"""
        return int(hashlib.md5(original.encode()).hexdigest(), 16)
    
    def _get_or_generate(self, original: str, generator_func, *args) -> str:
        """Get cached replacement or generate new one"""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        # Use hash of original for deterministic generation
        seed = self._get_hash(original)
        Faker.seed(seed)
        
        fake_value = generator_func(*args)
        self.replacement_cache[original] = fake_value
        
        return fake_value
    
    def generate_name(self, original: str) -> str:
        """Generate fake name"""
        return self._get_or_generate(original, self.faker.name)
    
    def generate_email(self, original: str) -> str:
        """Generate fake email"""
        return self._get_or_generate(original, self.faker.email)
    
    def generate_phone(self, original: str) -> str:
        """Generate fake phone number matching original format"""
        def _gen():
            # Try to match the format of the original
            if '+91' in original:
                return f'+91 {random.randint(7000000000, 9999999999)}'
            elif '+1' in original:
                return f'+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}'
            else:
                return self.faker.phone_number()
        
        return self._get_or_generate(original, _gen)
    
    def generate_ssn(self, original: str) -> str:
        """Generate fake SSN"""
        def _gen():
            return f'{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}'
        
        return self._get_or_generate(original, _gen)
    
    def generate_credit_card(self, original: str) -> str:
        """Generate fake credit card number"""
        def _gen():
            # Simple fake generation (not Luhn-valid for security)
            return f'{random.randint(4000, 4999)}-XXXX-XXXX-{random.randint(1000, 9999)}'
        
        return self._get_or_generate(original, _gen)
    
    def generate_ip_address(self, original: str) -> str:
        """Generate fake IP address"""
        return self._get_or_generate(original, self.faker.ipv4_private)
    
    def generate_address(self, original: str) -> str:
        """Generate fake address"""
        return self._get_or_generate(original, self.faker.address)
    
    def generate_company(self, original: str) -> str:
        """Generate fake company name"""
        return self._get_or_generate(original, self.faker.company)
    
    def generate_dob(self, original: str) -> str:
        """Generate fake date of birth"""
        def _gen():
            # Match format of original if possible
            date = self.faker.date_of_birth(minimum_age=18, maximum_age=90)
            if '/' in original:
                return date.strftime('%m/%d/%Y')
            elif '-' in original:
                return date.strftime('%Y-%m-%d')
            else:
                return date.strftime('%B %d, %Y')
        
        return self._get_or_generate(original, _gen)
    
    def get_replacement_mapping(self) -> Dict[str, str]:
        """Get all original -> fake mappings"""
        return self.replacement_cache.copy()
    
    def clear_cache(self):
        """Clear the replacement cache"""
        self.replacement_cache.clear()
