import os
import json
import numpy as np
from PIL import Image
import nibabel as nib
from datetime import datetime
import warnings

def extract_metadata(nii_img):
    """Extract relevant metadata from NIfTI image."""
    metadata = {}
    
    # Get header information
    header = nii_img.header
    
    # Basic image information
    metadata['image_info'] = {
        'filename': getattr(nii_img, 'file_name', 'Unknown'),
        'data_shape': list(nii_img.shape),
        'data_dtype': str(nii_img.get_data_dtype()),
        'ndim': nii_img.ndim,
        'voxel_sizes': list(header.get_zooms()),
        'voxel_units': header.get_xyzt_units()[0] if header.get_xyzt_units() else 'Unknown',
        'time_units': header.get_xyzt_units()[1] if len(header.get_xyzt_units()) > 1 else 'Unknown'
    }
    
    # Affine transformation matrix
    metadata['spatial_info'] = {
        'affine_matrix': nii_img.affine.tolist(),
        'qform_code': int(header['qform_code']) if 'qform_code' in header else 'Unknown',
        'sform_code': int(header['sform_code']) if 'sform_code' in header else 'Unknown',
        'pixdim': list(header['pixdim']) if 'pixdim' in header else 'Unknown',
        'orientation': nib.aff2axcodes(nii_img.affine)
    }
    
    # Header-specific information
    metadata['header_info'] = {
        'sizeof_hdr': int(header['sizeof_hdr']) if 'sizeof_hdr' in header else 'Unknown',
        'data_type': int(header['datatype']) if 'datatype' in header else 'Unknown',
        'bitpix': int(header['bitpix']) if 'bitpix' in header else 'Unknown',
        'slice_start': int(header['slice_start']) if 'slice_start' in header else 'Unknown',
        'slice_end': int(header['slice_end']) if 'slice_end' in header else 'Unknown',
        'slice_duration': float(header['slice_duration']) if 'slice_duration' in header else 'Unknown',
        'toffset': float(header['toffset']) if 'toffset' in header else 'Unknown'
    }
    
    # Intensity scaling information
    metadata['intensity_info'] = {
        'scl_slope': float(header['scl_slope']) if 'scl_slope' in header else 'Unknown',
        'scl_inter': float(header['scl_inter']) if 'scl_inter' in header else 'Unknown',
        'cal_max': float(header['cal_max']) if 'cal_max' in header else 'Unknown',
        'cal_min': float(header['cal_min']) if 'cal_min' in header else 'Unknown',
        'glmax': int(header['glmax']) if 'glmax' in header else 'Unknown',
        'glmin': int(header['glmin']) if 'glmin' in header else 'Unknown'
    }
    
    # Description and auxiliary information
    metadata['description_info'] = {
        'descrip': header['descrip'].tobytes().decode('utf-8', errors='ignore').strip('\x00') if 'descrip' in header else 'Unknown',
        'aux_file': header['aux_file'].tobytes().decode('utf-8', errors='ignore').strip('\x00') if 'aux_file' in header else 'Unknown',
        'intent_name': header['intent_name'].tobytes().decode('utf-8', errors='ignore').strip('\x00') if 'intent_name' in header else 'Unknown',
        'intent_code': int(header['intent_code']) if 'intent_code' in header else 'Unknown'
    }
    
    # Statistical information (if available)
    try:
        data = nii_img.get_fdata()
        metadata['statistics'] = {
            'min_value': float(np.min(data)),
            'max_value': float(np.max(data)),
            'mean_value': float(np.mean(data)),
            'std_value': float(np.std(data)),
            'non_zero_voxels': int(np.count_nonzero(data)),
            'total_voxels': int(data.size)
        }
    except Exception as e:
        metadata['statistics'] = {'error': f'Could not calculate statistics: {str(e)}'}
    
    # Processing timestamp
    metadata['processing_info'] = {
        'processed_at': datetime.now().isoformat(),
        'nibabel_version': nib.__version__
    }
    
    return metadata

