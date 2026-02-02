"""
Grad-CAM for explainable AI - visualize what the model focuses on
"""
import torch
import torch.nn.functional as F
import numpy as np
import cv2
from typing import Tuple, Optional
from PIL import Image

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for explainability
    Shows which regions of the image the model focuses on
    """
    
    def __init__(self, model, target_layer):
        """
        Initialize Grad-CAM
        
        Args:
            model: Neural network model
            target_layer: Layer to extract gradients from
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        """Hook to save forward pass activations"""
        self.activations = output.detach()
    
    def save_gradient(self, module, grad_input, grad_output):
        """Hook to save backward pass gradients"""
        self.gradients = grad_output[0].detach()
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Class Activation Map
        
        Args:
            input_tensor: Input image tensor
            target_class: Target class index (None for highest predicted)
            
        Returns:
            CAM heatmap as numpy array
        """
        # Forward pass
        self.model.eval()
        output = self.model(input_tensor)
        
        # Get target class
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward()
        
        # Generate CAM
        gradients = self.gradients[0]  # [C, H, W]
        activations = self.activations[0]  # [C, H, W]
        
        # Global average pooling on gradients
        weights = gradients.mean(dim=(1, 2))  # [C]
        
        # Weighted combination of activation maps
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
        
        # ReLU to keep only positive influences
        cam = F.relu(cam)
        
        # Normalize to [0, 1]
        cam = cam - cam.min()
        if cam.max() != 0:
            cam = cam / cam.max()
        
        return cam.cpu().numpy()
    
    def visualize_cam(
        self,
        input_tensor: torch.Tensor,
        original_image: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Create visualization by overlaying CAM on original image
        
        Args:
            input_tensor: Input image tensor
            original_image: Original image as numpy array (RGB)
            alpha: Transparency for overlay
            
        Returns:
            Overlaid visualization
        """
        # Generate CAM
        cam = self.generate_cam(input_tensor)
        
        # Resize CAM to match original image
        cam_resized = cv2.resize(cam, (original_image.shape[1], original_image.shape[0]))
        
        # Convert to heatmap
        heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        # Overlay on original image
        overlaid = (alpha * heatmap + (1 - alpha) * original_image).astype(np.uint8)
        
        return overlaid

class ProductAuthenticityExplainer:
    """
    Explainable AI for product authenticity detection
    Provides visual and textual explanations for decisions
    """
    
    def __init__(self):
        """Initialize explainer"""
        pass
    
    def generate_visual_explanation(
        self,
        image_tensor: torch.Tensor,
        original_image: np.ndarray,
        model,
        target_layer
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate visual explanation using Grad-CAM
        
        Args:
            image_tensor: Preprocessed image tensor
            original_image: Original image
            model: Model to explain
            target_layer: Layer to extract activations from
            
        Returns:
            Tuple of (heatmap, overlaid_image)
        """
        gradcam = GradCAM(model, target_layer)
        
        # Generate CAM
        cam = gradcam.generate_cam(image_tensor)
        
        # Create visualization
        overlaid = gradcam.visualize_cam(image_tensor, original_image)
        
        return cam, overlaid
    
    def identify_suspicious_regions(
        self,
        cam: np.ndarray,
        threshold: float = 0.7
    ) -> list:
        """
        Identify suspicious regions from CAM
        
        Args:
            cam: Class activation map
            threshold: Threshold for suspicion
            
        Returns:
            List of bounding boxes for suspicious regions
        """
        # Threshold the CAM
        suspicious_mask = (cam > threshold).astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(
            suspicious_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Extract bounding boxes
        regions = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Minimum area
                x, y, w, h = cv2.boundingRect(contour)
                regions.append({
                    'bbox': [int(x), int(y), int(x+w), int(y+h)],
                    'area': int(cv2.contourArea(contour)),
                    'confidence': float(cam[y:y+h, x:x+w].mean())
                })
        
        # Sort by confidence
        regions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return regions
    
    def generate_textual_explanation(
        self,
        analysis_results: dict
    ) -> dict:
        """
        Generate human-readable explanation of the decision
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Dictionary with explanations and recommendations
        """
        explanations = []
        recommendations = []
        
        # Visual similarity explanation
        visual_score = analysis_results.get('visual_similarity_score', 0)
        if visual_score > 0.8:
            explanations.append(
                f"✓ The product's appearance closely matches the authentic reference (similarity: {visual_score:.1%})"
            )
        elif visual_score > 0.6:
            explanations.append(
                f"⚠ The product shows moderate similarity to the authentic version (similarity: {visual_score:.1%})"
            )
            recommendations.append("Compare with official product images for verification")
        else:
            explanations.append(
                f"✗ Significant visual differences detected from authentic product (similarity: {visual_score:.1%})"
            )
            recommendations.append("Exercise caution - product may be counterfeit")
        
        # Text validation explanation
        text_score = analysis_results.get('text_validation_score', 0)
        text_issues = analysis_results.get('text_issues', [])
        
        if text_score > 0.85:
            explanations.append("✓ Brand text matches expected format and spelling")
        elif text_score > 0.6:
            explanations.append(f"⚠ Brand text shows minor discrepancies (match: {text_score:.1%})")
            if text_issues:
                explanations.append(f"  Issues found: {', '.join(text_issues[:2])}")
        else:
            explanations.append(f"✗ Brand text significantly differs from authentic (match: {text_score:.1%})")
            if text_issues:
                explanations.append(f"  Critical issues: {', '.join(text_issues)}")
            recommendations.append("Verify brand name spelling carefully")
        
        # Anomaly detection explanation
        anomaly_score = analysis_results.get('anomaly_score', 0)
        if anomaly_score < 0.3:
            explanations.append("✓ Product features align with typical authentic patterns")
        elif anomaly_score < 0.6:
            explanations.append(f"⚠ Some unusual features detected (anomaly level: {anomaly_score:.1%})")
        else:
            explanations.append(f"✗ Significant deviations from authentic product patterns (anomaly: {anomaly_score:.1%})")
            recommendations.append("Product exhibits characteristics uncommon in genuine items")
        
        # Overall verdict
        confidence = analysis_results.get('confidence_score', 0)
        classification = analysis_results.get('classification', 'unknown')
        
        if classification == 'likely_real':
            verdict = f"Based on comprehensive AI analysis, this product is LIKELY AUTHENTIC (confidence: {confidence:.1%})"
            recommendations.append("Product passed multiple authenticity checks")
        elif classification == 'suspicious':
            verdict = f"Analysis indicates SUSPICIOUS characteristics requiring further verification (confidence: {confidence:.1%})"
            recommendations.extend([
                "Compare with official product from authorized retailer",
                "Check for security features (holograms, QR codes, etc.)"
            ])
        else:
            verdict = f"Analysis suggests this product is LIKELY COUNTERFEIT (confidence: {confidence:.1%})"
            recommendations.extend([
                "Do not purchase or consume this product",
                "Report to authorities if purchased from a retailer",
                "Purchase only from authorized distributors"
            ])
        
        return {
            'verdict': verdict,
            'explanations': explanations,
            'recommendations': recommendations,
            'confidence_level': 'HIGH' if confidence > 0.8 else 'MEDIUM' if confidence > 0.6 else 'LOW'
        }

# Global explainer instance
explainer = ProductAuthenticityExplainer()
