"""
AI Models Package
Complete AI/ML pipeline for product authenticity detection
"""
from .preprocessing import preprocessor, ImagePreprocessor
from .vision_transformer import feature_extractor, FeatureExtractor, VisionTransformerExtractor
from .siamese_network import similarity_matcher, SimilarityMatcher, SiameseNetwork
from .autoencoder import anomaly_detector, AnomalyDetector, Autoencoder
from .ocr_validator import text_extractor, brand_validator, TextExtractor, BrandValidator
from .gradcam import explainer, ProductAuthenticityExplainer, GradCAM
from .decision_engine import decision_engine, DecisionEngine

__all__ = [
    'preprocessor',
    'feature_extractor',
    'similarity_matcher',
    'anomaly_detector',
    'text_extractor',
    'brand_validator',
    'explainer',
    'decision_engine',
    'ImagePreprocessor',
    'FeatureExtractor',
    'VisionTransformerExtractor',
    'SiameseNetwork',
    'SimilarityMatcher',
    'Autoencoder',
    'AnomalyDetector',
    'TextExtractor',
    'BrandValidator',
    'GradCAM',
    'ProductAuthenticityExplainer',
    'DecisionEngine'
]
