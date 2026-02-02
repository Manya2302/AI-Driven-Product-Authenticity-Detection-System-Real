"""
Decision Engine - Combines all AI models to make final authenticity decision
"""
import numpy as np
from typing import Dict, Tuple, Optional
import torch
from datetime import datetime
from ..app.config import settings
from .preprocessing import preprocessor
from .vision_transformer import feature_extractor
from .siamese_network import similarity_matcher
from .autoencoder import anomaly_detector
from .ocr_validator import brand_validator
from .gradcam import explainer

class DecisionEngine:
    """
    Main decision engine combining all AI/ML models
    Makes final authenticity determination with explainability
    
    PHASE ARCHITECTURE:
    - PHASE 1: Admin Bootstraps Reality (stores reference feature profiles)
    - PHASE 2: User Scans Product (provides intent context)
    - PHASE 3: Hybrid Decision Logic (3 brains: reference comparison, text/name, generic AI)
    - PHASE 4: Deception Logic (detects look-alikes that fool visual matching)
    - PHASE 5: Final Scoring Engine (weighted combination)
    - PHASE 6: Final Decision (with explanations)
    - PHASE 7: Location Intelligence (for fake products)
    """
    
    def __init__(self):
        """Initialize decision engine with all AI components"""
        self.preprocessor = preprocessor
        self.feature_extractor = feature_extractor
        self.similarity_matcher = similarity_matcher
        self.anomaly_detector = anomaly_detector
        self.brand_validator = brand_validator
        self.explainer = explainer
        
        # Decision weights from config
        self.weights = {
            'visual_similarity': settings.VISUAL_SIMILARITY_WEIGHT,      # 40%
            'text_validation': settings.TEXT_VALIDATION_WEIGHT,          # 30%
            'anomaly': settings.ANOMALY_WEIGHT,                          # 20%
            'pattern_consistency': settings.PATTERN_CONSISTENCY_WEIGHT   # 10%
        }
        
        # Deception detection weights
        self.deception_weights = {
            'visual_high_similarity': 0.4,
            'name_lookalike': 0.3,
            'text_exact_mismatch': 0.2,
            'phonetic_similarity': 0.1
        }
        
        # Classification thresholds
        self.real_threshold = settings.REAL_THRESHOLD
        self.suspicious_threshold = settings.SUSPICIOUS_THRESHOLD
        
        # Deception thresholds
        self.deception_threshold = 0.65  # High deception probability
        self.lookalike_visual_threshold = 0.85  # Visual similarity above this
        self.lookalike_text_threshold = 0.70  # Fuzzy text match above this
    
    def analyze_product(
        self,
        image_path: str,
        reference_profile: Dict,
        product_info: Dict,
        user_intent: Optional[str] = None
    ) -> Dict:
        """
        Complete product authenticity analysis pipeline with deception detection
        
        PHASE 2: User provides intent context (selected product name)
        PHASE 3: Hybrid decision logic with 3 brains
        PHASE 4: Deception logic prevents false positives
        
        Args:
            image_path: Path to user-uploaded product image
            reference_profile: Reference feature profile from admin
            product_info: Product metadata (name, brand, category)
            user_intent: User's selected product name (intent context)
            
        Returns:
            Complete analysis results with scores and explanations
        """
        start_time = datetime.utcnow()
        
        # Step 1: Image Preprocessing
        image_tensor, original_image = self.preprocessor.preprocess_for_inference(image_path)
        
        # Step 2: Feature Extraction
        query_features = self.feature_extractor.extract_comprehensive_features(
            image_tensor,
            original_image
        )
        
        # Step 3: BRAIN 1 - Visual Similarity Analysis (if reference exists)
        visual_similarity_results = self._analyze_visual_similarity(
            query_features,
            reference_profile
        )
        
        # Step 4: BRAIN 2 - OCR and Text Validation (Critical for deception)
        text_validation_results = self._analyze_text_validation(
            image_path,
            product_info.get('brand_name', '')
        )
        
        # Step 5: BRAIN 3 - Generic Authenticity AI (works without reference)
        generic_authenticity_results = self._analyze_generic_authenticity(
            image_tensor,
            query_features
        )
        
        # Step 6: Anomaly Detection
        anomaly_results = self._analyze_anomalies(image_tensor)
        
        # Step 7: Pattern Consistency Check
        pattern_results = self._analyze_pattern_consistency(
            query_features,
            reference_profile
        )
        
        # Step 8: PHASE 4 - Deception Detection Logic
        deception_results = self._detect_deception(
            visual_similarity_results,
            text_validation_results,
            product_info,
            user_intent
        )
        
        # Step 9: Compute Weighted Score
        final_score, component_scores = self._compute_final_score(
            visual_similarity_results,
            text_validation_results,
            anomaly_results,
            pattern_results,
            deception_results
        )
        
        # Step 10: Classification (with deception override)
        classification = self._classify(final_score, deception_results)
        
        # Step 11: Generate Explanations
        explanations = self._generate_explanations(
            classification,
            final_score,
            component_scores,
            visual_similarity_results,
            text_validation_results,
            anomaly_results,
            deception_results,
            generic_authenticity_results
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Compile results
        results = {
            'classification': classification,
            'confidence_score': float(final_score),
            'visual_similarity_score': float(component_scores['visual_similarity']),
            'text_validation_score': float(component_scores['text_validation']),
            'anomaly_score': float(1.0 - component_scores['anomaly']),
            'pattern_consistency_score': float(component_scores['pattern_consistency']),
            'generic_authenticity_score': float(generic_authenticity_results.get('score', 0.5)),
            'deception_probability': float(deception_results.get('deception_probability', 0.0)),
            'is_likely_lookalike': deception_results.get('is_deceptive_lookalike', False),
            'explanations': explanations['explanations'],
            'verdict': explanations['verdict'],
            'recommendations': explanations['recommendations'],
            'suspicious_regions': anomaly_results.get('regions', []),
            'text_issues': text_validation_results.get('issues', []),
            'extracted_text': text_validation_results.get('extracted_texts', []),
            'processing_time_seconds': processing_time,
            'requires_location_sharing': classification == 'likely_fake' and deception_results.get('is_deceptive_lookalike', False)
        }
        
        return results
    
    def _analyze_visual_similarity(
        self,
        query_features: Dict,
        reference_profile: Dict
    ) -> Dict:
        """Analyze visual similarity using Siamese Network"""
        
        # Get reference features for all angles
        reference_features_dict = reference_profile.get('visual_features', {})
        
        if not reference_features_dict:
            return {'overall_similarity': 0.0, 'details': 'No reference features available'}
        
        # Compute multi-angle similarity
        similarity_results = self.similarity_matcher.compute_multi_angle_similarity(
            query_features,
            reference_features_dict
        )
        
        return similarity_results
    
    def _analyze_text_validation(
        self,
        image_path: str,
        reference_brand: str
    ) -> Dict:
        """Analyze text using OCR and brand validation"""
        
        validation_results = self.brand_validator.validate_brand_text(
            image_path,
            reference_brand
        )
        
        return validation_results
    
    def _analyze_anomalies(
        self,
        image_tensor: torch.Tensor
    ) -> Dict:
        """Detect anomalies using Autoencoder"""
        
        anomaly_results = self.anomaly_detector.detect_anomaly(image_tensor)
        
        # Detect localized anomalies
        anomalous_regions = self.anomaly_detector.detect_localized_anomalies(image_tensor)
        
        anomaly_results['regions'] = anomalous_regions
        
        return anomaly_results
    
    def _analyze_pattern_consistency(
        self,
        query_features: Dict,
        reference_profile: Dict
    ) -> Dict:
        """Analyze pattern consistency across different feature types"""
        
        consistency_scores = []
        
        # Color consistency
        if 'color_features' in query_features and 'color_features' in reference_profile:
            color_sim = self._compute_color_similarity(
                query_features['color_features'],
                reference_profile.get('color_features', {})
            )
            consistency_scores.append(color_sim)
        
        # Edge pattern consistency
        if 'edge_features' in query_features and 'edge_features' in reference_profile:
            edge_sim = self._compute_edge_similarity(
                query_features['edge_features'],
                reference_profile.get('edge_features', {})
            )
            consistency_scores.append(edge_sim)
        
        # Overall consistency
        overall_consistency = np.mean(consistency_scores) if consistency_scores else 0.5
        
        return {
            'overall_consistency': float(overall_consistency),
            'component_consistencies': consistency_scores
        }
    
    def _compute_color_similarity(self, query_colors: Dict, reference_colors: Dict) -> float:
        """Compute color histogram similarity"""
        if 'color_histogram' not in query_colors or 'color_histogram' not in reference_colors:
            return 0.5
        
        query_hist = np.array(query_colors['color_histogram'])
        ref_hist = np.array(reference_colors['color_histogram'])
        
        # Compute histogram intersection
        intersection = np.minimum(query_hist, ref_hist).sum()
        
        return float(intersection)
    
    def _compute_edge_similarity(self, query_edges: Dict, reference_edges: Dict) -> float:
        """Compute edge pattern similarity"""
        if 'hog_features' not in query_edges or 'hog_features' not in reference_edges:
            return 0.5
        
        query_hog = np.array(query_edges['hog_features'])
        ref_hog = np.array(reference_edges['hog_features'])
        
        # Cosine similarity
        dot_product = np.dot(query_hog, ref_hog)
        norm_product = np.linalg.norm(query_hog) * np.linalg.norm(ref_hog)
        
        if norm_product == 0:
            return 0.5
        
        similarity = dot_product / norm_product
        
        # Convert to [0, 1]
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    def _analyze_generic_authenticity(
        self,
        image_tensor: torch.Tensor,
        query_features: Dict
    ) -> Dict:
        """
        BRAIN 3: Generic Authenticity AI
        
        Analyzes print quality, texture consistency, and manufacturing patterns
        Works WITHOUT reference product - detects well-made counterfeits
        
        Returns:
            Authenticity assessment (NOT genuineness, but manufacturing quality)
        """
        
        # Analyze print quality through texture features
        print_quality_score = 0.5
        if 'texture_features' in query_features:
            texture = query_features['texture_features']
            # Check for consistent texture patterns (real products)
            if 'print_consistency' in texture:
                print_quality_score = texture.get('print_consistency', 0.5)
        
        # Analyze industrial manufacturing patterns
        manufacturing_score = 0.5
        if 'edge_features' in query_features:
            edges = query_features['edge_features']
            # Check for realistic edge patterns
            if 'edge_sharpness' in edges:
                manufacturing_score = edges.get('edge_sharpness', 0.5)
        
        # Anomaly score from autoencoder (low anomaly = well-made)
        anomaly_score = self.anomaly_detector.detect_anomaly(image_tensor)
        manufacturing_quality = 1.0 - anomaly_score.get('anomaly_score', 0.5)
        
        # Overall generic authenticity score
        generic_score = (print_quality_score * 0.4 + manufacturing_score * 0.3 + manufacturing_quality * 0.3)
        
        return {
            'score': float(generic_score),
            'print_quality': float(print_quality_score),
            'manufacturing_patterns': float(manufacturing_score),
            'manufacturing_quality': float(manufacturing_quality),
            'note': 'High score means well-made (but not necessarily genuine)'
        }
    
    def _detect_deception(
        self,
        visual_results: Dict,
        text_results: Dict,
        product_info: Dict,
        user_intent: Optional[str] = None
    ) -> Dict:
        """
        PHASE 4: Deception Detection Logic
        
        Critical rule to prevent false positives from look-alikes:
        
        IF visual_similarity is HIGH
        AND name_similarity is HIGH  
        AND exact_text_match is FALSE
        AND user_intent_mismatch is TRUE
        THEN → DECEPTIVE LOOK-ALIKE
        
        Example: "Bisleri" vs "Belsiri"
        - Looks 95% similar visually ✓
        - Sounds similar (phonetic) ✓
        - Text doesn't match exactly (looks like typo) ✓
        - User intended "Bisleri" but image says "Belsiri" ✓
        → AI concludes: DECEPTIVE LOOK-ALIKE (fake with intentional imitation)
        
        Args:
            visual_results: Visual similarity analysis
            text_results: Text validation results
            product_info: Product metadata (brand name, etc.)
            user_intent: User's selected product name (intent context)
            
        Returns:
            Deception assessment with probability and reasoning
        """
        
        visual_similarity = visual_results.get('overall_similarity', 0.0)
        text_validation = text_results.get('best_match', {})
        lookalike_detection = text_validation.get('lookalike_result', {})
        
        # Component 1: Visual Similarity is HIGH
        visual_is_high = visual_similarity >= self.lookalike_visual_threshold
        visual_score = min(visual_similarity / self.lookalike_visual_threshold, 1.0)
        
        # Component 2: Text Name is Similar BUT NOT Exact
        exact_match = lookalike_detection.get('is_exact_match', False)
        fuzzy_similarity = lookalike_detection.get('fuzzy_similarity', 0.0)
        name_is_similar = fuzzy_similarity >= self.lookalike_text_threshold and not exact_match
        name_score = 0.0
        
        if name_is_similar:
            name_score = min(fuzzy_similarity / self.lookalike_text_threshold, 1.0)
        
        # Component 3: Phonetic Similarity (high deception indicator)
        phonetically_similar = lookalike_detection.get('phonetically_similar', False)
        phonetic_score = 1.0 if phonetically_similar else 0.0
        
        # Component 4: Suspicious Character Substitution (classic fake tactic)
        has_substitution = lookalike_detection.get('suspicious_substitution', False)
        substitution_score = 1.0 if has_substitution else 0.0
        
        # Component 5: User Intent Mismatch (user selected one brand, image shows different)
        user_intent_mismatch = False
        if user_intent and not exact_match:
            # User intended brand doesn't match extracted text
            intended_norm = self.brand_validator.normalize_text(user_intent)
            extracted_norm = self.brand_validator.normalize_text(
                text_validation.get('text', '')
            )
            user_intent_mismatch = intended_norm != extracted_norm
        
        intent_score = 1.0 if user_intent_mismatch else 0.0
        
        # DECEPTION SCORING
        # Deceptive pattern: High visual + Name lookalike + Exact mismatch + Intent mismatch
        deception_score = (
            visual_score * self.deception_weights['visual_high_similarity'] +
            name_score * self.deception_weights['name_lookalike'] +
            substitution_score * self.deception_weights['text_exact_mismatch'] +
            phonetic_score * self.deception_weights['phonetic_similarity']
        )
        
        is_deceptive_lookalike = (
            deception_score >= self.deception_threshold and
            visual_is_high and
            name_is_similar and
            not exact_match and
            user_intent_mismatch
        )
        
        return {
            'deception_probability': float(deception_score),
            'is_deceptive_lookalike': is_deceptive_lookalike,
            'components': {
                'visual_similarity_high': visual_is_high,
                'visual_score': float(visual_score),
                'name_lookalike': name_is_similar,
                'name_score': float(name_score),
                'phonetically_similar': phonetically_similar,
                'suspicious_substitution': has_substitution,
                'user_intent_mismatch': user_intent_mismatch,
            },
            'reasoning': [
                f"Visual similarity: {visual_similarity:.1%}" if visual_is_high else None,
                f"Brand name is similar but not exact: '{text_validation.get('text', 'N/A')}' vs '{product_info.get('brand_name', 'N/A')}'" if name_is_similar else None,
                f"Phonetic similarity suggests sound-alike tactic" if phonetically_similar else None,
                f"Character substitution detected (classic counterfeit strategy)" if has_substitution else None,
                f"User selected '{user_intent}' but image shows '{text_validation.get('text', 'N/A')}'" if user_intent_mismatch else None,
            ]
        }
    
    def _compute_final_score(
        self,
        visual_results: Dict,
        text_results: Dict,
        anomaly_results: Dict,
        pattern_results: Dict,
        deception_results: Dict = None
    ) -> Tuple[float, Dict]:
        """
        PHASE 5: Final Scoring Engine
        
        Computes weighted final authenticity score
        Incorporates deception detection to avoid false positives
        
        Args:
            visual_results: Visual similarity analysis
            text_results: Text validation results
            anomaly_results: Anomaly detection results
            pattern_results: Pattern consistency results
            deception_results: Deception detection results
            
        Returns:
            Final score and component breakdown
        """
        
        # Extract individual scores
        visual_score = visual_results.get('overall_similarity', 0.0)
        text_score = text_results.get('validation_score', 0.0)
        
        # Anomaly score (inverted - low anomaly = high authenticity)
        anomaly_score = 1.0 - anomaly_results.get('anomaly_score', 0.5)
        
        pattern_score = pattern_results.get('overall_consistency', 0.5)
        
        # Component scores
        component_scores = {
            'visual_similarity': visual_score,
            'text_validation': text_score,
            'anomaly': anomaly_score,
            'pattern_consistency': pattern_score
        }
        
        # DECEPTION OVERRIDE: If detected deceptive lookalike, penalize visual score
        if deception_results and deception_results.get('is_deceptive_lookalike', False):
            # Visual similarity alone shouldn't indicate authenticity for lookalikes
            # Reduce visual score significantly
            visual_score = max(0.0, visual_score - 0.5)
            component_scores['visual_similarity'] = visual_score
        
        # Weighted combination
        final_score = (
            self.weights['visual_similarity'] * visual_score +
            self.weights['text_validation'] * text_score +
            self.weights['anomaly'] * anomaly_score +
            self.weights['pattern_consistency'] * pattern_score
        )
        
        return final_score, component_scores
    
    def _classify(self, score: float, deception_results: Dict = None) -> str:
        """
        Classify product based on final score
        Deception results override visual-only false positives
        
        Args:
            score: Final authenticity score
            deception_results: Deception detection results
            
        Returns:
            Classification: 'likely_real', 'suspicious', or 'likely_fake'
        """
        # Deception override: Lookalike detected = likely fake, regardless of visual
        if deception_results and deception_results.get('is_deceptive_lookalike', False):
            return 'likely_fake'
        
        # Standard classification
        if score >= self.real_threshold:
            return 'likely_real'
        elif score >= self.suspicious_threshold:
            return 'suspicious'
        else:
            return 'likely_fake'
    
    def _generate_explanations(
        self,
        classification: str,
        final_score: float,
        component_scores: Dict,
        visual_results: Dict,
        text_results: Dict,
        anomaly_results: Dict,
        deception_results: Dict = None,
        generic_authenticity_results: Dict = None
    ) -> Dict:
        """
        Generate human-readable explanations with deception insights
        
        Explains WHY AI made the decision, not just WHAT
        Highlights deceptive tactics if lookalike detected
        """
        
        analysis_results = {
            'classification': classification,
            'confidence_score': final_score,
            'visual_similarity_score': component_scores['visual_similarity'],
            'text_validation_score': component_scores['text_validation'],
            'anomaly_score': 1.0 - component_scores['anomaly'],
            'text_issues': text_results.get('issues', []),
            'is_deceptive_lookalike': deception_results.get('is_deceptive_lookalike', False) if deception_results else False,
            'deception_probability': deception_results.get('deception_probability', 0.0) if deception_results else 0.0,
            'generic_authenticity_score': generic_authenticity_results.get('score', 0.5) if generic_authenticity_results else 0.5
        }
        
        explanations = self.explainer.generate_textual_explanation(analysis_results)
        
        # Add deception-specific insights if lookalike detected
        if deception_results and deception_results.get('is_deceptive_lookalike', False):
            deception_insight = {
                'deception_detected': True,
                'reasoning': [r for r in deception_results.get('reasoning', []) if r is not None],
                'tactic': 'Visual imitation with intentional brand name variation',
                'confidence': deception_results.get('deception_probability', 0.0)
            }
            
            if 'explanations' in explanations:
                explanations['explanations'].insert(0, f"DECEPTION DETECTED: This product visually imitates the real brand but the name doesn't match. This is a classic counterfeit tactic.")
            
            explanations['deception_insight'] = deception_insight
        
        return explanations

# Global decision engine instance
decision_engine = DecisionEngine()
