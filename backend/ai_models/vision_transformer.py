"""
Vision Transformer feature extractor
"""
import torch
import torch.nn as nn
from transformers import ViTModel, ViTImageProcessor
from typing import List, Tuple
import numpy as np
from ..app.config import settings

class VisionTransformerExtractor:
    """
    Vision Transformer (ViT) for deep feature extraction
    Uses pre-trained ViT model and fine-tunes for product authenticity
    """
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize Vision Transformer
        
        Args:
            model_name: HuggingFace model name
            device: Device to run model on (cuda/cpu)
        """
        self.model_name = model_name or settings.VIT_MODEL_NAME
        self.device = device or settings.DEVICE
        
        # Load pre-trained ViT model
        self.model = ViTModel.from_pretrained(self.model_name)
        self.processor = ViTImageProcessor.from_pretrained(self.model_name)
        
        # Move model to device
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Feature dimension
        self.feature_dim = settings.FEATURE_DIM
    
    def extract_features(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """
        Extract deep features from image using ViT
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Feature vector (embedding)
        """
        with torch.no_grad():
            # Ensure batch dimension
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            # Move to device
            image_tensor = image_tensor.to(self.device)
            
            # Extract features
            outputs = self.model(pixel_values=image_tensor)
            
            # Get CLS token embedding (global representation)
            features = outputs.last_hidden_state[:, 0, :]  # Shape: (batch, feature_dim)
            
            return features
    
    def extract_multi_scale_features(self, image_tensor: torch.Tensor) -> dict:
        """
        Extract features from multiple transformer layers
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Dictionary with features from different layers
        """
        with torch.no_grad():
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            
            # Get all hidden states
            outputs = self.model(
                pixel_values=image_tensor,
                output_hidden_states=True
            )
            
            hidden_states = outputs.hidden_states
            
            # Extract features from different layers
            features = {
                'early_layer': hidden_states[3][:, 0, :],   # Layer 3
                'mid_layer': hidden_states[6][:, 0, :],     # Layer 6
                'deep_layer': hidden_states[9][:, 0, :],    # Layer 9
                'final_layer': hidden_states[-1][:, 0, :]   # Last layer
            }
            
            return features
    
    def extract_patch_features(self, image_tensor: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract patch-level features (useful for localization)
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Tuple of (global_features, patch_features)
        """
        with torch.no_grad():
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            
            outputs = self.model(pixel_values=image_tensor)
            
            # Global features (CLS token)
            global_features = outputs.last_hidden_state[:, 0, :]
            
            # Patch features (all tokens except CLS)
            patch_features = outputs.last_hidden_state[:, 1:, :]
            
            return global_features, patch_features
    
    def compute_attention_maps(self, image_tensor: torch.Tensor) -> np.ndarray:
        """
        Extract attention maps for visualization
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Attention maps as numpy array
        """
        with torch.no_grad():
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            
            # Get attention weights
            outputs = self.model(
                pixel_values=image_tensor,
                output_attentions=True
            )
            
            # Average attention across all heads and layers
            attentions = outputs.attentions  # Tuple of attention tensors
            
            # Take last layer attention
            last_attention = attentions[-1]  # Shape: (batch, heads, seq_len, seq_len)
            
            # Average across heads
            avg_attention = last_attention.mean(dim=1)  # Shape: (batch, seq_len, seq_len)
            
            # Extract attention to CLS token
            cls_attention = avg_attention[0, 0, 1:]  # Attention from CLS to patches
            
            # Reshape to image grid (14x14 for standard ViT)
            grid_size = int(np.sqrt(cls_attention.shape[0]))
            attention_map = cls_attention.reshape(grid_size, grid_size)
            
            return attention_map.cpu().numpy()

class FeatureExtractor:
    """
    Main feature extraction pipeline
    Combines ViT features with traditional CV features
    """
    
    def __init__(self):
        self.vit_extractor = VisionTransformerExtractor()
    
    def extract_comprehensive_features(
        self,
        image_tensor: torch.Tensor,
        original_image: np.ndarray
    ) -> dict:
        """
        Extract comprehensive feature set for product analysis
        
        Args:
            image_tensor: Preprocessed image tensor
            original_image: Original image as numpy array
            
        Returns:
            Dictionary of all extracted features
        """
        from .preprocessing import preprocessor
        
        # Deep learning features
        vit_features = self.vit_extractor.extract_features(image_tensor)
        vit_features_np = vit_features.cpu().numpy().flatten()
        
        # Multi-scale features
        multiscale_features = self.vit_extractor.extract_multi_scale_features(image_tensor)
        
        # Color features
        color_features = preprocessor.extract_color_features(original_image)
        
        # Edge features
        edge_features = preprocessor.extract_edge_features(original_image)
        
        # Attention maps
        attention_map = self.vit_extractor.compute_attention_maps(image_tensor)
        
        return {
            'vit_features': vit_features_np.tolist(),
            'multiscale_features': {
                k: v.cpu().numpy().flatten().tolist()
                for k, v in multiscale_features.items()
            },
            'color_features': color_features,
            'edge_features': edge_features,
            'attention_map': attention_map.tolist()
        }

# Global feature extractor
feature_extractor = FeatureExtractor()
