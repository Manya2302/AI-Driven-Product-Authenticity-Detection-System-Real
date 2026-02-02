"""
Autoencoder for anomaly detection in product images
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple
from ..app.config import settings

class Autoencoder(nn.Module):
    """
    Convolutional Autoencoder for detecting anomalies in product images
    Trained on genuine products, identifies deviations as potential fakes
    """
    
    def __init__(
        self,
        input_channels: int = 3,
        latent_dim: int = 256
    ):
        """
        Initialize Autoencoder
        
        Args:
            input_channels: Number of input channels (3 for RGB)
            latent_dim: Latent space dimension
        """
        super(Autoencoder, self).__init__()
        
        self.latent_dim = latent_dim
        
        # Encoder
        self.encoder = nn.Sequential(
            # Input: 224x224x3
            nn.Conv2d(input_channels, 64, kernel_size=4, stride=2, padding=1),  # 112x112x64
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2),
            
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),  # 56x56x128
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),
            
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),  # 28x28x256
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2),
            
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),  # 14x14x512
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),
            
            nn.Conv2d(512, 512, kernel_size=4, stride=2, padding=1),  # 7x7x512
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),
        )
        
        # Flatten and compress to latent space
        self.fc_encoder = nn.Linear(512 * 7 * 7, latent_dim)
        
        # Expand from latent space
        self.fc_decoder = nn.Linear(latent_dim, 512 * 7 * 7)
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 512, kernel_size=4, stride=2, padding=1),  # 14x14x512
            nn.BatchNorm2d(512),
            nn.ReLU(),
            
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),  # 28x28x256
            nn.BatchNorm2d(256),
            nn.ReLU(),
            
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),  # 56x56x128
            nn.BatchNorm2d(128),
            nn.ReLU(),
            
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),  # 112x112x64
            nn.BatchNorm2d(64),
            nn.ReLU(),
            
            nn.ConvTranspose2d(64, input_channels, kernel_size=4, stride=2, padding=1),  # 224x224x3
            nn.Sigmoid()
        )
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode input to latent representation
        
        Args:
            x: Input image tensor
            
        Returns:
            Latent representation
        """
        x = self.encoder(x)
        x = x.view(x.size(0), -1)
        latent = self.fc_encoder(x)
        return latent
    
    def decode(self, latent: torch.Tensor) -> torch.Tensor:
        """
        Decode latent representation to image
        
        Args:
            latent: Latent representation
            
        Returns:
            Reconstructed image
        """
        x = self.fc_decoder(latent)
        x = x.view(x.size(0), 512, 7, 7)
        reconstructed = self.decoder(x)
        return reconstructed
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through autoencoder
        
        Args:
            x: Input image tensor
            
        Returns:
            Tuple of (reconstructed image, latent representation)
        """
        latent = self.encode(x)
        reconstructed = self.decode(latent)
        return reconstructed, latent

class AnomalyDetector:
    """
    Anomaly detection using trained Autoencoder
    Detects deviations from genuine product patterns
    """
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        Initialize anomaly detector
        
        Args:
            model_path: Path to trained model weights
            device: Device to run model on
        """
        self.device = device or settings.DEVICE
        
        # Initialize model
        self.model = Autoencoder(latent_dim=settings.AUTOENCODER_LATENT_DIM)
        
        # Load trained weights if available
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            except:
                print(f"Warning: Could not load model from {model_path}, using untrained model")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Threshold for anomaly (higher = more anomalous)
        self.threshold = settings.ANOMALY_THRESHOLD
    
    def compute_reconstruction_error(
        self,
        image_tensor: torch.Tensor
    ) -> Tuple[float, torch.Tensor]:
        """
        Compute reconstruction error for anomaly detection
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Tuple of (reconstruction_error, reconstructed_image)
        """
        with torch.no_grad():
            # Ensure batch dimension
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            # Move to device
            image_tensor = image_tensor.to(self.device)
            
            # Forward pass
            reconstructed, latent = self.model(image_tensor)
            
            # Compute MSE reconstruction error
            mse = F.mse_loss(reconstructed, image_tensor, reduction='mean')
            
            # Also compute SSIM-based error (structural similarity)
            ssim_error = self._compute_ssim_error(image_tensor, reconstructed)
            
            # Combine errors
            combined_error = 0.7 * mse.item() + 0.3 * ssim_error
            
            return float(combined_error), reconstructed
    
    def _compute_ssim_error(
        self,
        original: torch.Tensor,
        reconstructed: torch.Tensor
    ) -> float:
        """
        Compute SSIM-based error
        
        Args:
            original: Original image tensor
            reconstructed: Reconstructed image tensor
            
        Returns:
            SSIM error (1 - SSIM)
        """
        from torchmetrics.functional import structural_similarity_index_measure
        
        try:
            ssim = structural_similarity_index_measure(reconstructed, original)
            return 1.0 - ssim.item()
        except:
            # Fallback to simple MSE if SSIM computation fails
            return F.mse_loss(reconstructed, original).item()
    
    def detect_anomaly(
        self,
        image_tensor: torch.Tensor
    ) -> dict:
        """
        Detect if image contains anomalies
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Dictionary with anomaly detection results
        """
        reconstruction_error, reconstructed = self.compute_reconstruction_error(image_tensor)
        
        # Normalize error to 0-1 scale
        # Typical errors range from 0.0 to 0.5, so we scale accordingly
        normalized_error = min(reconstruction_error / 0.5, 1.0)
        
        # Anomaly score (1 = highly anomalous, 0 = normal)
        anomaly_score = normalized_error
        
        # Binary classification
        is_anomalous = anomaly_score > self.threshold
        
        # Compute pixel-wise difference for visualization
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        diff_map = torch.abs(reconstructed - image_tensor.to(self.device))
        diff_map = diff_map.squeeze().cpu().numpy()
        
        # Average across channels for visualization
        if diff_map.ndim == 3:
            diff_map = np.mean(diff_map, axis=0)
        
        return {
            'anomaly_score': float(anomaly_score),
            'is_anomalous': bool(is_anomalous),
            'reconstruction_error': float(reconstruction_error),
            'difference_map': diff_map.tolist(),
            'confidence': float(abs(anomaly_score - self.threshold))
        }
    
    def detect_localized_anomalies(
        self,
        image_tensor: torch.Tensor,
        threshold: float = 0.3
    ) -> list:
        """
        Detect localized anomalous regions
        
        Args:
            image_tensor: Preprocessed image tensor
            threshold: Threshold for anomaly region detection
            
        Returns:
            List of anomalous bounding boxes
        """
        result = self.detect_anomaly(image_tensor)
        diff_map = np.array(result['difference_map'])
        
        # Threshold difference map
        anomaly_mask = (diff_map > threshold).astype(np.uint8)
        
        # Find connected components
        from scipy import ndimage
        labeled, num_features = ndimage.label(anomaly_mask)
        
        # Extract bounding boxes
        anomalous_regions = []
        for i in range(1, num_features + 1):
            region = np.where(labeled == i)
            if len(region[0]) > 100:  # Minimum size threshold
                y_min, y_max = region[0].min(), region[0].max()
                x_min, x_max = region[1].min(), region[1].max()
                
                anomalous_regions.append({
                    'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
                    'area': int(len(region[0])),
                    'severity': float(diff_map[region].mean())
                })
        
        return anomalous_regions

# Global anomaly detector
anomaly_detector = AnomalyDetector()
