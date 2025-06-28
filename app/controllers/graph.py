from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.dto.graph_dto import (
    CreateNodeRequest, CreateNodeResponse, UpdateNodeRequest, NodeResponse, EdgeResponse,
    BuildEdgesRequest, CenterEdgesRequest, SimilarityRequest, SimilarityResponse,
    ThresholdRequest, ThresholdResponse, GraphStatsResponse
)
from app.service.graph_service import get_graph_service, GraphService

router = APIRouter()


@router.post("/nodes", response_model=CreateNodeResponse, summary="노드 생성")
async def create_node(
    request: CreateNodeRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """새로운 노드를 생성합니다."""
    try:
        # ID 중복 확인
        existing_node = graph_service.get_node_by_id(request.id)
        if existing_node:
            raise HTTPException(status_code=409, detail=f"ID '{request.id}'가 이미 존재합니다")
        
        node_id = graph_service.create_node(
            node_id=request.id,
            name=request.name,
            datetime_obj=request.datetime,
            content=request.content
        )
        return CreateNodeResponse(
            id=node_id,
            message=f"노드 '{request.name}' (ID: {request.id}) 생성 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 생성 실패: {str(e)}")


@router.get("/nodes", response_model=List[NodeResponse], summary="모든 노드 조회")
async def get_all_nodes(
    graph_service: GraphService = Depends(get_graph_service)
):
    """모든 노드를 조회합니다."""
    try:
        nodes = graph_service.get_all_nodes()
        return [NodeResponse(**node) for node in nodes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 조회 실패: {str(e)}")


@router.get("/nodes/name/{node_name}", response_model=NodeResponse, summary="이름으로 노드 조회")
async def get_node_by_name(
    node_name: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """이름으로 노드를 조회합니다."""
    try:
        node = graph_service.get_node_by_name(node_name)
        if not node:
            raise HTTPException(status_code=404, detail=f"노드 '{node_name}'를 찾을 수 없습니다")
        return NodeResponse(**node)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 조회 실패: {str(e)}")


@router.get("/nodes/id/{node_id}", response_model=NodeResponse, summary="ID로 노드 조회")
async def get_node_by_id(
    node_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """ID로 노드를 조회합니다."""
    try:
        node = graph_service.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"ID '{node_id}'에 해당하는 노드를 찾을 수 없습니다")
        return NodeResponse(**node)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 조회 실패: {str(e)}")


@router.put("/nodes/name/{node_name}", response_model=dict, summary="이름으로 노드 내용 업데이트")
async def update_node_content_by_name(
    node_name: str,
    request: UpdateNodeRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """이름으로 노드의 내용을 업데이트합니다."""
    try:
        # 노드 존재 확인
        node = graph_service.get_node_by_name(node_name)
        if not node:
            raise HTTPException(status_code=404, detail=f"노드 '{node_name}'를 찾을 수 없습니다")
        
        graph_service.update_node_content(node_name, request.content)
        return {"message": f"노드 '{node_name}' 업데이트 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 업데이트 실패: {str(e)}")


@router.put("/nodes/id/{node_id}", response_model=dict, summary="ID로 노드 내용 업데이트")
async def update_node_content_by_id(
    node_id: str,
    request: UpdateNodeRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """ID로 노드의 내용을 업데이트합니다."""
    try:
        # 노드 존재 확인
        node = graph_service.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"ID '{node_id}'에 해당하는 노드를 찾을 수 없습니다")
        
        graph_service.update_node_content_by_id(node_id, request.content)
        return {"message": f"노드 ID '{node_id}' 업데이트 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 업데이트 실패: {str(e)}")


@router.delete("/nodes/name/{node_name}", response_model=dict, summary="이름으로 노드 삭제")
async def delete_node_by_name(
    node_name: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """이름으로 노드를 삭제합니다."""
    try:
        # 노드 존재 확인
        node = graph_service.get_node_by_name(node_name)
        if not node:
            raise HTTPException(status_code=404, detail=f"노드 '{node_name}'를 찾을 수 없습니다")
        
        graph_service.delete_node(node_name)
        return {"message": f"노드 '{node_name}' 삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 삭제 실패: {str(e)}")


@router.delete("/nodes/id/{node_id}", response_model=dict, summary="ID로 노드 삭제")
async def delete_node_by_id(
    node_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """ID로 노드를 삭제합니다."""
    try:
        # 노드 존재 확인
        node = graph_service.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"ID '{node_id}'에 해당하는 노드를 찾을 수 없습니다")
        
        graph_service.delete_node_by_id(node_id)
        return {"message": f"노드 ID '{node_id}' 삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노드 삭제 실패: {str(e)}")


@router.get("/edges", response_model=List[EdgeResponse], summary="모든 엣지 조회")
async def get_all_edges(
    graph_service: GraphService = Depends(get_graph_service)
):
    """모든 엣지를 조회합니다."""
    try:
        edges = graph_service.get_all_edges()
        result = []
        for edge in edges:
            edge_response = EdgeResponse(
                from_node=edge.get("from"),
                to_node=edge.get("to"),
                type=edge.get("type"),
                score=edge.get("score"),
                embedding1_dim=edge.get("embedding1_dim"),
                embedding2_dim=edge.get("embedding2_dim")
            )
            result.append(edge_response)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엣지 조회 실패: {str(e)}")


@router.post("/edges/similarity", response_model=dict, summary="유사도 기반 엣지 생성")
async def build_similarity_edges(
    request: BuildEdgesRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """유사도 기반으로 엣지를 생성합니다."""
    try:
        if len(request.working_set) < 2:
            raise HTTPException(status_code=400, detail="working_set에 최소 2개의 노드가 필요합니다")
        
        graph_service.build_similarity_edges(request.working_set)
        return {"message": f"유사도 기반 엣지 생성 완료 (노드 수: {len(request.working_set)})"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엣지 생성 실패: {str(e)}")


@router.post("/edges/same-date", response_model=dict, summary="같은 날짜 엣지 생성")
async def build_same_date_edges(
    graph_service: GraphService = Depends(get_graph_service)
):
    """같은 날짜의 노드들 간에 엣지를 생성합니다."""
    try:
        graph_service.build_same_date_edges()
        return {"message": "같은 날짜 엣지 생성 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엣지 생성 실패: {str(e)}")


@router.post("/edges/center-same-date", response_model=dict, summary="중심 노드 기준 같은 날짜 엣지 생성")
async def build_center_same_date_edges(
    request: CenterEdgesRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """중심 노드와 HAS_RELATION으로 연결된 노드들 중 같은 날짜인 경우 IS_SAMEDATE 엣지를 생성합니다."""
    try:
        # 중심 노드 존재 확인
        node = graph_service.get_node_by_name(request.center_node_name)
        if not node:
            raise HTTPException(status_code=404, detail=f"중심 노드 '{request.center_node_name}'를 찾을 수 없습니다")
        
        graph_service.build_center_same_date_edges(request.center_node_name)
        return {"message": f"중심 노드 '{request.center_node_name}' 기준 같은 날짜 엣지 생성 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엣지 생성 실패: {str(e)}")


@router.post("/similarity", response_model=SimilarityResponse, summary="두 노드간 유사도 계산")
async def calculate_similarity(
    request: SimilarityRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """두 노드 간의 유사도를 계산합니다."""
    try:
        # 노드 존재 확인
        node1 = graph_service.get_node_by_name(request.node1_name)
        node2 = graph_service.get_node_by_name(request.node2_name)
        
        if not node1:
            raise HTTPException(status_code=404, detail=f"노드 '{request.node1_name}'를 찾을 수 없습니다")
        if not node2:
            raise HTTPException(status_code=404, detail=f"노드 '{request.node2_name}'를 찾을 수 없습니다")
        
        similarity = graph_service.calculate_similarity(request.node1_name, request.node2_name)
        return SimilarityResponse(similarity_score=similarity)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유사도 계산 실패: {str(e)}")


@router.get("/threshold", response_model=ThresholdResponse, summary="현재 임계값 조회")
async def get_threshold(
    graph_service: GraphService = Depends(get_graph_service)
):
    """현재 설정된 임계값을 조회합니다."""
    try:
        threshold = graph_service.get_threshold()
        return ThresholdResponse(threshold=threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임계값 조회 실패: {str(e)}")


@router.put("/threshold", response_model=dict, summary="임계값 설정")
async def set_threshold(
    request: ThresholdRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """엣지 생성을 위한 임계값을 설정합니다."""
    try:
        if not 0.0 <= request.threshold <= 1.0:
            raise HTTPException(status_code=400, detail="임계값은 0.0과 1.0 사이여야 합니다")
        
        graph_service.set_threshold(request.threshold)
        return {"message": f"임계값을 {request.threshold}로 설정했습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임계값 설정 실패: {str(e)}")


@router.get("/stats", response_model=GraphStatsResponse, summary="그래프 통계 조회")
async def get_graph_stats(
    graph_service: GraphService = Depends(get_graph_service)
):
    """그래프의 통계 정보를 조회합니다."""
    try:
        nodes = graph_service.get_all_nodes()
        edges = graph_service.get_all_edges()
        
        has_relation_edges = [e for e in edges if e.get("type") == "HAS_RELATION"]
        same_date_edges = [e for e in edges if e.get("type") == "IS_SAMEDATE"]
        
        return GraphStatsResponse(
            total_nodes=len(nodes),
            total_edges=len(edges),
            has_relation_edges=len(has_relation_edges),
            same_date_edges=len(same_date_edges)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.delete("/data", response_model=dict, summary="모든 데이터 삭제 (테스트용)")
async def clear_all_data(
    graph_service: GraphService = Depends(get_graph_service)
):
    """모든 노드와 엣지를 삭제합니다. 주의: 복구 불가능합니다."""
    try:
        graph_service.clear_all_data()
        return {"message": "모든 그래프 데이터가 삭제되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 삭제 실패: {str(e)}") 