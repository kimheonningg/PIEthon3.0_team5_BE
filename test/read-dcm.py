import os
import json
import numpy as np
from PIL import Image
import pydicom
from pydicom.errors import InvalidDicomError

def extract_metadata(ds):
    """Extract relevant metadata from DICOM dataset."""
    metadata = {}
    
    # Patient information
    metadata['patient_info'] = {
        'patient_id': getattr(ds, 'PatientID', 'Unknown'),
        'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
        'patient_birth_date': getattr(ds, 'PatientBirthDate', 'Unknown'),
        'patient_sex': getattr(ds, 'PatientSex', 'Unknown'),
        'patient_age': getattr(ds, 'PatientAge', 'Unknown')
    }
    
    # Study information
    metadata['study_info'] = {
        'study_instance_uid': getattr(ds, 'StudyInstanceUID', 'Unknown'),
        'study_date': getattr(ds, 'StudyDate', 'Unknown'),
        'study_time': getattr(ds, 'StudyTime', 'Unknown'),
        'study_description': getattr(ds, 'StudyDescription', 'Unknown'),
        'accession_number': getattr(ds, 'AccessionNumber', 'Unknown')
    }
    
    # Series information
    metadata['series_info'] = {
        'series_instance_uid': getattr(ds, 'SeriesInstanceUID', 'Unknown'),
        'series_number': getattr(ds, 'SeriesNumber', 'Unknown'),
        'series_description': getattr(ds, 'SeriesDescription', 'Unknown'),
        'modality': getattr(ds, 'Modality', 'Unknown'),
        'body_part_examined': getattr(ds, 'BodyPartExamined', 'Unknown')
    }
    
    # Image information
    metadata['image_info'] = {
        'sop_instance_uid': getattr(ds, 'SOPInstanceUID', 'Unknown'),
        'instance_number': getattr(ds, 'InstanceNumber', 'Unknown'),
        'rows': getattr(ds, 'Rows', 'Unknown'),
        'columns': getattr(ds, 'Columns', 'Unknown'),
        'pixel_spacing': getattr(ds, 'PixelSpacing', 'Unknown'),
        'slice_thickness': getattr(ds, 'SliceThickness', 'Unknown'),
        'window_center': getattr(ds, 'WindowCenter', 'Unknown'),
        'window_width': getattr(ds, 'WindowWidth', 'Unknown')
    }
    
    # Technical parameters
    metadata['technical_info'] = {
        'bits_allocated': getattr(ds, 'BitsAllocated', 'Unknown'),
        'bits_stored': getattr(ds, 'BitsStored', 'Unknown'),
        'high_bit': getattr(ds, 'HighBit', 'Unknown'),
        'pixel_representation': getattr(ds, 'PixelRepresentation', 'Unknown'),
        'photometric_interpretation': getattr(ds, 'PhotometricInterpretation', 'Unknown'),
        'samples_per_pixel': getattr(ds, 'SamplesPerPixel', 'Unknown')
    }
    
    return metadata

