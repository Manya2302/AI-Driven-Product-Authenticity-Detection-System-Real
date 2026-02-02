"""
OCR and text validation for brand authenticity
"""
import easyocr
import numpy as np
from typing import List, Dict, Tuple
import re
from Levenshtein import distance as levenshtein_distance
from fuzzywuzzy import fuzz
import phonetics
from ..app.config import settings

class TextExtractor:
    """
    OCR-based text extraction from product images
    """
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize text extractor
        
        Args:
            languages: List of language codes for OCR
        """
        self.languages = languages or settings.OCR_LANGUAGES
        
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(
            self.languages,
            gpu=settings.OCR_GPU
        )
    
    def extract_text(self, image_path: str) -> List[Dict]:
        """
        Extract text from image
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected text regions with bounding boxes
        """
        # Read image and detect text
        result = self.reader.readtext(image_path)
        
        # Format results
        extracted = []
        for bbox, text, confidence in result:
            extracted.append({
                'text': text,
                'confidence': float(confidence),
                'bbox': [[int(x), int(y)] for x, y in bbox]
            })
        
        return extracted
    
    def extract_text_from_array(self, image_array: np.ndarray) -> List[Dict]:
        """
        Extract text from numpy array image
        
        Args:
            image_array: Image as numpy array
            
        Returns:
            List of detected text regions
        """
        result = self.reader.readtext(image_array)
        
        extracted = []
        for bbox, text, confidence in result:
            extracted.append({
                'text': text,
                'confidence': float(confidence),
                'bbox': [[int(x), int(y)] for x, y in bbox]
            })
        
        return extracted
    
    def get_all_text(self, image_path: str) -> str:
        """
        Get all extracted text as single string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Concatenated text
        """
        results = self.extract_text(image_path)
        all_text = " ".join([item['text'] for item in results])
        return all_text

class BrandValidator:
    """
    Validate brand names and detect look-alikes
    """
    
    def __init__(self):
        self.text_extractor = TextExtractor()
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def compute_edit_distance(self, text1: str, text2: str) -> int:
        """
        Compute Levenshtein edit distance
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Edit distance
        """
        return levenshtein_distance(
            self.normalize_text(text1),
            self.normalize_text(text2)
        )
    
    def compute_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """
        Compute fuzzy string similarity
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-100)
        """
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        # Use multiple fuzzy matching methods
        ratio = fuzz.ratio(text1_norm, text2_norm)
        partial_ratio = fuzz.partial_ratio(text1_norm, text2_norm)
        token_sort_ratio = fuzz.token_sort_ratio(text1_norm, text2_norm)
        
        # Weighted average
        similarity = (ratio * 0.4 + partial_ratio * 0.3 + token_sort_ratio * 0.3)
        
        return similarity / 100.0  # Convert to 0-1 scale
    
    def compute_phonetic_similarity(self, text1: str, text2: str) -> bool:
        """
        Check if two texts sound similar (phonetic matching)
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            True if phonetically similar
        """
        try:
            # Soundex algorithm
            soundex1 = phonetics.soundex(self.normalize_text(text1))
            soundex2 = phonetics.soundex(self.normalize_text(text2))
            
            return soundex1 == soundex2
        except:
            return False
    
    def detect_lookalike(
        self,
        extracted_text: str,
        reference_brand: str
    ) -> Dict:
        """
        Detect if extracted text is a look-alike of reference brand
        
        Args:
            extracted_text: Text extracted from user image
            reference_brand: Reference brand name
            
        Returns:
            Dictionary with lookalike detection results
        """
        # Normalize both texts
        extracted_norm = self.normalize_text(extracted_text)
        reference_norm = self.normalize_text(reference_brand)
        
        # Exact match
        is_exact_match = extracted_norm == reference_norm
        
        # Fuzzy similarity
        fuzzy_score = self.compute_fuzzy_similarity(extracted_text, reference_brand)
        
        # Edit distance
        edit_dist = self.compute_edit_distance(extracted_text, reference_brand)
        max_len = max(len(reference_norm), len(extracted_norm))
        edit_similarity = 1.0 - (edit_dist / max_len) if max_len > 0 else 0.0
        
        # Phonetic similarity
        is_phonetically_similar = self.compute_phonetic_similarity(extracted_text, reference_brand)
        
        # Character substitution detection (common fake tactics)
        # E.g., "BISLERI" vs "BISLER1" (I -> 1)
        has_suspicious_substitution = self._detect_character_substitution(
            extracted_norm, reference_norm
        )
        
        # Overall lookalike assessment
        is_lookalike = (
            not is_exact_match and
            (fuzzy_score > 0.7 or is_phonetically_similar or has_suspicious_substitution) and
            edit_dist <= 3
        )
        
        return {
            'is_exact_match': is_exact_match,
            'is_lookalike': is_lookalike,
            'fuzzy_similarity': float(fuzzy_score),
            'edit_distance': int(edit_dist),
            'edit_similarity': float(edit_similarity),
            'phonetically_similar': is_phonetically_similar,
            'suspicious_substitution': has_suspicious_substitution,
            'confidence': float(fuzzy_score) if not is_exact_match else 1.0
        }
    
    def _detect_character_substitution(self, text1: str, text2: str) -> bool:
        """
        Detect common character substitutions (e.g., o->0, i->1, l->1)
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            True if suspicious substitution detected
        """
        substitution_map = {
            'o': '0', '0': 'o',
            'i': '1', '1': 'i', 'l': '1',
            's': '5', '5': 's',
            'e': '3', '3': 'e',
            'a': '4', '4': 'a',
            'b': '8', '8': 'b',
            'g': '9', '9': 'g'
        }
        
        if len(text1) != len(text2):
            return False
        
        substitutions = 0
        for c1, c2 in zip(text1, text2):
            if c1 != c2:
                if substitution_map.get(c1) == c2 or substitution_map.get(c2) == c1:
                    substitutions += 1
        
        return substitutions > 0
    
    def check_spelling_grammar(self, text: str) -> Dict:
        """
        Check for spelling and grammar issues (common in fake products)
        
        Args:
            text: Extracted text
            
        Returns:
            Dictionary with spelling/grammar issues
        """
        issues = []
        
        # Check for common misspellings patterns
        # Multiple consecutive same letters
        if re.search(r'(.)\1{3,}', text):
            issues.append("Suspicious repeated characters")
        
        # Random capitalization
        if text != text.upper() and text != text.lower() and text != text.title():
            caps_count = sum(1 for c in text if c.isupper())
            if caps_count > 0 and caps_count < len(text) * 0.8:
                issues.append("Inconsistent capitalization")
        
        # Numbers in unexpected places
        if re.search(r'[a-zA-Z]+\d+[a-zA-Z]+', text):
            issues.append("Numbers mixed with letters suspiciously")
        
        # Excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / (len(text) + 1)
        if special_char_ratio > 0.3:
            issues.append("Excessive special characters")
        
        return {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'issue_count': len(issues)
        }
    
    def validate_brand_text(
        self,
        image_path: str,
        reference_brand: str
    ) -> Dict:
        """
        Complete brand text validation pipeline
        
        Args:
            image_path: Path to image file
            reference_brand: Reference brand name
            
        Returns:
            Complete validation results
        """
        # Extract text
        extracted_texts = self.text_extractor.extract_text(image_path)
        
        if not extracted_texts:
            return {
                'text_found': False,
                'validation_score': 0.0,
                'issues': ['No text detected in image']
            }
        
        # Find best matching text
        best_match = None
        best_similarity = 0.0
        
        all_issues = []
        
        for item in extracted_texts:
            text = item['text']
            
            # Check for lookalike
            lookalike_result = self.detect_lookalike(text, reference_brand)
            
            if lookalike_result['fuzzy_similarity'] > best_similarity:
                best_similarity = lookalike_result['fuzzy_similarity']
                best_match = {
                    'text': text,
                    'confidence': item['confidence'],
                    'lookalike_result': lookalike_result
                }
            
            # Check spelling/grammar
            spelling_result = self.check_spelling_grammar(text)
            if spelling_result['has_issues']:
                all_issues.extend(spelling_result['issues'])
        
        # Compute overall validation score
        if best_match:
            validation_score = (
                best_match['lookalike_result']['fuzzy_similarity'] * 0.7 +
                best_match['confidence'] * 0.3
            )
        else:
            validation_score = 0.0
        
        return {
            'text_found': True,
            'extracted_texts': [item['text'] for item in extracted_texts],
            'best_match': best_match,
            'validation_score': float(validation_score),
            'issues': list(set(all_issues)),
            'total_texts_found': len(extracted_texts)
        }

# Global instances
text_extractor = TextExtractor()
brand_validator = BrandValidator()
