"""
AI Model Inference Service for Medical Imaging.
Provides mock inference results for brain MRI and chest X-ray disease detection.
"""

import logging
import random
from typing import List, Dict, Any

from app.core.db.schema import ModalityType, BodyPartType, DiseaseClassType


logger = logging.getLogger(__name__)


class AIModelService:
    """Mock AI service that provides hardcoded inference results."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIModelService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.device = "cpu"
            logger.info("🤖 Mock AI service initialized - using hardcoded inference results")
            self._initialized = True
    
    def _load_models(self):
        """Load both brain MRI and chest X-ray models."""
        if self.models_loaded:
            logger.info("Models already loaded, skipping...")
            return
            
        logger.info("Starting AI model loading process...")
        
        try:
            # Add AI model directories to Python path
            current_dir = os.getcwd()
            brain_mri_path = os.path.join(current_dir, "ai", "BrainMRI")
            chest_xray_path = os.path.join(current_dir, "ai", "ChestXray")
            
            logger.info(f"Current working directory: {current_dir}")
            logger.info(f"Looking for Brain MRI modules at: {brain_mri_path}")
            logger.info(f"Looking for Chest X-ray modules at: {chest_xray_path}")
            
            # Check if directories exist
            brain_dir_exists = os.path.exists(brain_mri_path)
            chest_dir_exists = os.path.exists(chest_xray_path)
            logger.info(f"Brain MRI directory exists: {brain_dir_exists}")
            logger.info(f"Chest X-ray directory exists: {chest_dir_exists}")
            
            # Temporarily add to path
            original_sys_path = sys.path.copy()
            if brain_mri_path not in sys.path:
                sys.path.insert(0, brain_mri_path)
                logger.info(f"Added Brain MRI path to sys.path")
            if chest_xray_path not in sys.path:
                sys.path.insert(0, chest_xray_path)
                logger.info(f"Added Chest X-ray path to sys.path")
            
            # Load brain MRI model
            brain_model_path = "data/brainMRI_model_weights.pkl"
            brain_file_exists = os.path.exists(brain_model_path)
            logger.info(f"Brain MRI model file exists at {brain_model_path}: {brain_file_exists}")
            
            if brain_file_exists:
                try:
                    logger.info("Loading Brain MRI model...")
                    logger.info(f"Using device: {self.device}")
                    logger.info(f"CUDA available: {torch.cuda.is_available()}")
                    logger.info(f"Loading from: {os.path.abspath(brain_model_path)}")
                    
                    # Try multiple approaches to load the model
                    try:
                        # First try with explicit CPU mapping
                        self.brain_model = torch.load(brain_model_path, map_location='cpu', weights_only=False)
                        logger.info("Brain MRI model loaded with map_location='cpu'")
                    except Exception as e1:
                        logger.warning(f"Failed with map_location='cpu': {e1}")
                        try:
                            # Try with lambda mapping
                            self.brain_model = torch.load(brain_model_path, map_location=lambda storage, loc: storage, weights_only=False)
                            logger.info("Brain MRI model loaded with lambda mapping")
                        except Exception as e2:
                            logger.error(f"Failed with lambda mapping: {e2}")
                            raise e1  # Raise the original error
                    
                    self.brain_model.eval()
                    logger.info("Brain MRI model set to eval mode")
                    
                    self.brain_model = self.brain_model.to(self.device)
                    logger.info(f"Brain MRI model moved to device: {self.device}")
                    logger.info("✅ Brain MRI model loaded successfully!")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load brain MRI model: {e}")
                    self.brain_model = None
            else:
                logger.warning(f"Brain MRI model not found at {brain_model_path}")
            
            # Load chest X-ray model
            chest_model_path = "data/chest_Xray_weight.pkl"
            chest_file_exists = os.path.exists(chest_model_path)
            logger.info(f"Chest X-ray model file exists at {chest_model_path}: {chest_file_exists}")
            
            if chest_file_exists:
                try:
                    logger.info("Loading Chest X-ray model...")
                    logger.info(f"Using device: {self.device}")
                    # Explicitly use CPU for compatibility
                    self.chest_model = torch.load(chest_model_path, map_location=torch.device('cpu'), weights_only=False)
                    logger.info("Chest X-ray model torch.load completed successfully")
                    
                    self.chest_model.eval()
                    logger.info("Chest X-ray model set to eval mode")
                    logger.info(f"Chest X-ray model on device: {self.device}")
                    logger.info("✅ Chest X-ray model loaded successfully!")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load chest X-ray model: {e}")
                    self.chest_model = None
            else:
                logger.warning(f"Chest X-ray model not found at {chest_model_path}")
                
            # Restore original sys.path
            sys.path = original_sys_path
            logger.info("Restored original sys.path")
            self.models_loaded = True
            
            # Summary
            brain_status = "✅ Loaded" if self.brain_model else "❌ Failed"
            chest_status = "✅ Loaded" if self.chest_model else "❌ Failed"
            logger.info(f"🔬 AI Model Loading Summary:")
            logger.info(f"   Brain MRI: {brain_status}")
            logger.info(f"   Chest X-ray: {chest_status}")
            logger.info(f"   Device: {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Critical error during model loading initialization: {e}")
            # Restore original sys.path on error
            if 'original_sys_path' in locals():
                sys.path = original_sys_path
                logger.info("Restored sys.path after error")
            self.models_loaded = True  # Mark as attempted to avoid infinite retries
    
    @property
    def models_available(self) -> Dict[str, bool]:
        """Check which models are available."""
        return {
            "brain_mri": self.brain_model is not None,
            "chest_xray": self.chest_model is not None
        }


class ClassMapping:
    """Class label mappings for different models."""
    
    # Brain MRI model class mapping (single class: brain tumor)
    BRAIN_MRI_CLASSES = {
        0: DiseaseClassType.BRAIN_TUMOUR
    }
    
    # Chest X-ray model class mapping (multiple disease classes)
    CHEST_XRAY_CLASSES = {
        0: DiseaseClassType.ATELECTASIS,
        1: DiseaseClassType.CARDIOMEGALY,
        2: DiseaseClassType.CONSOLIDATION,
        3: DiseaseClassType.PLEURAL_EFFUSION,
        4: DiseaseClassType.PNEUMOTHORAX,
        5: DiseaseClassType.LUNG_OPACITY,
        6: DiseaseClassType.NODULE_MASS,
        7: DiseaseClassType.INFILTRATION,
        8: DiseaseClassType.PLEURAL_THICKENING,
        9: DiseaseClassType.CALCIFICATION,
        10: DiseaseClassType.AORTIC_ENLARGEMENT,
        11: DiseaseClassType.ILD,
        12: DiseaseClassType.PULMONARY_FIBROSIS,
        13: DiseaseClassType.OTHER_LESION
    }
    
    @classmethod
    def get_disease_class(cls, model_type: str, class_id: int) -> Optional[DiseaseClassType]:
        """Get disease class enum from model output class ID."""
        if model_type == "brain_mri":
            return cls.BRAIN_MRI_CLASSES.get(class_id)
        elif model_type == "chest_xray":
            return cls.CHEST_XRAY_CLASSES.get(class_id)
        return None


class ImageDownloader:
    """Utility for downloading images from URLs."""
    
    @staticmethod
    def download_image_from_url(url: str, timeout: int = 30) -> np.ndarray:
        """
        Download image from URL and convert to OpenCV format.
        
        Args:
            url: Image URL
            timeout: Download timeout in seconds
            
        Returns:
            Image as numpy array in BGR format
            
        Raises:
            Exception: If download or conversion fails
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Convert to PIL Image
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to OpenCV format (BGR)
            img_array = np.array(image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            raise
    
    @staticmethod
    def construct_slice_url(slices_dir: str, slice_idx: int) -> str:
        """
        Construct image URL from slices directory and slice index.
        
        Args:
            slices_dir: Base directory URL for slices
            slice_idx: Slice index (0-based)
            
        Returns:
            Complete image URL
        """
        # Ensure slices_dir ends with /
        if not slices_dir.endswith('/'):
            slices_dir += '/'
        
        # Format slice index as 4-digit zero-padded number
        slice_filename = f"slice_{slice_idx:04d}.png"
        
        return f"{slices_dir}{slice_filename}"


class MedicalImageInference:
    """Main inference engine for medical images."""
    
    def __init__(self):
        self.model_service = AIModelService()
        self.image_downloader = ImageDownloader()
    
    def infer_brain_mri(self, image_url: str, conf_thres: float = 0.25) -> List[Dict[str, Any]]:
        """
        Perform brain MRI inference.
        
        Args:
            image_url: URL to the brain MRI slice image
            conf_thres: Confidence threshold
            
        Returns:
            List of detections (max 1 for brain MRI)
        """
        if not self.model_service.brain_model:
            logger.warning("Brain MRI model not available")
            return []
        
        try:
            # Download image
            img_array = self.image_downloader.download_image_from_url(image_url)
            
            # Preprocess
            img_tensor, img0, _, _ = preprocess_image(img_array, target_size=640)
            img_tensor = img_tensor.to(self.model_service.device)
            
            # Inference
            with torch.no_grad():
                pred = self.model_service.brain_model(img_tensor, augment=False)[0]
            
            # Postprocess
            detections = postprocess_detections(
                pred.unsqueeze(0),  # Add batch dimension back
                img_tensor.shape[2:],
                img0.shape[:2],
                conf_thres=conf_thres,
                iou_thres=0.45
            )
            
            # Convert to disease format and limit to 1 detection (brain model characteristic)
            results = []
            for det in detections[:1]:  # Max 1 detection for brain
                disease_class = ClassMapping.get_disease_class("brain_mri", det['class'])
                result = {
                    "bounding_box": det['bbox'],
                    "confidence_score": det['confidence'],
                    "class_name": disease_class,
                    "disease": disease_class.value if disease_class else None
                }
                results.append(result)
            
            logger.info(f"Brain MRI inference completed: {len(results)} detections")
            return results
            
        except Exception as e:
            logger.error(f"Brain MRI inference failed: {e}")
            return []
    
    def infer_chest_xray(self, image_url: str, conf_thres: float = 0.25) -> List[Dict[str, Any]]:
        """
        Perform chest X-ray inference.
        
        Args:
            image_url: URL to the chest X-ray image
            conf_thres: Confidence threshold
            
        Returns:
            List of detections (can be multiple for chest X-ray)
        """
        if not self.model_service.chest_model:
            logger.warning("Chest X-ray model not available")
            return []
        
        try:
            # Download image
            img_array = self.image_downloader.download_image_from_url(image_url)
            
            # Preprocess
            img_tensor, img0, _, _ = preprocess_image(img_array, target_size=640)
            img_tensor = img_tensor.to(self.model_service.device)
            
            # Inference (different interface for chest model)
            with torch.no_grad():
                pred, _ = self.model_service.chest_model(img_tensor)
            
            # Postprocess
            detections = postprocess_detections(
                pred,
                img_tensor.shape[2:],
                img0.shape[:2],
                conf_thres=conf_thres,
                iou_thres=0.45
            )
            
            # Convert to disease format
            results = []
            for det in detections:
                disease_class = ClassMapping.get_disease_class("chest_xray", det['class'])
                result = {
                    "bounding_box": det['bbox'],
                    "confidence_score": det['confidence'],
                    "class_name": disease_class,
                    "disease": disease_class.value if disease_class else None
                }
                results.append(result)
            
            logger.info(f"Chest X-ray inference completed: {len(results)} detections")
            return results
            
        except Exception as e:
            logger.error(f"Chest X-ray inference failed: {e}")
            return []
    
    def infer_from_series_data(self, 
                              slices_dir: str, 
                              slice_idx: int,
                              modality: ModalityType,
                              body_part: BodyPartType,
                              conf_thres: float = 0.25) -> List[Dict[str, Any]]:
        """
        Perform inference based on series data.
        
        Args:
            slices_dir: Base directory URL for image slices
            slice_idx: Slice index to analyze
            modality: Imaging modality (MRI, X-ray)
            body_part: Body part being imaged (brain, chest)
            conf_thres: Confidence threshold
            
        Returns:
            List of disease detections
        """
        # Construct image URL
        image_url = self.image_downloader.construct_slice_url(slices_dir, slice_idx)
        
        # Determine which model to use
        if modality == ModalityType.MRI and body_part == BodyPartType.BRAIN:
            return self.infer_brain_mri(image_url, conf_thres)
        elif modality == ModalityType.XRAY and body_part == BodyPartType.CHEST:
            return self.infer_chest_xray(image_url, conf_thres)
        else:
            logger.warning(f"No model available for {modality.value} {body_part.value}")
            return []
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of loaded models."""
        models_available = self.model_service.models_available
        return {
            "device": str(self.model_service.device),
            "models_loaded": models_available,
            "total_models": len(models_available),
            "models_ready": sum(models_available.values())
        }


# Global inference engine instance
inference_engine = MedicalImageInference()


def get_inference_engine() -> MedicalImageInference:
    """Get the global inference engine instance."""
    return inference_engine