def normalize_for_display(data, percentile_range=(2, 98)):
    """Normalize data for display purposes using percentile-based scaling."""
    if data.size == 0:
        return np.zeros_like(data, dtype=np.uint8)
    
    # Remove NaN and infinite values
    valid_data = data[np.isfinite(data)]
    
    if valid_data.size == 0:
        return np.zeros_like(data, dtype=np.uint8)
    
    # Use percentile-based normalization for better contrast
    p_low, p_high = np.percentile(valid_data, percentile_range)
    
    if p_high <= p_low:
        return np.zeros_like(data, dtype=np.uint8)
    
    # Clip and normalize
    normalized = np.clip(data, p_low, p_high)
    normalized = ((normalized - p_low) / (p_high - p_low) * 255).astype(np.uint8)
    
    return normalized

def create_slice_montage(volume_data, axis=2, max_slices=None):
    """Create a montage image showing multiple slices from a volume."""
    if axis >= volume_data.ndim:
        axis = volume_data.ndim - 1
    
    num_slices = volume_data.shape[axis]
    
    # Limit number of slices if specified
    if max_slices and num_slices > max_slices:
        slice_indices = np.linspace(0, num_slices-1, max_slices, dtype=int)
    else:
        slice_indices = range(num_slices)
    
    # Calculate grid dimensions
    n_display_slices = len(slice_indices)
    montage_cols = int(np.ceil(np.sqrt(n_display_slices)))
    montage_rows = int(np.ceil(n_display_slices / montage_cols))
    
    # Get slice dimensions
    slice_shape = list(volume_data.shape)
    slice_shape.pop(axis)
    slice_height, slice_width = slice_shape[0], slice_shape[1]
    
    # Create montage
    montage_img = Image.new('L', (montage_cols * slice_width, montage_rows * slice_height), 0)
    
    for i, slice_idx in enumerate(slice_indices):
        row = i // montage_cols
        col = i % montage_cols
        x = col * slice_width
        y = row * slice_height
        
        # Extract slice based on axis
        if axis == 0:
            slice_data = volume_data[slice_idx, :, :]
        elif axis == 1:
            slice_data = volume_data[:, slice_idx, :]
        else:  # axis == 2
            slice_data = volume_data[:, :, slice_idx]
        
        # Normalize for display
        normalized_slice = normalize_for_display(slice_data)
        slice_pil = Image.fromarray(normalized_slice, mode='L')
        montage_img.paste(slice_pil, (x, y))
    
    return montage_img, slice_indices