def normalize_pixel_array(pixel_array, window_center=None, window_width=None):
    """Normalize pixel array to 0-255 range for image saving."""
    if window_center is not None and window_width is not None:
        # Apply windowing
        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2
        pixel_array = np.clip(pixel_array, img_min, img_max)
        pixel_array = ((pixel_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        # Auto-scale to full range
        if pixel_array.max() > pixel_array.min():
            pixel_array = ((pixel_array - pixel_array.min()) / 
                          (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
        else:
            pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)
    
    return pixel_array

def process_dicom_file(file_path, output_dir):
    """Process a single DICOM file and extract image and metadata."""
    try:
        # Read DICOM file
        ds = pydicom.dcmread(file_path)
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Create subdirectory for this DICOM file
        file_output_dir = os.path.join(output_dir, base_name)
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Extract metadata
        metadata = extract_metadata(ds)
        
        # Save metadata as JSON
        metadata_path = os.path.join(file_output_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"Metadata saved: {metadata_path}")
        
        # Extract and save image if pixel data exists
        if hasattr(ds, 'pixel_array'):
            try:
                pixel_array = ds.pixel_array
                
                # Get windowing parameters if available
                window_center = getattr(ds, 'WindowCenter', None)
                window_width = getattr(ds, 'WindowWidth', None)
                
                # Handle multiple window values (take first if list)
                if isinstance(window_center, (list, tuple)):
                    window_center = window_center[0]
                if isinstance(window_width, (list, tuple)):
                    window_width = window_width[0]
                
                # Normalize pixel array
                normalized_array = normalize_pixel_array(pixel_array, window_center, window_width)
                
                # Convert to PIL Image and save
                if len(normalized_array.shape) == 2:
                    # Single grayscale image
                    img = Image.fromarray(normalized_array, mode='L')
                    image_path = os.path.join(file_output_dir, "image.png")
                    img.save(image_path)
                    print(f"Image saved: {image_path}")
                    
                elif len(normalized_array.shape) == 3:
                    # Check if it's a multi-slice volume or color image
                    if normalized_array.shape[2] == 3:
                        # RGB color image
                        img = Image.fromarray(normalized_array, mode='RGB')
                        image_path = os.path.join(file_output_dir, "image.png")
                        img.save(image_path)
                        print(f"Color image saved: {image_path}")
                        
                    elif normalized_array.shape[2] == 1:
                        # Single channel image with extra dimension
                        img = Image.fromarray(normalized_array.squeeze(), mode='L')
                        image_path = os.path.join(file_output_dir, "image.png")
                        img.save(image_path)
                        print(f"Image saved: {image_path}")
                        
                    else:
                        # Multi-slice volume (slices, height, width)
                        num_slices = normalized_array.shape[0]
                        print(f"Multi-slice volume detected: {num_slices} slices of {normalized_array.shape[1]}x{normalized_array.shape[2]}")
                        
                        # Create a subdirectory for slices
                        slices_dir = os.path.join(file_output_dir, "slices")
                        os.makedirs(slices_dir, exist_ok=True)
                        
                        # Save each slice as a separate image
                        for slice_idx in range(num_slices):
                            slice_img = Image.fromarray(normalized_array[slice_idx], mode='L')
                            slice_path = os.path.join(slices_dir, f"slice_{slice_idx:04d}.png")
                            slice_img.save(slice_path)
                        
                        print(f"Saved {num_slices} slices to: {slices_dir}")
                        
                        # Also create a montage image showing all slices
                        montage_cols = int(np.ceil(np.sqrt(num_slices)))
                        montage_rows = int(np.ceil(num_slices / montage_cols))
                        
                        slice_height, slice_width = normalized_array.shape[1], normalized_array.shape[2]
                        montage_img = Image.new('L', (montage_cols * slice_width, montage_rows * slice_height), 0)
                        
                        for slice_idx in range(num_slices):
                            row = slice_idx // montage_cols
                            col = slice_idx % montage_cols
                            x = col * slice_width
                            y = row * slice_height
                            
                            slice_pil = Image.fromarray(normalized_array[slice_idx], mode='L')
                            montage_img.paste(slice_pil, (x, y))
                        
                        montage_path = os.path.join(file_output_dir, "montage.png")
                        montage_img.save(montage_path)
                        print(f"Montage image saved: {montage_path}")
                        
                else:
                    print(f"Unsupported image dimensions: {normalized_array.shape}")
                    return
                
                # Also save raw pixel data as numpy array
                raw_data_path = os.path.join(file_output_dir, "raw_pixels.npy")
                np.save(raw_data_path, ds.pixel_array)
                print(f"Raw pixel data saved: {raw_data_path}")
                
            except Exception as e:
                print(f"Error processing pixel data for {file_path}: {e}")
        else:
            print(f"No pixel data found in {file_path}")
            
    except InvalidDicomError:
        print(f"Invalid DICOM file: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    """Main function to process all DICOM files in the data folder."""
    data_folder = "data"
    output_folder = "output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Check if data folder exists
    if not os.path.exists(data_folder):
        print(f"Error: '{data_folder}' folder not found!")
        return
    
    # Find all .dcm files
    dcm_files = []
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.lower().endswith('.dcm'):
                dcm_files.append(os.path.join(root, file))
    
    if not dcm_files:
        print(f"No .dcm files found in '{data_folder}' folder!")
        return
    
    print(f"Found {len(dcm_files)} DICOM files")
    print(f"Output will be saved to '{output_folder}' folder")
    print("-" * 50)
    
    # Process each DICOM file
    for i, dcm_file in enumerate(dcm_files, 1):
        print(f"Processing {i}/{len(dcm_files)}: {dcm_file}")
        process_dicom_file(dcm_file, output_folder)
        print()
    
    print("Processing complete!")

if __name__ == "__main__":
    main()