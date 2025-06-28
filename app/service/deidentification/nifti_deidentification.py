import os
import json
import datetime as dt
import numpy as np
from typing import Dict, Any, Optional, List, Union
import nibabel as nib
import warnings


class NIfTIDeidentifier:
    """NIfTI 파일의 민감정보를 비식별화하는 클래스"""
    
    # 제거할 헤더 필드들 (민감정보)
    FIELDS_TO_REMOVE = [
        'descrip',      # 설명 정보 (환자 정보 포함 가능)
        'aux_file',     # 보조 파일 정보
        'intent_name'   # 의도 이름 (개인정보 포함 가능)
    ]
    
    # 익명화할 필드들 (완전히 제거하지 않고 일반화)
    FIELDS_TO_ANONYMIZE = [
        'db_name'       # 데이터베이스 이름
    ]
    
    def __init__(self, anonymous_prefix: str = "ANON"):
        """
        비식별화 클래스 초기화
        
        Args:
            anonymous_prefix: 익명 ID에 사용할 접두사
        """
        self.anonymous_prefix = anonymous_prefix
        self._id_counter = 2000  # NIfTI용 카운터 (DICOM과 구분)
    
    def _generate_anonymous_id(self, original_id: str) -> str:
        """
        원본 ID를 단순한 익명 ID로 변환
        
        Args:
            original_id: 원본 ID
            
        Returns:
            str: 익명화된 ID
        """
        self._id_counter += 1
        return f"{self.anonymous_prefix}_NIFTI_{self._id_counter:06d}"
    
    def _anonymize_description(self, desc_field: Any) -> bytes:
        """
        설명 필드를 익명화
        
        Args:
            desc_field: 원본 설명 필드
            
        Returns:
            bytes: 익명화된 설명 바이트
        """
        anonymous_desc = "ANONYMIZED_NIFTI_STUDY"
        # NIfTI 헤더 필드 크기에 맞춰 패딩
        if hasattr(desc_field, 'shape') and len(desc_field.shape) > 0:
            field_size = desc_field.shape[0]
        else:
            field_size = 80  # 기본 크기
        
        padded_desc = anonymous_desc.ljust(field_size, '\x00')[:field_size]
        return padded_desc.encode('utf-8')
    
    def _clean_header_field(self, field_data: Any, replacement: str = "ANONYMIZED") -> bytes:
        """
        헤더 필드를 안전하게 정리
        
        Args:
            field_data: 원본 필드 데이터
            replacement: 대체할 문자열
            
        Returns:
            bytes: 정리된 필드 데이터
        """
        if hasattr(field_data, 'shape') and len(field_data.shape) > 0:
            field_size = field_data.shape[0]
        else:
            field_size = len(str(field_data)) if field_data else 10
        
        # 적절한 크기로 패딩하여 반환
        cleaned = replacement.ljust(field_size, '\x00')[:field_size]
        return cleaned.encode('utf-8')
    
    def deidentify_nifti(self, nii_img: Any) -> nib.Nifti1Image:
        """
        NIfTI 이미지를 비식별화
        
        Args:
            nii_img: nibabel NIfTI 이미지 객체
            
        Returns:
            nib.Nifti1Image: 비식별화된 NIfTI 이미지
        """
        # 헤더 복사
        new_header = nii_img.header.copy()
        
        # 민감정보 필드 제거/익명화
        for field_name in self.FIELDS_TO_REMOVE:
            try:
                if hasattr(new_header, field_name):
                    field_value = getattr(new_header, field_name)
                    if field_name == 'descrip':
                        # 설명은 익명화된 내용으로 변경
                        setattr(new_header, field_name, self._anonymize_description(field_value))
                    else:
                        # 다른 필드들은 빈 값으로 설정
                        if hasattr(field_value, 'shape') and len(field_value.shape) > 0:
                            field_size = field_value.shape[0]
                            setattr(new_header, field_name, b'\x00' * field_size)
            except Exception:
                # 필드 접근 실패시 무시
                continue
        
        # 익명화할 필드들 처리
        for field_name in self.FIELDS_TO_ANONYMIZE:
            try:
                if hasattr(new_header, field_name):
                    field_value = getattr(new_header, field_name)
                    setattr(new_header, field_name, self._clean_header_field(field_value, "ANON_DB"))
            except Exception:
                # 필드 접근 실패시 무시
                continue
        
        # 새로운 NIfTI 이미지 생성 (동일한 데이터, 비식별화된 헤더)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data = nii_img.get_fdata()
            
        anonymized_nii = nib.Nifti1Image(data, nii_img.affine, new_header)
        
        return anonymized_nii
    
    def deidentify_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        NIfTI 파일을 비식별화하여 저장
        
        Args:
            input_path: 입력 NIfTI 파일 경로
            output_path: 출력 NIfTI 파일 경로
            
        Returns:
            Dict: 처리 결과 정보
        """
        result = {
            'success': False,
            'input_path': input_path,
            'output_path': output_path,
            'message': '',
            'removed_fields': [],
            'anonymized_fields': []
        }
        
        try:
            # NIfTI 파일 읽기
            print(f"Loading NIfTI file: {input_path}")
            nii_img = nib.load(input_path)
            
            # 제거/익명화되는 필드들 기록
            removed_fields = []
            for field_name in self.FIELDS_TO_REMOVE:
                try:
                    if hasattr(nii_img.header, field_name):
                        field_data = getattr(nii_img.header, field_name)
                        if hasattr(field_data, 'tobytes'):
                            decoded = field_data.tobytes().decode('utf-8', errors='ignore').strip('\x00')
                        else:
                            decoded = str(field_data).strip('\x00')
                        if decoded:
                            removed_fields.append(field_name)
                except Exception:
                    continue
            
            anonymized_fields = []
            for field_name in self.FIELDS_TO_ANONYMIZE:
                try:
                    if hasattr(nii_img.header, field_name):
                        field_data = getattr(nii_img.header, field_name)
                        if hasattr(field_data, 'tobytes'):
                            decoded = field_data.tobytes().decode('utf-8', errors='ignore').strip('\x00')
                        else:
                            decoded = str(field_data).strip('\x00')
                        if decoded:
                            anonymized_fields.append(field_name)
                except Exception:
                    continue
            
            result['removed_fields'] = removed_fields
            result['anonymized_fields'] = anonymized_fields
            
            # 비식별화 수행
            print("Performing deidentification...")
            anonymized_nii = self.deidentify_nifti(nii_img)
            
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 비식별화된 파일 저장
            print(f"Saving anonymized file: {output_path}")
            nib.save(anonymized_nii, output_path)
            
            result['success'] = True
            result['message'] = '비식별화 완료'
            
        except Exception as e:
            result['message'] = f'처리 중 오류 발생: {str(e)}'
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def extract_deidentified_metadata(self, nii_img: Any) -> Dict[str, Any]:
        """
        비식별화된 NIfTI에서 메타데이터 추출 (read-nifti.py의 extract_metadata 기반)
        
        Args:
            nii_img: 비식별화된 nibabel NIfTI 이미지
            
        Returns:
            Dict: 비식별화된 메타데이터
        """
        metadata = {}
        header = nii_img.header
        
        # 기본 이미지 정보 (의료적으로 중요한 정보는 유지)
        metadata['image_info'] = {
            'filename': 'ANONYMIZED.nii',  # 파일명 익명화
            'data_shape': list(nii_img.shape),
            'data_dtype': str(nii_img.get_data_dtype()),
            'ndim': nii_img.ndim,
            'voxel_sizes': list(header.get_zooms()),
            'voxel_units': header.get_xyzt_units()[0] if header.get_xyzt_units() else 'Unknown',
            'time_units': header.get_xyzt_units()[1] if len(header.get_xyzt_units()) > 1 else 'Unknown'
        }
        
        # 공간 정보 (의료적 분석에 필요)
        try:
            affine_matrix = nii_img.affine.tolist() if nii_img.affine is not None else 'Unknown'
            orientation = nib.aff2axcodes(nii_img.affine) if nii_img.affine is not None else 'Unknown'
        except Exception:
            affine_matrix = 'Unknown'
            orientation = 'Unknown'
            
        metadata['spatial_info'] = {
            'affine_matrix': affine_matrix,
            'qform_code': int(header['qform_code']) if hasattr(header, 'qform_code') else 'Unknown',
            'sform_code': int(header['sform_code']) if hasattr(header, 'sform_code') else 'Unknown',
            'pixdim': list(header['pixdim']) if hasattr(header, 'pixdim') else 'Unknown',
            'orientation': orientation
        }
        
        # 헤더 정보 (기술적 파라미터)
        metadata['header_info'] = {
            'sizeof_hdr': int(header['sizeof_hdr']) if hasattr(header, 'sizeof_hdr') else 'Unknown',
            'data_type': int(header['datatype']) if hasattr(header, 'datatype') else 'Unknown',
            'bitpix': int(header['bitpix']) if hasattr(header, 'bitpix') else 'Unknown',
            'slice_start': int(header['slice_start']) if hasattr(header, 'slice_start') else 'Unknown',
            'slice_end': int(header['slice_end']) if hasattr(header, 'slice_end') else 'Unknown',
            'slice_duration': float(header['slice_duration']) if hasattr(header, 'slice_duration') else 'Unknown',
            'toffset': float(header['toffset']) if hasattr(header, 'toffset') else 'Unknown'
        }
        
        # 강도 스케일링 정보 (의료 영상 분석에 중요)
        metadata['intensity_info'] = {
            'scl_slope': float(header['scl_slope']) if hasattr(header, 'scl_slope') else 'Unknown',
            'scl_inter': float(header['scl_inter']) if hasattr(header, 'scl_inter') else 'Unknown',
            'cal_max': float(header['cal_max']) if hasattr(header, 'cal_max') else 'Unknown',
            'cal_min': float(header['cal_min']) if hasattr(header, 'cal_min') else 'Unknown',
            'glmax': int(header['glmax']) if hasattr(header, 'glmax') else 'Unknown',
            'glmin': int(header['glmin']) if hasattr(header, 'glmin') else 'Unknown'
        }
        
        # 설명 정보 (비식별화됨)
        metadata['description_info'] = {
            'descrip': 'ANONYMIZED_NIFTI_STUDY',
            'aux_file': 'ANONYMIZED',
            'intent_name': 'ANONYMIZED',
            'intent_code': int(header['intent_code']) if hasattr(header, 'intent_code') else 'Unknown'
        }
        
        # 통계 정보 (의료적 분석에 유용)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                data = nii_img.get_fdata()
            
            # numpy 배열로 변환하여 계산
            data_array = np.asarray(data, dtype=np.float64)
            
            metadata['statistics'] = {
                'min_value': float(data_array.min()),
                'max_value': float(data_array.max()),
                'mean_value': float(data_array.mean()),
                'std_value': float(data_array.std()),
                'non_zero_voxels': int((data_array != 0).sum()),
                'total_voxels': int(data_array.size)
            }
        except Exception as e:
            metadata['statistics'] = {'error': f'Could not calculate statistics: {str(e)}'}
        
        # 비식별화 정보
        metadata['deidentification_info'] = {
            'deidentified': True,
            'deidentification_date': dt.datetime.now().isoformat(),
            'method': 'NIfTIDeidentifier',
            'removed_fields_count': len(self.FIELDS_TO_REMOVE),
            'anonymized_fields_count': len(self.FIELDS_TO_ANONYMIZE),
            'nibabel_version': nib.__version__
        }
        
        return metadata


def process_nifti_file(input_file_path: str, output_directory: str = "output/anonymized", anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    NIfTI 파일을 비식별화하고 결과를 반환하는 메인 함수
    
    Args:
        input_file_path: 입력 NIfTI 파일 경로
        output_directory: 출력 디렉토리 경로
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 비식별화 결과와 메타데이터
    """
    # 비식별화 객체 생성
    deidentifier = NIfTIDeidentifier(anonymous_prefix)
    
    # 파일명 추출 및 출력 경로 생성
    filename = os.path.basename(input_file_path)
    name_without_ext = filename
    if name_without_ext.endswith('.gz'):
        name_without_ext = os.path.splitext(name_without_ext)[0]
    if name_without_ext.endswith('.nii'):
        name_without_ext = os.path.splitext(name_without_ext)[0]
    
    # 확장자 유지
    if filename.endswith('.nii.gz'):
        output_filename = f"anonymized_{name_without_ext}.nii.gz"
    elif filename.endswith('.nii'):
        output_filename = f"anonymized_{name_without_ext}.nii"
    else:
        output_filename = f"anonymized_{filename}"
    
    output_file_path = os.path.join(output_directory, output_filename)
    
    # 비식별화 수행
    deidentification_result = deidentifier.deidentify_file(input_file_path, output_file_path)
    
    # 결과 구성
    result = {
        'success': deidentification_result['success'],
        'message': deidentification_result['message'],
        'input_file': input_file_path,
        'output_file': output_file_path if deidentification_result['success'] else None,
        'processing_info': {
            'removed_fields': deidentification_result['removed_fields'],
            'anonymized_fields': deidentification_result['anonymized_fields'],
            'removed_fields_count': len(deidentification_result['removed_fields']),
            'anonymized_fields_count': len(deidentification_result['anonymized_fields'])
        },
        'metadata': None
    }
    
    # 성공한 경우 메타데이터 추출
    if deidentification_result['success']:
        try:
            # 비식별화된 파일에서 메타데이터 추출
            anonymized_nii = nib.load(output_file_path)
            result['metadata'] = deidentifier.extract_deidentified_metadata(anonymized_nii)
        except Exception as e:
            current_message = result['message']
            result['message'] = f"{current_message} (메타데이터 추출 실패: {str(e)})"
    
    return result


