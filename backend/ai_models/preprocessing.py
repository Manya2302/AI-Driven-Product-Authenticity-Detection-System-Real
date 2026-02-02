"""
Image preprocessing utilities for AI analysis
"""
import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from typing import Tuple, Optional
import albumentations as A
from albumentations.pytorch import ToTensorV2
from ..app.config import settings

class ImagePreprocessor:
    """Advanced image preprocessing for product authenticity detection"""
    
    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        """
        Initialize preprocessor
        
        Args:
            target_size: Target image size (width, height)
        """
        self.target_size = target_size
        
        # Normalization parameters (ImageNet standards)
        self.mean = settings.NORMALIZATION_MEAN
        self.std = settings.NORMALIZATION_STD
        
        # Define augmentation pipeline for training
        self.train_transform = A.Compose([
            A.Resize(*target_size),
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=15, p=0.3),
            A.RandomBrightnessContrast(p=0.3),
            A.GaussNoise(p=0.2),
            A.Normalize(mean=self.mean, std=self.std),
            ToTensorV2()
        ])
        
        # Define transform for inference (no augmentation)
        self.inference_transform = transforms.Compose([
            transforms.Resize(target_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.mean, std=self.std)
        ])
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load image from file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image as numpy array (RGB)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply denoising to image
        
        Args:
            image: Input image
            
        Returns:
            Denoised image
        """
        # Non-local means denoising
        denoised = cv2.fastNlMeansDenoisingColored(
            image, None, 10, 10, 7, 21
        )
        return denoised
    
    def enhance_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance edges in image
        
        Args:
            image: Input image
            
        Returns:
            Edge-enhanced image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply bilateral filter to smooth while preserving edges
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(filtered, -1, kernel)
        
        # Merge back to RGB
        enhanced = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
        
        # Blend with original
        result = cv2.addWeighted(image, 0.7, enhanced, 0.3, 0)
        return result
    
    def adjust_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Adaptive histogram equalization
        
        Args:
            image: Input image
            
        Returns:
            Contrast-adjusted image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        
        # Merge channels
        lab_clahe = cv2.merge([l_clahe, a, b])
        
        # Convert back to RGB
        enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
        return enhanced
    
    def preprocess_for_inference(self, image_path: str) -> Tuple[torch.Tensor, np.ndarray]:
        """
        Full preprocessing pipeline for inference
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (preprocessed tensor, original image)
        """
        # Load image
        image = self.load_image(image_path)
        original = image.copy()
        
        # Denoise
        image = self.denoise(image)
        
        # Enhance contrast
        image = self.adjust_contrast(image)
        
        # Enhance edges
        image = self.enhance_edges(image)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Apply transforms
        tensor = self.inference_transform(pil_image)
        
        return tensor, original
    
    def extract_color_features(self, image: np.ndarray) -> dict:
        """
        Extract color-based features
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of color features
        """
        features = {}
        
        # Dominant colors using K-means
        pixels = image.reshape(-1, 3)
        pixels = np.float32(pixels)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        k = 5
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        
        centers = np.uint8(centers)
        features['dominant_colors'] = centers.tolist()
        
        # Color histogram
        hist_r = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
        hist_b = cv2.calcHist([image], [2], None, [256], [0, 256])
        
        hist_r = hist_r.flatten() / hist_r.sum()
        hist_g = hist_g.flatten() / hist_g.sum()
        hist_b = hist_b.flatten() / hist_b.sum()
        
        features['color_histogram'] = np.concatenate([hist_r, hist_g, hist_b]).tolist()
        
        return features
    
    def extract_edge_features(self, image: np.ndarray) -> dict:
        """
        Extract edge-based features
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of edge features
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Canny edge detection
        edges = cv2.Canny(gray, 100, 200)
        
        # Edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        # Edge direction histogram
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        direction = np.arctan2(sobely, sobelx)
        
        # Histogram of oriented gradients
        hist, _ = np.histogram(direction, bins=18, range=(-np.pi, np.pi), weights=magnitude)
        hist = hist / (hist.sum() + 1e-6)
        
        features = {
            'edge_density': float(edge_density),
            'hog_features': hist.tolist()
        }
        
        return features

# Global preprocessor instance
preprocessor = ImagePreprocessor(target_size=settings.IMAGE_SIZE)
