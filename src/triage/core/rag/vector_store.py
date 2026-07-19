import uuid
import json
from dataclasses import dataclass
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from typing import Optional, Any

from triage.config import Settings

@dataclass
class ExpertiseMatch:
    testable_id: str # id
    text: str # document
    member_ids: list[uuid.UUID] # metadata.member_ids
    team_id: uuid.UUID # metadata.team_id
    score: float # calculated from cosine similarity

"""
id -> testable_id
document -> app : feature : description
metadata -> team_id , member_ids (list of str)
"""
COLLECTION_NAME = "testable_records"  # single collection shared by all teams; isolation is via team_id filter

QUERY_TEXT_TEMPLATE = "{app} : {feature} : {description}"  # how we embed the testable's text for expertise lookups

def _parse_uuid_list(raw_val: Any) -> list[uuid.UUID]:
    if isinstance(raw_val, list):
        return [uuid.UUID(str(m)) for m in raw_val]
    if isinstance(raw_val, str):
        try:
            parsed = json.loads(raw_val.replace("'", '"'))
            if isinstance(parsed, list):
                return [uuid.UUID(str(m)) for m in parsed]
        except (ValueError, TypeError):
            pass
        return [uuid.UUID(m.strip()) for m in raw_val.split(',') if m.strip()]
    return []

class ExpertiseVectorStore:
    """Single Chroma collection shared by every team. Isolation comes from a
    `team_id` field on each record's metadata, filtered at query time — not
    from separate collections per team. This is what lets cross-team
    escalation widen the filter to multiple team_ids instead of standing up
    a second store and merging results.
    """

    def __init__(self, settings: Settings):
        self._client = chromadb.PersistentClient(path=settings.vector_store_path)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=OllamaEmbeddingFunction(model_name=settings.embedding_model)
        )

    def upsert_testable_record(
        self, 
        testable_id: str, 
        team_id: uuid.UUID, 
        member_ids: list[uuid.UUID], 
        app: str, 
        feature: str, 
        description: str
    ):
        """Upserts a single historical testable record, with the given 
        team_id and member_ids of the developers. The text is embedded 
        into the vector store for future expertise lookups.
        """
        text = QUERY_TEXT_TEMPLATE.format(app=app, feature=feature, description=description)
        meta = {"team_id": str(team_id)}
        if member_ids:
            meta["member_ids"] = [str(m) for m in member_ids]
            
        self._collection.upsert(
            ids=[testable_id],
            metadatas=[meta],
            documents=[text],
        )

    def upsert_testable_records_batch(
        self, 
        testable_ids: list[str], 
        team_ids: list[uuid.UUID], 
        member_ids_list: list[list[uuid.UUID]], 
        app_list: list[str], 
        feature_list: list[str], 
        description_list: list[str]
    ):
        """Upserts a batch of historical testable records for multiple 
        testables along with their associated team_ids and member_ids. 
        The texts are embedded into the vector store for future 
        expertise lookups.
        """
        texts = [
            QUERY_TEXT_TEMPLATE.format(app=app, feature=feature, description=description)
            for app, feature, description in zip(app_list, feature_list, description_list)
        ]
        metadatas = []
        for team_id, member_ids in zip(team_ids, member_ids_list):
            meta = {"team_id": str(team_id)}
            if member_ids:
                meta["member_ids"] = [str(m) for m in member_ids]
            metadatas.append(meta)
        self._collection.upsert(
            ids=testable_ids,
            metadatas=metadatas,
            documents=texts,
        )

    def search_expertise(
        self,
        team_ids: list[uuid.UUID],
        app: str,
        feature: str,
        description: str,
        candidate_member_ids: list[uuid.UUID],
        k: int = 10,
    ) -> list[ExpertiseMatch]:
        """Returns the k most relevant historical assignments, restricted to
        the given team_ids. Pass a single team for normal lookups, or
        multiple team_ids to widen the search during cross-team escalation
        when the home team is fully at capacity.
        """

        team_filter = (
            {"team_id": str(team_ids[0])} 
            if len(team_ids) == 1 
            else {"team_id": {"$in": [str(t) for t in team_ids]}}
        )

        candidate_filter = {}
        if candidate_member_ids:
            if len(candidate_member_ids) == 1:
                candidate_filter = {"member_ids": {"$contains": str(candidate_member_ids[0])}}
            else:
                candidate_filter = {
                    "$or": [
                        {"member_ids": {"$contains": str(m)}} for m in candidate_member_ids
                    ]
                }

        if candidate_filter:
            where_filter = {
                "$and": [
                    team_filter,
                    candidate_filter
                ]
            }
        else:
            where_filter = team_filter

        query_text = QUERY_TEXT_TEMPLATE.format(app=app, feature=feature, description=description)

        results = self._collection.query(
            query_texts=[query_text],
            n_results=k,
            where=where_filter,
        )

        matches: list[ExpertiseMatch] = []
        
        if not results.get("ids") or not results["ids"][0]:
            return matches
            
        for ids, documents, metadatas, distances in zip(results["ids"], results["documents"], results["metadatas"], results["distances"]):
            for id, document, metadata, distance in zip(ids, documents, metadatas, distances):
                matches.append(
                    ExpertiseMatch(
                        member_ids=_parse_uuid_list(metadata.get("member_ids", [])),
                        team_id=uuid.UUID(str(metadata["team_id"])),
                        testable_id=id,
                        score=1.0 - distance,  # chroma returns cosine distance(dissimilarity); convert to similarity
                        text=document,
                    )
                )
        return matches


    def expertise_score_per_member(
        self,
        team_ids: list[uuid.UUID],
        candidate_member_ids: list[uuid.UUID],
        app: str,
        feature: str,
        description: str,
        k: int = 10,
    ) -> dict[uuid.UUID, float]:
        """Aggregates raw matches into one 0-1 expertise score per candidate,
        taking each member's best-matching historical assignment. Candidates
        with no history get 0.0 rather than being dropped, so the constraint
        scorer can still apply a cold-start fallback instead of crashing on
        a missing key.
        """
        matches = self.search_expertise(
            team_ids=team_ids,
            app=app,
            feature=feature,
            description=description,
            candidate_member_ids=candidate_member_ids,
            k=k
        )

        best_score_by_member: dict[uuid.UUID, float] = {}
        
        for match in matches:
            for member_id in match.member_ids:
                current_best = best_score_by_member.get(member_id)
                if current_best is None or match.score > current_best:
                    best_score_by_member[member_id] = match.score

        return {
            member_id: best_score_by_member.get(member_id, 0.0)
            for member_id in candidate_member_ids
        }


_vector_store: Optional[ExpertiseVectorStore] = None

def get_vector_store() -> ExpertiseVectorStore:
    global _vector_store
    if _vector_store is None:
        settings = Settings()
        _vector_store = ExpertiseVectorStore(settings)
    return _vector_store
