import os
import json
import datetime
import random
from typing import Dict, Any, Optional, List, Union
import pydicom
from pydicom.errors import InvalidDicomError
from pydicom.tag import Tag


class DICOMDeidentifier:
    """DICOM 파일의 민감정보를 비식별화하는 클래스"""
    
    # 제거할 DICOM 태그들 (민감정보)
    TAGS_TO_REMOVE = [
        'PatientName',
        'PatientID', 
        'PatientBirthDate',
        'PatientAddress',
        'InstitutionName',
        'InstitutionAddress',
        'ReferringPhysicianName',
        'PerformingPhysicianName',
        'OperatorsName',
        'InstitutionalDepartmentName',
        'PhysiciansOfRecord',
        'PerformingPhysicianIdentificationSequence',
        'OperatorIdentificationSequence',
        'StudyID',
        'AccessionNumber',
        'RequestingPhysician',
        'RequestingService',
        'StudyComments',
        'SeriesComments',
        'ImageComments',
        'ScheduledPerformingPhysicianName',
        'DeviceSerialNumber',
        'ProtocolName',
        'StationName',
        'InstitutionCodeSequence',
        'PatientTelephoneNumbers',
        'EthnicGroup',
        'Occupation',
        'AdditionalPatientHistory',
        'PatientComments',
        'PersonName',
        'PersonAddress',
        'PersonTelephoneNumbers'
    ]
    
    # 날짜 관련 태그들 (년도만 유지하고 월/일은 01/01로 변경)
    DATE_TAGS = [
        'StudyDate',
        'SeriesDate',
        'AcquisitionDate',
        'ContentDate',
        'InstanceCreationDate'
    ]
    
    # 시간 관련 태그들 (00:00:00으로 변경)
    TIME_TAGS = [
        'StudyTime',
        'SeriesTime',
        'AcquisitionTime',
        'ContentTime',
        'InstanceCreationTime'
    ]
    
    def __init__(self, anonymous_prefix: str = "ANON"):
        """
        비식별화 클래스 초기화
        
        Args:
            anonymous_prefix: 익명 ID에 사용할 접두사
        """
        self.anonymous_prefix = anonymous_prefix
        self._id_counter = 1000  # 익명 ID 카운터
    
    def _generate_anonymous_id(self, original_id: str) -> str:
        """
        원본 ID를 단순한 익명 ID로 변환
        
        Args:
            original_id: 원본 ID
            
        Returns:
            str: 익명화된 ID
        """
        # 카운터를 증가시켜 고유한 익명 ID 생성
        self._id_counter += 1
        return f"{self.anonymous_prefix}_{self._id_counter:06d}"
    
    def _anonymize_date(self, date_str: str) -> str:
        """
        날짜를 익명화 (년도만 유지하고 월/일은 01/01로 변경)
        
        Args:
            date_str: DICOM 날짜 형식 (YYYYMMDD)
            
        Returns:
            str: 익명화된 날짜
        """
        try:
            if len(date_str) >= 4:
                year = date_str[:4]
                return f"{year}0101"
            return "19700101"  # 기본값
        except:
            return "19700101"
    
    def _anonymize_time(self, time_str: str) -> str:
        """
        시간을 익명화 (00:00:00으로 변경)
        
        Args:
            time_str: DICOM 시간 형식
            
        Returns:
            str: 익명화된 시간
        """
        return "000000"
    
    def _calculate_age_from_date(self, birth_date: str, study_date: str) -> str:
        """
        생년월일과 검사날짜로부터 나이 계산
        
        Args:
            birth_date: 생년월일 (YYYYMMDD)
            study_date: 검사날짜 (YYYYMMDD)
            
        Returns:
            str: 나이 (예: "045Y")
        """
        try:
            birth_year = int(birth_date[:4])
            study_year = int(study_date[:4])
            age = study_year - birth_year
            return f"{age:03d}Y"
        except:
            return "000Y"
    
    def deidentify_dataset(self, ds: pydicom.Dataset) -> pydicom.Dataset:
        """
        DICOM 데이터셋을 비식별화
        
        Args:
            ds: pydicom Dataset 객체
            
        Returns:
            pydicom.Dataset: 비식별화된 데이터셋
        """
        # 원본 값들 저장 (나이 계산용)
        original_patient_id = getattr(ds, 'PatientID', '')
        original_birth_date = getattr(ds, 'PatientBirthDate', '')
        original_study_date = getattr(ds, 'StudyDate', '')
        
        # 민감정보 태그들 제거 또는 익명화
        for tag_name in self.TAGS_TO_REMOVE:
            if hasattr(ds, tag_name):
                if tag_name == 'PatientID':
                    # PatientID는 익명 ID로 변경
                    setattr(ds, 'PatientID', self._generate_anonymous_id(original_patient_id))
                elif tag_name == 'PatientName':
                    # 환자명은 익명명으로 변경
                    setattr(ds, 'PatientName', "ANONYMOUS^PATIENT")
                else:
                    # 나머지는 제거
                    delattr(ds, tag_name)
        
        # 날짜 태그들 익명화
        for tag_name in self.DATE_TAGS:
            if hasattr(ds, tag_name):
                original_date = getattr(ds, tag_name)
                setattr(ds, tag_name, self._anonymize_date(str(original_date)))
        
        # 시간 태그들 익명화
        for tag_name in self.TIME_TAGS:
            if hasattr(ds, tag_name):
                setattr(ds, tag_name, self._anonymize_time(str(getattr(ds, tag_name))))
        
        # 나이 정보가 있으면 계산된 나이로 교체 (더 정확한 나이 제공)
        if original_birth_date and original_study_date:
            calculated_age = self._calculate_age_from_date(original_birth_date, original_study_date)
            setattr(ds, 'PatientAge', calculated_age)
        elif hasattr(ds, 'PatientAge'):
            # 기존 나이 정보가 있으면 유지하되 정확도 조정
            age_str = str(getattr(ds, 'PatientAge', ''))
            if 'Y' in age_str:
                age_num = int(''.join(filter(str.isdigit, age_str)))
                # 5세 단위로 반올림하여 정확도 감소
                rounded_age = round(age_num / 5) * 5
                setattr(ds, 'PatientAge', f"{rounded_age:03d}Y")
        
        # UID들 익명화 (Study, Series, SOP Instance UID)
        if hasattr(ds, 'StudyInstanceUID'):
            setattr(ds, 'StudyInstanceUID', self._generate_anonymous_id('study'))
        
        if hasattr(ds, 'SeriesInstanceUID'):
            setattr(ds, 'SeriesInstanceUID', self._generate_anonymous_id('series'))
        
        if hasattr(ds, 'SOPInstanceUID'):
            setattr(ds, 'SOPInstanceUID', self._generate_anonymous_id('sop'))
        
        # 개인정보가 포함될 수 있는 Description 필드들 일반화
        if hasattr(ds, 'StudyDescription'):
            setattr(ds, 'StudyDescription', "ANONYMIZED_STUDY")
        
        if hasattr(ds, 'SeriesDescription'):
            # 검사 유형은 유지하되 구체적인 정보는 제거
            original_desc = str(getattr(ds, 'SeriesDescription', '')).upper()
            if any(keyword in original_desc for keyword in ['CT', 'MR', 'XRAY', 'US', 'NM']):
                setattr(ds, 'SeriesDescription', "ANONYMIZED_SERIES")
            else:
                setattr(ds, 'SeriesDescription', "ANONYMIZED_SERIES")
        
        return ds
    
    def deidentify_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        DICOM 파일을 비식별화하여 저장
        
        Args:
            input_path: 입력 DICOM 파일 경로
            output_path: 출력 DICOM 파일 경로
            
        Returns:
            Dict: 처리 결과 정보
        """
        result = {
            'success': False,
            'input_path': input_path,
            'output_path': output_path,
            'message': '',
            'removed_tags': [],
            'anonymized_tags': []
        }
        
        try:
            # DICOM 파일 읽기
            ds = pydicom.dcmread(input_path)
            
            # 제거되는 태그들 기록
            removed_tags = []
            for tag_name in self.TAGS_TO_REMOVE:
                if hasattr(ds, tag_name):
                    removed_tags.append(tag_name)
            result['removed_tags'] = removed_tags
            
            # 익명화되는 태그들 기록
            anonymized_tags = []
            for tag_name in self.DATE_TAGS + self.TIME_TAGS:
                if hasattr(ds, tag_name):
                    anonymized_tags.append(tag_name)
            result['anonymized_tags'] = anonymized_tags
            
            # 비식별화 수행
            anonymized_ds = self.deidentify_dataset(ds)
            
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 비식별화된 파일 저장
            anonymized_ds.save_as(output_path)
            
            result['success'] = True
            result['message'] = '비식별화 완료'
            
        except InvalidDicomError:
            result['message'] = '유효하지 않은 DICOM 파일'
        except Exception as e:
            result['message'] = f'처리 중 오류 발생: {str(e)}'
        
        return result
    
    def extract_deidentified_metadata(self, ds: pydicom.Dataset) -> Dict[str, Any]:
        """
        비식별화된 DICOM에서 메타데이터 추출 (read-dcm.py의 extract_metadata 기반)
        
        Args:
            ds: 비식별화된 pydicom Dataset
            
        Returns:
            Dict: 비식별화된 메타데이터
        """
        metadata = {}
        
        # 환자 정보 (비식별화됨)
        metadata['patient_info'] = {
            'patient_id': getattr(ds, 'PatientID', 'ANONYMOUS'),
            'patient_name': str(getattr(ds, 'PatientName', 'ANONYMOUS^PATIENT')),
            'patient_birth_date': 'ANONYMIZED',  # 생년월일은 완전히 숨김
            'patient_sex': getattr(ds, 'PatientSex', 'Unknown'),  # 성별은 유지 (통계적 분석용)
            'patient_age': getattr(ds, 'PatientAge', 'Unknown')   # 나이는 유지 (의료적 중요성)
        }
        
        # 검사 정보 (날짜는 익명화됨)
        metadata['study_info'] = {
            'study_instance_uid': getattr(ds, 'StudyInstanceUID', 'Unknown'),
            'study_date': getattr(ds, 'StudyDate', 'Unknown'),
            'study_time': getattr(ds, 'StudyTime', 'Unknown'),
            'study_description': getattr(ds, 'StudyDescription', 'ANONYMIZED_STUDY'),
            'accession_number': 'ANONYMIZED'
        }
        
        # 시리즈 정보
        metadata['series_info'] = {
            'series_instance_uid': getattr(ds, 'SeriesInstanceUID', 'Unknown'),
            'series_number': getattr(ds, 'SeriesNumber', 'Unknown'),
            'series_description': getattr(ds, 'SeriesDescription', 'ANONYMIZED_SERIES'),
            'modality': getattr(ds, 'Modality', 'Unknown'),
            'body_part_examined': getattr(ds, 'BodyPartExamined', 'Unknown')
        }
        
        # 이미지 정보 (기술적 파라미터는 유지)
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
        
        # 기술적 정보 (의료진에게 필요한 정보는 유지)
        metadata['technical_info'] = {
            'bits_allocated': getattr(ds, 'BitsAllocated', 'Unknown'),
            'bits_stored': getattr(ds, 'BitsStored', 'Unknown'),
            'high_bit': getattr(ds, 'HighBit', 'Unknown'),
            'pixel_representation': getattr(ds, 'PixelRepresentation', 'Unknown'),
            'photometric_interpretation': getattr(ds, 'PhotometricInterpretation', 'Unknown'),
            'samples_per_pixel': getattr(ds, 'SamplesPerPixel', 'Unknown')
        }
        
        # 비식별화 정보 추가
        metadata['deidentification_info'] = {
            'deidentified': True,
            'deidentification_date': datetime.datetime.now().isoformat(),
            'method': 'DICOMDeidentifier_Simple',
            'removed_tags_count': len(self.TAGS_TO_REMOVE),
            'anonymized_dates': True,
            'anonymized_times': True
        }
        
        return metadata


def deidentify_dicom_directory(input_dir: str, output_dir: str, anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    디렉토리 내의 모든 DICOM 파일을 비식별화
    
    Args:
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 전체 처리 결과
    """
    deidentifier = DICOMDeidentifier(anonymous_prefix)
    
    results: Dict[str, Union[int, List[Dict[str, Any]]]] = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'file_results': []
    }
    
    # DICOM 파일 찾기
    dcm_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.dcm'):
                dcm_files.append(os.path.join(root, file))
    
    results['total_files'] = len(dcm_files)
    
    # 각 파일 처리
    file_results: List[Dict[str, Any]] = []
    successful_count = 0
    failed_count = 0
    
    for dcm_file in dcm_files:
        # 상대 경로 유지하여 출력 경로 생성
        rel_path = os.path.relpath(dcm_file, input_dir)
        output_file = os.path.join(output_dir, rel_path)
        
        # 비식별화 수행
        file_result = deidentifier.deidentify_file(dcm_file, output_file)
        file_results.append(file_result)
        
        if file_result['success']:
            successful_count += 1
        else:
            failed_count += 1
    
    results['file_results'] = file_results
    results['successful'] = successful_count
    results['failed'] = failed_count
    
    return results


