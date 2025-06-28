from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CreateNodeRequest(BaseModel):
    """노드 생성 요청"""
    id: str
    name: str
    datetime: datetime
    content: str


class CreateNodeResponse(BaseModel):
    """노드 생성 응답"""
    id: str
    message: str


class UpdateNodeRequest(BaseModel):
    """노드 업데이트 요청"""
    content: str


class NodeResponse(BaseModel):
    """노드 응답"""
    id: str
    name: str
    datetime: str
    content: str


class EdgeResponse(BaseModel):
    """엣지 응답"""
    from_node: str = None
    to_node: str = None
    type: str  # HAS_RELATION 또는 IS_SAMEDATE
    score: Optional[float] = None
    embedding1_dim: Optional[int] = None
    embedding2_dim: Optional[int] = None


class BuildEdgesRequest(BaseModel):
    """엣지 생성 요청"""
    working_set: List[str]


class CenterEdgesRequest(BaseModel):
    """중심 노드 기준 엣지 생성 요청"""
    center_node_name: str


class SimilarityRequest(BaseModel):
    """유사도 계산 요청"""
    node1_name: str
    node2_name: str


class SimilarityResponse(BaseModel):
    """유사도 계산 응답"""
    similarity_score: float


class ThresholdRequest(BaseModel):
    """임계값 설정 요청"""
    threshold: float


class ThresholdResponse(BaseModel):
    """임계값 조회 응답"""
    threshold: float


class GraphStatsResponse(BaseModel):
    """그래프 통계 응답"""
    total_nodes: int
    total_edges: int
    has_relation_edges: int
    same_date_edges: int 