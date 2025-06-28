import asyncio
import requests
from datetime import datetime

# 백엔드 서버 URL
BASE_URL = "http://localhost:8000/graph"

def test_graph_api():
    """Graph API 기능 테스트"""
    
    print("🧪 Graph API 테스트 시작\n")
    
    # 1. 모든 데이터 초기화
    print("1. 모든 데이터 초기화...")
    response = requests.delete(f"{BASE_URL}/data")
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    # 2. 노드 생성
    print("2. 테스트 노드들 생성...")
    test_nodes = [
        {
            "id": "node_001",
            "name": "두통_진료",
            "datetime": "2024-01-15T09:30:00",
            "content": "환자가 심한 두통을 호소. 편두통 가능성 높음. 진통제 처방."
        },
        {
            "id": "node_002",
            "name": "혈압_검사",
            "datetime": "2024-01-15T10:00:00", 
            "content": "혈압 측정 결과 140/90. 고혈압 경계선. 정기 모니터링 필요."
        },
        {
            "id": "node_003",
            "name": "소화불량_상담",
            "datetime": "2024-01-16T14:30:00",
            "content": "식후 소화불량 증상. 위산억제제 처방 및 식이요법 권유."
        },
        {
            "id": "node_004",
            "name": "당뇨_관리",
            "datetime": "2024-01-16T15:00:00",
            "content": "혈당 수치 관리 상담. 인슐린 투여량 조정 필요."
        }
    ]
    
    created_node_ids = ["node_001", "node_002", "node_003", "node_004"]
    for node in test_nodes:
        response = requests.post(f"{BASE_URL}/nodes", json=node)
        print(f"   {node['name']} (ID: {node['id']}): {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"      응답: {result['message']}")
        else:
            print(f"      오류: {response.json()}")
    print()
    
    # 3. 노드 조회
    print("3. 생성된 노드들 조회...")
    response = requests.get(f"{BASE_URL}/nodes")
    if response.status_code == 200:
        nodes = response.json()
        print(f"   총 {len(nodes)}개 노드:")
        for node in nodes:
            print(f"   - {node['name']} (ID: {node['id'][:8]}...): {node['datetime']}")
    print()
    
    # 3-1. ID로 노드 조회 테스트
    if created_node_ids:
        print("3-1. ID로 노드 조회 테스트...")
        test_id = created_node_ids[0]
        response = requests.get(f"{BASE_URL}/nodes/id/{test_id}")
        if response.status_code == 200:
            node = response.json()
            print(f"   ID {test_id}로 조회된 노드: {node['name']}")
        else:
            print(f"   ID 조회 실패: {response.status_code}")
        print()
    
    # 3-2. 중복 ID 생성 테스트
    print("3-2. 중복 ID 생성 테스트...")
    duplicate_node = {
        "id": "node_001",  # 이미 존재하는 ID
        "name": "중복_테스트",
        "datetime": "2024-01-17T10:00:00",
        "content": "중복 ID로 노드 생성 시도"
    }
    response = requests.post(f"{BASE_URL}/nodes", json=duplicate_node)
    print(f"   상태: {response.status_code} (409 Conflict 예상)")
    if response.status_code == 409:
        print(f"   응답: {response.json()}")
        print("   ✅ 중복 ID 검증 성공")
    else:
        print(f"   ❌ 예상과 다른 응답: {response.json()}")
    print()
    
    # 4. 유사도 계산
    print("4. 두 노드간 유사도 계산...")
    similarity_request = {
        "node1_name": "두통_진료",
        "node2_name": "혈압_검사"
    }
    response = requests.post(f"{BASE_URL}/similarity", json=similarity_request)
    if response.status_code == 200:
        result = response.json()
        print(f"   유사도 점수: {result['similarity_score']:.4f}")
    print()
    
    # 5. 임계값 설정
    print("5. 유사도 임계값 설정...")
    threshold_request = {"threshold": 0.7}
    response = requests.put(f"{BASE_URL}/threshold", json=threshold_request)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    # 6. 유사도 기반 엣지 생성
    print("6. 유사도 기반 엣지 생성...")
    edges_request = {
        "working_set": ["두통_진료", "혈압_검사", "소화불량_상담", "당뇨_관리"]
    }
    response = requests.post(f"{BASE_URL}/edges/similarity", json=edges_request)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    # 7. 같은 날짜 엣지 생성
    print("7. 같은 날짜 엣지 생성...")
    response = requests.post(f"{BASE_URL}/edges/same-date")
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    # 8. 모든 엣지 조회
    print("8. 생성된 엣지들 조회...")
    response = requests.get(f"{BASE_URL}/edges")
    if response.status_code == 200:
        edges = response.json()
        print(f"   총 {len(edges)}개 엣지:")
        for edge in edges:
            print(f"   - {edge['from_node']} -> {edge['to_node']} ({edge['type']})")
            if edge.get('score'):
                print(f"     유사도: {edge['score']:.4f}")
    print()
    
    # 9. 그래프 통계
    print("9. 그래프 통계 조회...")
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   총 노드: {stats['total_nodes']}개")
        print(f"   총 엣지: {stats['total_edges']}개")
        print(f"   유사도 엣지: {stats['has_relation_edges']}개")
        print(f"   같은날짜 엣지: {stats['same_date_edges']}개")
    print()
    
    # 10. 노드 수정 테스트 (이름으로)
    print("10. 노드 내용 수정 (이름으로)...")
    update_request = {
        "content": "두통 증상이 호전됨. 추가 치료 불요."
    }
    response = requests.put(f"{BASE_URL}/nodes/name/두통_진료", json=update_request)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    # 10-1. 노드 수정 테스트 (ID로)
    if created_node_ids:
        print("10-1. 노드 내용 수정 (ID로)...")
        update_request = {
            "content": "ID로 업데이트된 내용입니다."
        }
        test_id = created_node_ids[1] if len(created_node_ids) > 1 else created_node_ids[0]
        response = requests.put(f"{BASE_URL}/nodes/id/{test_id}", json=update_request)
        print(f"   상태: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
        print()
    
    # 11. 특정 노드 조회 (이름으로)
    print("11. 수정된 노드 조회 (이름으로)...")
    response = requests.get(f"{BASE_URL}/nodes/name/두통_진료")
    if response.status_code == 200:
        node = response.json()
        print(f"   노드ID: {node['id'][:8]}...")
        print(f"   노드명: {node['name']}")
        print(f"   날짜: {node['datetime']}")
        print(f"   내용: {node['content']}")
    print()
    
    # 11-1. 특정 노드 조회 (ID로)
    if created_node_ids:
        print("11-1. 수정된 노드 조회 (ID로)...")
        test_id = created_node_ids[1] if len(created_node_ids) > 1 else created_node_ids[0]
        response = requests.get(f"{BASE_URL}/nodes/id/{test_id}")
        if response.status_code == 200:
            node = response.json()
            print(f"   노드ID: {node['id'][:8]}...")
            print(f"   노드명: {node['name']}")
            print(f"   날짜: {node['datetime']}")
            print(f"   내용: {node['content']}")
        print()
    
    # 12. 중심 노드 기준 같은 날짜 엣지 생성
    print("12. 중심 노드 기준 같은 날짜 엣지 생성...")
    center_request = {"center_node_name": "두통_진료"}
    response = requests.post(f"{BASE_URL}/edges/center-same-date", json=center_request)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
    print()
    
    print("✅ Graph API 테스트 완료!")

if __name__ == "__main__":
    try:
        test_graph_api()
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.")
        print("   서버 실행: python server.py")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}") 