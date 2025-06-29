"""
YOLO utility functions for medical imaging inference.
Simplified versions of YOLOv7 utilities for preprocessing and postprocessing.
"""

import torch
import cv2
import numpy as np
from typing import Tuple, List, Optional


def letterbox(img: np.ndarray, new_shape: Tuple[int, int] = (640, 640), color: Tuple[int, int, int] = (114, 114, 114)) -> Tuple[np.ndarray, Tuple[float, float], Tuple[int, int]]:
    """
    Resize and pad image while maintaining aspect ratio.
    
    Args:
        img: Input image (HWC format)
        new_shape: Target shape (height, width)
        color: Padding color
        
    Returns:
        Resized and padded image, scale factors, padding
    """
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)


def non_max_suppression(prediction: torch.Tensor, 
                       conf_thres: float = 0.25, 
                       iou_thres: float = 0.45, 
                       max_det: int = 300) -> List[torch.Tensor]:
    """
    Non-Maximum Suppression (NMS) on inference results.
    
    Args:
        prediction: Model output tensor [batch_size, num_anchors, 5 + num_classes]
        conf_thres: Confidence threshold
        iou_thres: IoU threshold for NMS
        max_det: Maximum number of detections per image
        
    Returns:
        List of detections per image [num_det, 6] (x1, y1, x2, y2, conf, cls)
    """
    device = prediction.device
    batch_size = prediction.shape[0]
    nc = prediction.shape[2] - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Settings
    min_wh, max_wh = 2, 7680  # (pixels) minimum and maximum box width and height
    max_nms = 30000  # maximum number of boxes into torchvision.ops.nms()
    redundant = True  # require redundant detections
    merge = False  # use merge-NMS

    output = [torch.zeros((0, 6), device=device)] * batch_size
    
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        x = x[xc[xi]]  # confidence filtering

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box (center x, center y, width, height) to (x1, y1, x2, y2)
        box = xywh2xyxy(x[:, :4])

        # Detections matrix nx6 (xyxy, conf, cls)
        conf, j = x[:, 5:].max(1, keepdim=True)
        x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

        # Check shape
        n = x.shape[0]  # number of boxes
        if not n:  # no boxes
            continue
        elif n > max_nms:  # excess boxes
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence

        # Batched NMS
        c = x[:, 5:6] * (0 if nc == 1 else max_wh)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torch.ops.torchvision.nms(boxes, scores, iou_thres)  # NMS
        if i.shape[0] > max_det:  # limit detections
            i = i[:max_det]
        
        output[xi] = x[i]

    return output


def xywh2xyxy(x: torch.Tensor) -> torch.Tensor:
    """
    Convert boxes from [x, y, w, h] to [x1, y1, x2, y2] format.
    
    Args:
        x: Input boxes tensor [..., 4]
        
    Returns:
        Converted boxes tensor [..., 4]
    """
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2  # top left x
    y[..., 1] = x[..., 1] - x[..., 3] / 2  # top left y
    y[..., 2] = x[..., 0] + x[..., 2] / 2  # bottom right x
    y[..., 3] = x[..., 1] + x[..., 3] / 2  # bottom right y
    return y


def scale_coords(img1_shape: Tuple[int, int], 
                coords: torch.Tensor, 
                img0_shape: Tuple[int, int], 
                ratio_pad: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None) -> torch.Tensor:
    """
    Rescale coordinates from img1_shape to img0_shape.
    
    Args:
        img1_shape: Input image shape (height, width)
        coords: Coordinates tensor [..., 4] (x1, y1, x2, y2)
        img0_shape: Original image shape (height, width)
        ratio_pad: Scaling ratio and padding info
        
    Returns:
        Rescaled coordinates tensor
    """
    if ratio_pad is None:  # calculate from img0_shape
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    coords[..., [0, 2]] -= pad[0]  # x padding
    coords[..., [1, 3]] -= pad[1]  # y padding
    coords[..., :4] /= gain
    clip_coords(coords, img0_shape)
    return coords


def clip_coords(boxes: torch.Tensor, shape: Tuple[int, int]) -> None:
    """
    Clip bounding xyxy boxes to image shape (height, width).
    
    Args:
        boxes: Bounding boxes tensor [..., 4]
        shape: Image shape (height, width)
    """
    boxes[..., [0, 2]] = boxes[..., [0, 2]].clamp(0, shape[1])  # x1, x2
    boxes[..., [1, 3]] = boxes[..., [1, 3]].clamp(0, shape[0])  # y1, y2


def preprocess_image(img_path_or_array: str | np.ndarray, target_size: int = 640) -> Tuple[torch.Tensor, np.ndarray, Tuple[float, float], Tuple[float, float]]:
    """
    Preprocess image for YOLO inference.
    
    Args:
        img_path_or_array: Image file path or numpy array
        target_size: Target image size
        
    Returns:
        Preprocessed tensor, original image, scale ratios, padding
    """
    # Load image
    if isinstance(img_path_or_array, str):
        img0 = cv2.imread(img_path_or_array)  # BGR
        if img0 is None:
            raise ValueError(f"Could not load image from {img_path_or_array}")
    else:
        img0 = img_path_or_array.copy()
    
    # Preprocess
    img, ratio, pad = letterbox(img0, new_shape=(target_size, target_size))
    img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    img = np.ascontiguousarray(img)
    img = torch.from_numpy(img).float()
    img /= 255.0
    img = img.unsqueeze(0)  # Add batch dimension
    
    return img, img0, ratio, pad


def postprocess_detections(pred: torch.Tensor, 
                         img_shape: Tuple[int, int], 
                         orig_shape: Tuple[int, int],
                         conf_thres: float = 0.25,
                         iou_thres: float = 0.45) -> List[dict]:
    """
    Postprocess YOLO model predictions.
    
    Args:
        pred: Model predictions
        img_shape: Preprocessed image shape (height, width) 
        orig_shape: Original image shape (height, width)
        conf_thres: Confidence threshold
        iou_thres: IoU threshold for NMS
        
    Returns:
        List of detection dictionaries with 'class', 'confidence', 'bbox'
    """
    # Apply NMS
    pred = non_max_suppression(pred, conf_thres=conf_thres, iou_thres=iou_thres)
    
    detections = []
    for det in pred:
        if len(det):
            # Rescale boxes from img_size to img0 size
            det[:, :4] = scale_coords(img_shape, det[:, :4], orig_shape).round()
            
            for *xyxy, conf, cls in det:
                detection = {
                    'class': int(cls.cpu()),
                    'confidence': float(conf.cpu()),
                    'bbox': {
                        'x1': int(xyxy[0].cpu()),
                        'y1': int(xyxy[1].cpu()),
                        'x2': int(xyxy[2].cpu()),
                        'y2': int(xyxy[3].cpu())
                    }
                }
                detections.append(detection)
    
    return detections