def process_nifti_file(file_path, output_dir):
    """Process a single NIfTI file and extract image and metadata."""
    try:
        # Load NIfTI file
        print(f"Loading NIfTI file: {file_path}")
        nii_img = nib.load(file_path)
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if base_name.endswith('.nii'):
            base_name = os.path.splitext(base_name)[0]
        
        # Create subdirectory for this NIfTI file
        file_output_dir = os.path.join(output_dir, base_name)
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Extract metadata
        print("Extracting metadata...")
        metadata = extract_metadata(nii_img)
        
        # Save metadata as JSON
        metadata_path = os.path.join(file_output_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"Metadata saved: {metadata_path}")
        
        # Get image data
        print("Loading image data...")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data = nii_img.get_fdata()
        
        print(f"Data shape: {data.shape}, Data type: {data.dtype}")
        
        # Save raw data
        raw_data_path = os.path.join(file_output_dir, "raw_data.npy")
        np.save(raw_data_path, data)
        print(f"Raw data saved: {raw_data_path}")
        
        # Process based on dimensionality
        if data.ndim == 2:
            # 2D image
            normalized_data = normalize_for_display(data)
            img = Image.fromarray(normalized_data, mode='L')
            image_path = os.path.join(file_output_dir, "image.png")
            img.save(image_path)
            print(f"2D image saved: {image_path}")
            
        elif data.ndim == 3:
            # 3D volume - create slices and montages for each axis
            print(f"Processing 3D volume: {data.shape}")
            
            axes_names = ['sagittal', 'coronal', 'axial']
            
            for axis in range(3):
                axis_name = axes_names[axis]
                axis_dir = os.path.join(file_output_dir, f"slices_{axis_name}")
                os.makedirs(axis_dir, exist_ok=True)
                
                num_slices = data.shape[axis]
                print(f"Saving {num_slices} {axis_name} slices...")
                
                # Save individual slices
                for slice_idx in range(num_slices):
                    if axis == 0:
                        slice_data = data[slice_idx, :, :]
                    elif axis == 1:
                        slice_data = data[:, slice_idx, :]
                    else:  # axis == 2
                        slice_data = data[:, :, slice_idx]
                    
                    normalized_slice = normalize_for_display(slice_data)
                    slice_img = Image.fromarray(normalized_slice, mode='L')
                    slice_path = os.path.join(axis_dir, f"slice_{slice_idx:04d}.png")
                    slice_img.save(slice_path)
                
                # Create montage
                montage_img, slice_indices = create_slice_montage(data, axis=axis, max_slices=64)
                montage_path = os.path.join(file_output_dir, f"montage_{axis_name}.png")
                montage_img.save(montage_path)
                print(f"{axis_name.capitalize()} montage saved: {montage_path}")
            
            # Create a summary montage with middle slices from each axis
            summary_montage = Image.new('L', (data.shape[1] * 3, data.shape[0]), 0)
            
            # Middle sagittal slice
            mid_sag = normalize_for_display(data[data.shape[0]//2, :, :])
            summary_montage.paste(Image.fromarray(mid_sag, mode='L'), (0, 0))
            
            # Middle coronal slice
            mid_cor = normalize_for_display(data[:, data.shape[1]//2, :])
            summary_montage.paste(Image.fromarray(mid_cor, mode='L'), (data.shape[1], 0))
            
            # Middle axial slice
            mid_ax = normalize_for_display(data[:, :, data.shape[2]//2])
            summary_montage.paste(Image.fromarray(mid_ax, mode='L'), (data.shape[1] * 2, 0))
            
            summary_path = os.path.join(file_output_dir, "summary_orthogonal.png")
            summary_montage.save(summary_path)
            print(f"Summary orthogonal view saved: {summary_path}")
            
        elif data.ndim == 4:
            # 4D data (time series or multi-contrast)
            print(f"Processing 4D data: {data.shape}")
            
            # Save middle volume slices
            mid_volume_idx = data.shape[3] // 2
            mid_volume = data[:, :, :, mid_volume_idx]
            
            # Create montage for middle volume
            montage_img, _ = create_slice_montage(mid_volume, axis=2, max_slices=36)
            montage_path = os.path.join(file_output_dir, f"montage_volume_{mid_volume_idx:04d}.png")
            montage_img.save(montage_path)
            print(f"4D middle volume montage saved: {montage_path}")
            
            # Save time series data info
            timeseries_info = {
                'num_volumes': data.shape[3],
                'middle_volume_saved': mid_volume_idx,
                'volume_shape': list(data.shape[:3])
            }
            
            timeseries_path = os.path.join(file_output_dir, "timeseries_info.json")
            with open(timeseries_path, 'w') as f:
                json.dump(timeseries_info, f, indent=2)
            print(f"Time series info saved: {timeseries_path}")
            
        else:
            print(f"Unsupported dimensionality: {data.ndim}D")
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to process all NIfTI files in the data folder."""
    data_folder = "data"
    output_folder = "output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Check if data folder exists
    if not os.path.exists(data_folder):
        print(f"Error: '{data_folder}' folder not found!")
        return
    
    # Find all NIfTI files (.nii, .nii.gz)
    nii_files = []
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.lower().endswith(('.nii', '.nii.gz')):
                nii_files.append(os.path.join(root, file))
    
    if not nii_files:
        print(f"No NIfTI files (.nii, .nii.gz) found in '{data_folder}' folder!")
        return
    
    print(f"Found {len(nii_files)} NIfTI files")
    print(f"Output will be saved to '{output_folder}' folder")
    print("-" * 60)
    
    # Process each NIfTI file
    for i, nii_file in enumerate(nii_files, 1):
        print(f"\nProcessing {i}/{len(nii_files)}: {nii_file}")
        print("=" * 60)
        process_nifti_file(nii_file, output_folder)
        print("=" * 60)
    
    print(f"\nProcessing complete! All files processed and saved to '{output_folder}'")

if __name__ == "__main__":
    main()