"""
Siamese Network for image similarity comparison
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
import numpy as np
from ..app.config import settings

class SiameseNetwork(nn.Module):
    """
    Siamese Network for learning similarity between product images
    Compares user-uploaded image with reference product profile
    """
    
    def __init__(
        self,
        input_dim: int = 768,
        embedding_dim: int = 512,
        hidden_dims: list = [1024, 512]
    ):
        """
        Initialize Siamese Network
        
        Args:
            input_dim: Input feature dimension (from ViT)
            embedding_dim: Output embedding dimension
            hidden_dims: Hidden layer dimensions
        """
        super(SiameseNetwork, self).__init__()
        
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        
        # Build embedding network
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        # Final embedding layer
        layers.append(nn.Linear(prev_dim, embedding_dim))
        
        self.embedding_network = nn.Sequential(*layers)
        
        # L2 normalization
        self.l2_norm = nn.functional.normalize
    
    def forward_once(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through one branch
        
        Args:
            x: Input features
            
        Returns:
            Normalized embedding
        """
        embedding = self.embedding_network(x)
        # L2 normalization
        embedding = self.l2_norm(embedding, p=2, dim=1)
        return embedding
    
    def forward(
        self,
        input1: torch.Tensor,
        input2: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through both branches
        
        Args:
            input1: First input features
            input2: Second input features
            
        Returns:
            Tuple of (embedding1, embedding2)
        """
        embedding1 = self.forward_once(input1)
        embedding2 = self.forward_once(input2)
        return embedding1, embedding2
    
    def compute_similarity(
        self,
        embedding1: torch.Tensor,
        embedding2: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute cosine similarity between embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0 to 1)
        """
        # Cosine similarity
        similarity = F.cosine_similarity(embedding1, embedding2, dim=1)
        
        # Convert to range [0, 1]
        similarity = (similarity + 1) / 2
        
        return similarity

class ContrastiveLoss(nn.Module):
    """
    Contrastive loss for Siamese Network training
    """
    
    def __init__(self, margin: float = 1.0):
        """
        Initialize contrastive loss
        
        Args:
            margin: Margin for negative pairs
        """
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
    
    def forward(
        self,
        embedding1: torch.Tensor,
        embedding2: torch.Tensor,
        label: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute contrastive loss
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            label: 1 for similar pairs, 0 for dissimilar pairs
            
        Returns:
            Loss value
        """
        # Euclidean distance
        euclidean_distance = F.pairwise_distance(embedding1, embedding2)
        
        # Contrastive loss
        loss_positive = label * torch.pow(euclidean_distance, 2)
        loss_negative = (1 - label) * torch.pow(
            torch.clamp(self.margin - euclidean_distance, min=0.0), 2
        )
        
        loss = torch.mean(loss_positive + loss_negative)
        return loss

class SimilarityMatcher:
    """
    Similarity matching using trained Siamese Network
    """
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        Initialize similarity matcher
        
        Args:
            model_path: Path to trained model weights
            device: Device to run model on
        """
        self.device = device or settings.DEVICE
        
        # Initialize model
        self.model = SiameseNetwork(
            input_dim=settings.FEATURE_DIM,
            embedding_dim=settings.SIAMESE_EMBEDDING_DIM
        )
        
        # Load trained weights if available
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            except:
                print(f"Warning: Could not load model from {model_path}, using untrained model")
        
        self.model = self.model.to(self.device)
        self.model.eval()
    
    def compute_similarity(
        self,
        query_features: np.ndarray,
        reference_features: np.ndarray
    ) -> float:
        """
        Compute similarity between query and reference images
        
        Args:
            query_features: Features from user-uploaded image
            reference_features: Features from reference product
            
        Returns:
            Similarity score (0 to 1)
        """
        with torch.no_grad():
            # Convert to tensors
            query_tensor = torch.FloatTensor(query_features).unsqueeze(0).to(self.device)
            reference_tensor = torch.FloatTensor(reference_features).unsqueeze(0).to(self.device)
            
            # Get embeddings
            query_embedding = self.model.forward_once(query_tensor)
            reference_embedding = self.model.forward_once(reference_tensor)
            
            # Compute similarity
            similarity = self.model.compute_similarity(query_embedding, reference_embedding)
            
            return float(similarity.item())
    
    def compute_multi_angle_similarity(
        self,
        query_features: dict,
        reference_features_dict: dict
    ) -> dict:
        """
        Compute similarity scores for multiple angles
        
        Args:
            query_features: Features from query image
            reference_features_dict: Dictionary of reference features by angle
            
        Returns:
            Dictionary of similarity scores by angle
        """
        similarities = {}
        
        query_array = np.array(query_features['vit_features'])
        
        for angle, ref_features in reference_features_dict.items():
            if 'vit_features' in ref_features:
                ref_array = np.array(ref_features['vit_features'])
                similarity = self.compute_similarity(query_array, ref_array)
                similarities[angle] = similarity
        
        # Overall similarity (average of best matches)
        if similarities:
            # Take top 3 matches
            top_similarities = sorted(similarities.values(), reverse=True)[:3]
            overall_similarity = np.mean(top_similarities)
        else:
            overall_similarity = 0.0
        
        return {
            'angle_similarities': similarities,
            'overall_similarity': float(overall_similarity),
            'best_match': max(similarities.items(), key=lambda x: x[1]) if similarities else None
        }

# Global similarity matcher
similarity_matcher = SimilarityMatcher()
