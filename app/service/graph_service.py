from datetime import datetime
from typing import List, Optional
from app.service.graph.graph import GraphDB, NodeDTO


class GraphService:
    """Graph 데이터베이스 서비스"""
    
    def __init__(self):
        self.graph_db = GraphDB()
    
    def __del__(self):
        """소멸자에서 연결 종료"""
        if hasattr(self, 'graph_db'):
            self.graph_db.close()
    
    # Node CRUD
    def create_node(self, node_id: str, name: str, datetime_obj: datetime, content: str):
        """노드 생성"""
        return self.graph_db.create_node(node_id, name, datetime_obj, content)
    
    def create_node_from_dto(self, node_dto: NodeDTO):
        """DTO로 노드 생성"""
        return self.graph_db.create_node_from_dto(node_dto)
    
    def get_all_nodes(self) -> List[dict]:
        """모든 노드 조회"""
        return self.graph_db.read_all_nodes()
    
    def get_all_nodes_as_dto(self) -> List[NodeDTO]:
        """모든 노드를 DTO로 조회"""
        return self.graph_db.read_all_nodes_as_dto()
    
    def get_node_by_name(self, name: str) -> Optional[dict]:
        """이름으로 노드 조회"""
        return self.graph_db.get_node_by_name(name)
    
    def get_node_by_id(self, node_id: str) -> Optional[dict]:
        """ID로 노드 조회"""
        return self.graph_db.get_node_by_id(node_id)
    
    def update_node_content(self, name: str, new_content: str):
        """노드 내용 업데이트 (이름으로)"""
        return self.graph_db.update_node_content(name, new_content)
    
    def update_node_content_by_id(self, node_id: str, new_content: str):
        """노드 내용 업데이트 (ID로)"""
        return self.graph_db.update_node_content_by_id(node_id, new_content)
    
    def delete_node(self, name: str):
        """노드 삭제 (이름으로)"""
        return self.graph_db.delete_node(name)
    
    def delete_node_by_id(self, node_id: str):
        """노드 삭제 (ID로)"""
        return self.graph_db.delete_node_by_id(node_id)
    
    # Edge 관련
    def get_all_edges(self) -> List[dict]:
        """모든 엣지 조회"""
        return self.graph_db.get_all_edges()
    
    def build_similarity_edges(self, working_set: List[str]):
        """유사도 기반 엣지 생성"""
        return self.graph_db.build_edges(working_set)
    
    def build_same_date_edges(self):
        """같은 날짜 엣지 생성"""
        return self.graph_db.build_samedate_edges()
    
    def build_center_same_date_edges(self, center_node_name: str):
        """중심 노드 기준 같은 날짜 엣지 생성"""
        return self.graph_db.build_samedate_with_center(center_node_name)
    
    # 임베딩 관련
    def calculate_similarity(self, node1_name: str, node2_name: str) -> float:
        """두 노드간 유사도 계산"""
        node1 = self.get_node_by_name(node1_name)
        node2 = self.get_node_by_name(node2_name)
        
        if not node1 or not node2:
            return 0.0
        
        score, _, _ = self.graph_db.cal_embed(node1, node2)
        return score
    
    # 유틸리티
    def clear_all_data(self):
        """모든 데이터 삭제 (테스트용)"""
        return self.graph_db.clear_all_data()
    
    def get_threshold(self) -> float:
        """현재 임계값 조회"""
        return self.graph_db.threshold
    
    def set_threshold(self, threshold: float):
        """임계값 설정"""
        self.graph_db.threshold = threshold


# 의존성 주입을 위한 인스턴스
_graph_service = None

def get_graph_service() -> GraphService:
    """GraphService 싱글톤 인스턴스 반환"""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service 