def process_multiple_nifti_files(input_files: List[str], output_directory: str = "output/anonymized", anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    여러 NIfTI 파일을 비식별화하고 결과를 반환하는 함수
    
    Args:
        input_files: 입력 NIfTI 파일 경로 리스트
        output_directory: 출력 디렉토리 경로
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 전체 처리 결과
    """
    results: Dict[str, Union[int, List[Dict[str, Any]]]] = {
        'total_files': len(input_files),
        'successful': 0,
        'failed': 0,
        'files': []
    }
    
    successful_count = 0
    failed_count = 0
    file_results: List[Dict[str, Any]] = []
    
    for input_file in input_files:
        # 각 파일 처리
        file_result = process_nifti_file(input_file, output_directory, anonymous_prefix)
        
        # 결과 카운트
        if file_result['success']:
            successful_count += 1
        else:
            failed_count += 1
        
        # 파일별 결과 저장
        file_results.append({
            'input_file': input_file,
            'success': file_result['success'],
            'message': file_result['message'],
            'output_file': file_result['output_file'],
            'removed_fields_count': file_result['processing_info']['removed_fields_count'],
            'anonymized_fields_count': file_result['processing_info']['anonymized_fields_count']
        })
    
    results['successful'] = successful_count
    results['failed'] = failed_count
    results['files'] = file_results
    
    return results


def deidentify_nifti_directory(input_dir: str, output_dir: str, anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    디렉토리 내의 모든 NIfTI 파일을 비식별화
    
    Args:
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 전체 처리 결과
    """
    deidentifier = NIfTIDeidentifier(anonymous_prefix)
    
    results: Dict[str, Union[int, List[Dict[str, Any]]]] = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'file_results': []
    }
    
    # NIfTI 파일 찾기
    nifti_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.nii', '.nii.gz')):
                nifti_files.append(os.path.join(root, file))
    
    results['total_files'] = len(nifti_files)
    
    # 각 파일 처리
    file_results: List[Dict[str, Any]] = []
    successful_count = 0
    failed_count = 0
    
    for nifti_file in nifti_files:
        # 상대 경로 유지하여 출력 경로 생성
        rel_path = os.path.relpath(nifti_file, input_dir)
        output_file = os.path.join(output_dir, f"anonymized_{rel_path}")
        
        # 비식별화 수행
        file_result = deidentifier.deidentify_file(nifti_file, output_file)
        file_results.append(file_result)
        
        if file_result['success']:
            successful_count += 1
        else:
            failed_count += 1
    
    results['file_results'] = file_results
    results['successful'] = successful_count
    results['failed'] = failed_count
    
    return results


