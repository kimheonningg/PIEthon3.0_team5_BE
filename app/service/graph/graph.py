from neo4j import GraphDatabase
from datetime import datetime
import random
import math
import numpy as np
from openai import OpenAI
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class NodeDTO:
    """노드 데이터 전송 객체"""
    name: str
    datetime_obj: datetime
    content: str
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "datetime": self.datetime_obj.isoformat(),
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """딕셔너리에서 생성"""
        return cls(
            name=data["name"],
            datetime_obj=datetime.fromisoformat(data["datetime"]),
            content=data["content"]
        )

class GraphDB:
    def __init__(self, uri=None, user=None, password=None, threshold=0.7):
        # 기본 원격 저장소 연결 정보
        if uri is None:
            uri = "neo4j+ssc://2a6c80b9.databases.neo4j.io"
        if user is None:
            user = "neo4j"
        if password is None:
            password = "8v30FR1TEgc51CEkKYVcsM-40GkqP4DvXsFxU5kdQDA"
            
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.threshold = threshold
        self.client = OpenAI(api_key="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")  # OpenAI 클라이언트 초기화

    def close(self):
        self.driver.close()

    def create_node_from_dto(self, node_dto: NodeDTO):
        """DTO를 사용하여 노드 생성"""
        self.create_node(node_dto.name, node_dto.datetime_obj, node_dto.content)

    def create_node(self, name, datetime_obj, content):
        """새로운 노드 생성"""
        with self.driver.session() as session:
            session.run(
                "CREATE (n:Node {name: $name, datetime: $datetime, content: $content})",
                name=name,
                datetime=datetime_obj.isoformat(),
                content=content
            )

    def read_all_nodes_as_dto(self) -> List[NodeDTO]:
        """모든 노드를 DTO 리스트로 조회"""
        nodes = self.read_all_nodes()
        return [NodeDTO.from_dict(node) for node in nodes]

    def read_all_nodes(self):
        """모든 노드 조회"""
        with self.driver.session() as session:
            result = session.run("MATCH (n:Node) RETURN n.name AS name, n.datetime AS datetime, n.content AS content")
            return [{
                "name": record["name"], 
                "datetime": record["datetime"], 
                "content": record["content"]
            } for record in result]

    def update_node_content(self, name, new_content):
        """노드 콘텐츠 업데이트"""
        with self.driver.session() as session:
            session.run(
                "MATCH (n:Node {name: $name}) SET n.content = $new_content",
                name=name,
                new_content=new_content
            )

    def delete_node(self, name):
        """노드 삭제"""
        with self.driver.session() as session:
            session.run("MATCH (n:Node {name: $name}) DETACH DELETE n", name=name)

    def create_edge(self, name1, name2, score, embedding1=None, embedding2=None):
        """두 노드 간 엣지 생성 (임베딩 정보 포함)"""
        with self.driver.session() as session:
            # 기본 엣지 속성
            edge_properties = {"score": score}
            
            # 임베딩 벡터가 제공된 경우 추가 (선택사항)
            if embedding1 is not None:
                edge_properties["embedding1"] = embedding1
            if embedding2 is not None:
                edge_properties["embedding2"] = embedding2
                
            session.run("""
                MATCH (a:Node {name: $name1}), (b:Node {name: $name2})
                MERGE (a)-[r:HAS_RELATION]->(b)
                SET r += $properties
            """, name1=name1, name2=name2, properties=edge_properties)

    def create_samedate_edge(self, name1, name2):
        """같은 날짜 노드 간 무방향 엣지 생성"""
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Node {name: $name1}), (b:Node {name: $name2})
                MERGE (a)-[:IS_SAMEDATE]-(b)
            """, name1=name1, name2=name2)

    def get_embedding(self, text, model="text-embedding-3-small"):
        """OpenAI API를 사용하여 텍스트 임베딩 생성"""
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=model).data[0].embedding

    def cosine_similarity(self, vec1, vec2):
        """두 벡터 간의 코사인 유사도 계산"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 코사인 유사도 계산: (A · B) / (||A|| × ||B||)
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        
        similarity = dot_product / (norm_vec1 * norm_vec2)
        return similarity

    def cal_embed(self, node1, node2):
        """
        두 노드 간의 유사도 점수 계산 (OpenAI 임베딩 기반)
        임베딩 벡터와 유사도 점수를 함께 반환
        """
        content1 = node1.get('content', '')
        content2 = node2.get('content', '')
        
        if not content1.strip() or not content2.strip():
            return 0.0, None, None
        
        try:
            # 각 노드의 콘텐츠에 대한 임베딩 생성
            embedding1 = self.get_embedding(content1)
            embedding2 = self.get_embedding(content2)
            
            # 코사인 유사도 계산
            similarity = self.cosine_similarity(embedding1, embedding2)
            
            # 코사인 유사도는 -1에서 1 사이의 값이므로 0에서 1 사이로 정규화
            normalized_similarity = (similarity + 1) / 2
            score = max(0.0, min(1.0, normalized_similarity))
            
            return score, embedding1, embedding2
            
        except Exception as e:
            print(f"임베딩 계산 중 오류 발생: {e}")
            # 오류 발생 시 기본값 반환
            return 0.0, None, None

    def get_node_by_name(self, name):
        """이름으로 노드 조회"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n:Node {name: $name}) RETURN n.name AS name, n.datetime AS datetime, n.content AS content",
                name=name
            )
            record = result.single()
            if record:
                return {
                    "name": record["name"],
                    "datetime": record["datetime"],
                    "content": record["content"]
                }
            return None

    def build_edges(self, working_set):
        """
        첫 번째 노드를 고정하고 나머지 모든 노드들과 비교하여 엣지를 구성하는 함수
        working_set: 노드 이름들의 리스트
        """
        if len(working_set) < 2:
            print("working_set에 최소 2개의 노드가 필요합니다.")
            return
        
        print(f"엣지 구축 시작 - working_set: {working_set}")
        print(f"threshold: {self.threshold}")
        print(f"첫 번째 노드 '{working_set[0]}'를 고정하고 나머지 모든 노드들과 비교합니다.")
        
        # 첫 번째 노드 고정
        first_node_name = working_set[0]
        first_node = self.get_node_by_name(first_node_name)
        
        if first_node is None:
            print(f"첫 번째 노드를 찾을 수 없습니다: {first_node_name}")
            return
        
        # 나머지 모든 노드들과 비교
        for i in range(1, len(working_set)):
            second_node_name = working_set[i]
            second_node = self.get_node_by_name(second_node_name)
            
            if second_node is None:
                print(f"노드를 찾을 수 없습니다: {second_node_name}")
                continue
            
            # 유사도 점수와 임베딩 벡터 계산
            score, embedding1, embedding2 = self.cal_embed(first_node, second_node)
            print(f"({first_node_name}, {second_node_name}) 점수: {score:.3f}")
            
            if score >= self.threshold:
                # 엣지 생성 (임베딩 벡터 포함)
                self.create_edge(first_node_name, second_node_name, score, embedding1, embedding2)
                print(f"✓ 엣지 생성: {first_node_name} -> {second_node_name} (점수: {score:.3f})")
                if embedding1 is not None and embedding2 is not None:
                    print(f"  임베딩 벡터도 저장됨 (차원: {len(embedding1)})")
            else:
                print(f"✗ 임계값 미달: {first_node_name} -> {second_node_name} (점수: {score:.3f})")
        
        print("엣지 구축 완료")

    def build_samedate_edges(self):
        """같은 날짜의 노드들 간에 IS_SAMEDATE 엣지를 생성"""
        print("\n=== IS_SAMEDATE 엣지 구축 시작 ===")
        
        with self.driver.session() as session:
            # 모든 노드의 날짜 정보 조회
            result = session.run("""
                MATCH (n:Node) 
                RETURN n.name AS name, n.datetime AS datetime
                ORDER BY n.datetime
            """)
            
            nodes_by_date = {}
            for record in result:
                node_name = record["name"]
                node_datetime = record["datetime"]
                
                # datetime에서 날짜 부분만 추출
                if node_datetime:
                    date_part = node_datetime.split('T')[0]  # YYYY-MM-DD 부분만
                    
                    if date_part not in nodes_by_date:
                        nodes_by_date[date_part] = []
                    nodes_by_date[date_part].append(node_name)
            
            # 같은 날짜에 2개 이상의 노드가 있는 경우 엣지 생성
            for date, node_names in nodes_by_date.items():
                if len(node_names) >= 2:
                    print(f"날짜 {date}에 {len(node_names)}개 노드: {node_names}")
                    
                    # 모든 노드 쌍에 대해 IS_SAMEDATE 엣지 생성
                    for i in range(len(node_names)):
                        for j in range(i + 1, len(node_names)):
                            self.create_samedate_edge(node_names[i], node_names[j])
                            print(f"  ✓ IS_SAMEDATE 엣지: {node_names[i]} <-> {node_names[j]}")
                else:
                    print(f"날짜 {date}에 1개 노드: {node_names[0]} (엣지 생성 안함)")
        
        print("IS_SAMEDATE 엣지 구축 완료")

    def clear_all_data(self):
        """모든 데이터 삭제 (테스트용)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("모든 데이터가 삭제되었습니다.")

    def get_all_edges(self):
        """모든 엣지 조회 (HAS_RELATION과 IS_SAMEDATE 포함)"""
        with self.driver.session() as session:
            edges = []
            
            # HAS_RELATION 엣지 조회
            result = session.run("""
                MATCH (a:Node)-[r:HAS_RELATION]->(b:Node) 
                RETURN a.name AS from_node, b.name AS to_node, r.score AS score,
                       r.embedding1 AS embedding1, r.embedding2 AS embedding2, 'HAS_RELATION' AS rel_type
            """)
            
            for record in result:
                edge_info = {
                    "from": record["from_node"],
                    "to": record["to_node"], 
                    "type": record["rel_type"],
                    "score": record["score"]
                }
                
                # 임베딩 정보가 있는 경우 추가
                if record["embedding1"] is not None:
                    edge_info["embedding1_dim"] = len(record["embedding1"])
                if record["embedding2"] is not None:
                    edge_info["embedding2_dim"] = len(record["embedding2"])
                    
                edges.append(edge_info)
            
            # IS_SAMEDATE 엣지 조회 (무방향이므로 양방향 모두 조회)
            result = session.run("""
                MATCH (a:Node)-[r:IS_SAMEDATE]-(b:Node) 
                WHERE ID(a) < ID(b)
                RETURN a.name AS from_node, b.name AS to_node, 'IS_SAMEDATE' AS rel_type
            """)
            
            for record in result:
                edge_info = {
                    "from": record["from_node"],
                    "to": record["to_node"], 
                    "type": record["rel_type"],
                    "score": None  # IS_SAMEDATE는 점수가 없음
                }
                edges.append(edge_info)
            
            return edges

    def build_samedate_with_center(self, center_node_name):
        """
        중심 노드와 HAS_RELATION으로 연결된 모든 노드에 대해
        같은 날짜면 IS_SAMEDATE 엣지를 추가
        """
        print(f"\n=== 중심 노드({center_node_name}) 기준 IS_SAMEDATE 엣지 추가 ===")
        with self.driver.session() as session:
            # 중심 노드의 날짜 조회
            result = session.run(
                "MATCH (n:Node {name: $center}) RETURN n.datetime AS datetime",
                center=center_node_name
            )
            record = result.single()
            if not record or not record["datetime"]:
                print("중심 노드의 날짜 정보를 찾을 수 없습니다.")
                return
            center_date = record["datetime"].split('T')[0]

            # HAS_RELATION으로 연결된 모든 노드 조회
            result = session.run(
                """
                MATCH (a:Node {name: $center})-[r:HAS_RELATION]->(b:Node)
                RETURN b.name AS name, b.datetime AS datetime
                """,
                center=center_node_name
            )
            for rec in result:
                other_name = rec["name"]
                other_datetime = rec["datetime"]
                if not other_datetime:
                    continue
                other_date = other_datetime.split('T')[0]
                if other_date == center_date:
                    self.create_samedate_edge(center_node_name, other_name)
                    print(f"  ✓ IS_SAMEDATE 엣지: {center_node_name} <-> {other_name}")
        print("중심 노드 기준 IS_SAMEDATE 엣지 추가 완료")