def process_dicom_file(input_file_path: str, output_directory: str = "output/anonymized", anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    DICOM 파일을 비식별화하고 결과를 반환하는 메인 함수
    
    Args:
        input_file_path: 입력 DICOM 파일 경로
        output_directory: 출력 디렉토리 경로
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 비식별화 결과와 메타데이터
    """
    # 비식별화 객체 생성
    deidentifier = DICOMDeidentifier(anonymous_prefix)
    
    # 파일명 추출 및 출력 경로 생성
    filename = os.path.basename(input_file_path)
    name_without_ext = os.path.splitext(filename)[0]
    output_file_path = os.path.join(output_directory, f"anonymized_{filename}")
    
    # 비식별화 수행
    deidentification_result = deidentifier.deidentify_file(input_file_path, output_file_path)
    
    # 결과 구성
    result = {
        'success': deidentification_result['success'],
        'message': deidentification_result['message'],
        'input_file': input_file_path,
        'output_file': output_file_path if deidentification_result['success'] else None,
        'processing_info': {
            'removed_tags': deidentification_result['removed_tags'],
            'anonymized_tags': deidentification_result['anonymized_tags'],
            'removed_tags_count': len(deidentification_result['removed_tags']),
            'anonymized_tags_count': len(deidentification_result['anonymized_tags'])
        },
        'metadata': None
    }
    
    # 성공한 경우 메타데이터 추출
    if deidentification_result['success']:
        try:
            # 비식별화된 파일에서 메타데이터 추출
            anonymized_ds = pydicom.dcmread(output_file_path)
            result['metadata'] = deidentifier.extract_deidentified_metadata(anonymized_ds)
        except Exception as e:
            current_message = result['message']
            result['message'] = f"{current_message} (메타데이터 추출 실패: {str(e)})"
    
    return result


def process_multiple_dicom_files(input_files: List[str], output_directory: str = "output/anonymized", anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    여러 DICOM 파일을 비식별화하고 결과를 반환하는 함수
    
    Args:
        input_files: 입력 DICOM 파일 경로 리스트
        output_directory: 출력 디렉토리 경로
        anonymous_prefix: 익명 ID 접두사
        
    Returns:
        Dict: 전체 처리 결과
    """
    # 비식별화 객체 생성 (모든 파일에 대해 동일한 객체 사용)
    deidentifier = DICOMDeidentifier(anonymous_prefix)
    
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
        file_result = process_dicom_file(input_file, output_directory, anonymous_prefix)
        
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
            'removed_tags_count': file_result['processing_info']['removed_tags_count'],
            'anonymized_tags_count': file_result['processing_info']['anonymized_tags_count']
        })
    
    results['successful'] = successful_count
    results['failed'] = failed_count
    results['files'] = file_results
    
    return results