def deidentify_and_return_nifti_metadata(file_path: str, anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    NIfTI 파일을 비식별화하고 메타데이터만 반환하는 함수 (파일 저장 안함)
    
    Args:
        file_path: NIfTI 파일 경로
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 비식별화된 메타데이터와 처리 정보
    """
    result: Dict[str, Any] = {
        'success': False,
        'message': '',
        'original_metadata': None,
        'anonymized_metadata': None,
        'processing_info': {
            'removed_fields': [],
            'anonymized_fields': [],
            'removed_fields_count': 0,
            'anonymized_fields_count': 0
        }
    }
    
    try:
        # 비식별화 객체 생성
        deidentifier = NIfTIDeidentifier(anonymous_prefix)
        
        # 원본 NIfTI 파일 읽기
        print(f"Loading original NIfTI file: {file_path}")
        original_nii = nib.load(file_path)
        
        # 원본 메타데이터 추출
        result['original_metadata'] = deidentifier.extract_deidentified_metadata(original_nii)
        
        # 제거될 필드들 확인
        removed_fields = []
        for field_name in deidentifier.FIELDS_TO_REMOVE:
            try:
                if hasattr(original_nii.header, field_name):
                    field_data = getattr(original_nii.header, field_name)
                    if hasattr(field_data, 'tobytes'):
                        decoded = field_data.tobytes().decode('utf-8', errors='ignore').strip('\x00')
                    else:
                        decoded = str(field_data).strip('\x00')
                    if decoded:
                        removed_fields.append(field_name)
            except Exception:
                continue
        
        # 익명화될 필드들 확인
        anonymized_fields = []
        for field_name in deidentifier.FIELDS_TO_ANONYMIZE:
            try:
                if hasattr(original_nii.header, field_name):
                    field_data = getattr(original_nii.header, field_name)
                    if hasattr(field_data, 'tobytes'):
                        decoded = field_data.tobytes().decode('utf-8', errors='ignore').strip('\x00')
                    else:
                        decoded = str(field_data).strip('\x00')
                    if decoded:
                        anonymized_fields.append(field_name)
            except Exception:
                continue
        
        # 처리 정보 업데이트
        processing_info = result['processing_info']
        if isinstance(processing_info, dict):
            processing_info['removed_fields'] = removed_fields
            processing_info['anonymized_fields'] = anonymized_fields
            processing_info['removed_fields_count'] = len(removed_fields)
            processing_info['anonymized_fields_count'] = len(anonymized_fields)
        
        # 비식별화 수행 (메모리에서만)
        print("Performing deidentification in memory...")
        anonymized_nii = deidentifier.deidentify_nifti(original_nii)
        
        # 비식별화된 메타데이터 추출
        result['anonymized_metadata'] = deidentifier.extract_deidentified_metadata(anonymized_nii)
        
        result['success'] = True
        result['message'] = '비식별화 및 메타데이터 추출 완료'
        
    except Exception as e:
        result['message'] = f'처리 중 오류 발생: {str(e)}'
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result


# 사용 예시
if __name__ == "__main__":
    # 1. 단일 파일 비식별화 (파일 저장)
    print("=== 단일 NIfTI 파일 비식별화 ===")
    result = process_nifti_file(
        "data/BraTS20_Training_001_flair.nii",
        "output/anonymized",
        "ANON"
    )
    print(f"성공: {result['success']}")
    print(f"메시지: {result['message']}")
    if result['success']:
        print(f"출력 파일: {result['output_file']}")
        print(f"제거된 필드 수: {result['processing_info']['removed_fields_count']}")
    print()
    
    # 2. 메타데이터만 추출 (파일 저장 안함)
    print("=== NIfTI 메타데이터만 추출 ===")
    metadata_result = deidentify_and_return_nifti_metadata("data/BraTS20_Training_001_flair.nii", "ANON")
    print(f"성공: {metadata_result['success']}")
    print(f"메시지: {metadata_result['message']}")
    if metadata_result['success']:
        print(f"데이터 형태: {metadata_result['anonymized_metadata']['image_info']['data_shape']}")
        print(f"제거된 필드 수: {metadata_result['processing_info']['removed_fields_count']}")
    print()
    
    # 3. 디렉토리 전체 비식별화
    print("=== 디렉토리 전체 NIfTI 비식별화 ===")
    dir_results = deidentify_nifti_directory(
        "data/",
        "output/anonymized/",
        "ANON"
    )
    print(f"전체 결과: {dir_results['successful']}/{dir_results['total_files']} 파일 성공")
