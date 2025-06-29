from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from app.dto.graph_dto import (
    CreateNodeRequest, CreateNodeResponse, UpdateNodeRequest, NodeResponse, EdgeResponse,
    CenterEdgesRequest, SimilarityRequest, SimilarityResponse,
    ThresholdRequest, ThresholdResponse, GraphStatsResponse
)
from app.service.graph_service import get_graph_service, GraphService
# from app.service.postgres.medicalhistorymanage import get_all_medicalhistories
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/nodes/{node_id}", response_model=NodeResponse, summary="ID로 노드 조회")
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


@router.put("/nodes/{node_id}", response_model=dict, summary="ID로 노드 내용 업데이트")
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


@router.delete("/nodes/{node_id}", response_model=dict, summary="ID로 노드 삭제")
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
    graph_service: GraphService = Depends(get_graph_service)
):
    """모든 노드를 대상으로 유사도 기반 엣지를 생성합니다."""
    try:
        # 모든 노드 조회
        nodes = graph_service.get_all_nodes()
        if len(nodes) < 2:
            raise HTTPException(status_code=400, detail="유사도 엣지 생성을 위해 최소 2개의 노드가 필요합니다")
        
        # 노드 ID 리스트 추출
        node_ids = [node["id"] for node in nodes]
        
        graph_service.build_similarity_edges(node_ids)
        return {"message": f"유사도 기반 엣지 생성 완료 (노드 수: {len(node_ids)})"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엣지 생성 실패: {str(e)}")


@router.post("/edges/similarity/center/{node_id}", response_model=dict, summary="중심 노드 기준 유사도 엣지 생성")
async def build_similarity_edges_with_center(
    node_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """지정된 노드를 중심으로 모든 노드와 유사도 기반 엣지를 생성합니다."""
    try:
        # 중심 노드 존재 확인
        center_node = graph_service.get_node_by_id(node_id)
        if not center_node:
            raise HTTPException(status_code=404, detail=f"중심 노드 ID '{node_id}'를 찾을 수 없습니다")
        
        # 모든 노드 조회
        nodes = graph_service.get_all_nodes()
        if len(nodes) < 2:
            raise HTTPException(status_code=400, detail="유사도 엣지 생성을 위해 최소 2개의 노드가 필요합니다")
        
        # 노드 ID 리스트 추출
        all_node_ids = [node["id"] for node in nodes]
        
        # 중심 노드가 리스트에 있는지 확인
        if node_id not in all_node_ids:
            raise HTTPException(status_code=404, detail=f"중심 노드 ID '{node_id}'가 그래프에 존재하지 않습니다")
        
        # 중심 노드를 첫 번째로 배치하고 나머지 노드들을 추가
        reordered_node_ids = [node_id]
        for nid in all_node_ids:
            if nid != node_id:
                reordered_node_ids.append(nid)
        
        graph_service.build_similarity_edges(reordered_node_ids)
        return {
            "message": f"중심 노드 '{center_node['name']}' (ID: {node_id}) 기준 유사도 엣지 생성 완료",
            "center_node_id": node_id,
            "center_node_name": center_node["name"],
            "total_comparisons": len(reordered_node_ids) - 1
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중심 노드 기준 엣지 생성 실패: {str(e)}")


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
        node = graph_service.get_node_by_id(request.center_node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"중심 노드 ID '{request.center_node_id}'를 찾을 수 없습니다")
        
        graph_service.build_center_same_date_edges_by_id(request.center_node_id)
        return {"message": f"중심 노드 ID '{request.center_node_id}' 기준 같은 날짜 엣지 생성 완료"}
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
        node1 = graph_service.get_node_by_id(request.node1_id)
        node2 = graph_service.get_node_by_id(request.node2_id)
        
        if not node1:
            raise HTTPException(status_code=404, detail=f"노드 ID '{request.node1_id}'를 찾을 수 없습니다")
        if not node2:
            raise HTTPException(status_code=404, detail=f"노드 ID '{request.node2_id}'를 찾을 수 없습니다")
        
        similarity = graph_service.calculate_similarity_by_id(request.node1_id, request.node2_id)
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


@router.post("/sync/medical-histories", response_model=dict, summary="Medical History를 Neo4j 노드로 동기화")
async def sync_medical_histories_to_graph(
    graph_service: GraphService = Depends(get_graph_service),
    db: AsyncSession = Depends(get_db)
):
    """medical_history 테이블에서 데이터를 읽어서 새로운 것들을 Neo4j 노드로 추가합니다."""
    try:
        # medical_history 테이블에서 모든 데이터 조회
        result = await get_all_medicalhistories(db)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"Medical history 조회 실패: {result['error']}")
        
        medical_histories = result["medical_histories"]
        if not medical_histories:
            return {"message": "동기화할 medical history 데이터가 없습니다", "added_count": 0, "skipped_count": 0}
        
        added_count = 0
        skipped_count = 0
        
        for history in medical_histories:
            # 이미 Neo4j에 존재하는지 확인
            existing_node = graph_service.get_node_by_id(history["medicalhistory_id"])
            if existing_node:
                skipped_count += 1
                continue
            
            # 새로운 노드 생성
            # datetime 문자열을 datetime 객체로 변환
            datetime_obj = datetime.fromisoformat(history["medicalhistory_date"])
            
            # content는 제목과 내용을 합쳐서 구성
            content = f"{history['medicalhistory_title']}\n\n{history['medicalhistory_content']}"
            if history.get('tags'):
                content += f"\n\nTags: {', '.join(history['tags'])}"
            
            graph_service.create_node(
                node_id=history["medicalhistory_id"],
                name=history["medicalhistory_title"],
                datetime_obj=datetime_obj,
                content=content
            )
            added_count += 1
        
        return {
            "message": f"Medical history 동기화 완료",
            "total_records": len(medical_histories),
            "added_count": added_count,
            "skipped_count": skipped_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Medical history 동기화 실패: {str(e)}")


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