def deidentify_and_return_metadata(file_path: str, anonymous_prefix: str = "ANON") -> Dict[str, Any]:
    """
    DICOM 파일을 비식별화하고 메타데이터만 반환하는 함수 (파일 저장 안함)
    
    Args:
        file_path: DICOM 파일 경로
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
            'removed_tags': [],
            'anonymized_tags': [],
            'removed_tags_count': 0,
            'anonymized_tags_count': 0
        }
    }
    
    try:
        # 비식별화 객체 생성
        deidentifier = DICOMDeidentifier(anonymous_prefix)
        
        # 원본 DICOM 파일 읽기
        original_ds = pydicom.dcmread(file_path)
        
        # 원본 메타데이터 추출
        result['original_metadata'] = deidentifier.extract_deidentified_metadata(original_ds)
        
        # 제거될 태그들 확인
        removed_tags = []
        for tag_name in deidentifier.TAGS_TO_REMOVE:
            if hasattr(original_ds, tag_name):
                removed_tags.append(tag_name)
        
        # 익명화될 태그들 확인
        anonymized_tags = []
        for tag_name in deidentifier.DATE_TAGS + deidentifier.TIME_TAGS:
            if hasattr(original_ds, tag_name):
                anonymized_tags.append(tag_name)
        
        # 처리 정보 업데이트
        processing_info = result['processing_info']
        if isinstance(processing_info, dict):
            processing_info['removed_tags'] = removed_tags
            processing_info['anonymized_tags'] = anonymized_tags
            processing_info['removed_tags_count'] = len(removed_tags)
            processing_info['anonymized_tags_count'] = len(anonymized_tags)
        
        # 비식별화 수행 (메모리에서만)
        anonymized_ds = deidentifier.deidentify_dataset(original_ds.copy())
        
        # 비식별화된 메타데이터 추출
        result['anonymized_metadata'] = deidentifier.extract_deidentified_metadata(anonymized_ds)
        
        result['success'] = True
        result['message'] = '비식별화 및 메타데이터 추출 완료'
        
    except InvalidDicomError:
        result['message'] = '유효하지 않은 DICOM 파일'
    except Exception as e:
        result['message'] = f'처리 중 오류 발생: {str(e)}'
    
    return result


# 사용 예시
if __name__ == "__main__":
    # 1. 단일 파일 비식별화 (파일 저장)
    print("=== 단일 파일 비식별화 ===")
    result = process_dicom_file(
        "data/0002.DCM",
        "output/anonymized",
        "ANON"
    )
    print(f"성공: {result['success']}")
    print(f"메시지: {result['message']}")
    if result['success']:
        print(f"출력 파일: {result['output_file']}")
        print(f"제거된 태그 수: {result['processing_info']['removed_tags_count']}")
    print()
    
    # 2. 메타데이터만 추출 (파일 저장 안함)
    print("=== 메타데이터만 추출 ===")
    metadata_result = deidentify_and_return_metadata("data/0002.DCM", "ANON")
    print(f"성공: {metadata_result['success']}")
    print(f"메시지: {metadata_result['message']}")
    if metadata_result['success']:
        print(f"익명화된 환자 ID: {metadata_result['anonymized_metadata']['patient_info']['patient_id']}")
        print(f"제거된 태그 수: {metadata_result['processing_info']['removed_tags_count']}")
    print()
    
    # 3. 디렉토리 전체 비식별화
    print("=== 디렉토리 전체 비식별화 ===")
    dir_results = deidentify_dicom_directory(
        "data/",
        "output/anonymized/",
        "ANON"
    )
    print(f"전체 결과: {dir_results['successful']}/{dir_results['total_files']} 파일 성공")