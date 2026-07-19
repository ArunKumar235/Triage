import asyncio
from collections import defaultdict
from sqlalchemy import select

from triage.config import get_settings
from triage.api.deps import init_engine, get_session_factory
from triage.models.db.testable import Testable
from triage.models.db.dev_history import DevHistory
from triage.core.rag.vector_store import get_vector_store
from triage.models.schemas.enums.role import Role

async def run_ingestion():
    print("Starting ingestion process...")
    settings = get_settings()
    init_engine(settings)
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        # Fetch all testables
        result = await session.execute(select(Testable))
        testables = result.scalars().all()
        
        # Fetch all dev history records
        history_result = await session.execute(select(DevHistory).where(DevHistory.role==Role.DEVELOPER))
        dev_histories = history_result.scalars().all()
        
        if not testables:
            print("No testables found in the database.")
            return
            
        # Group developers by testable_id
        dev_map = defaultdict(set)
        for dh in dev_histories:
            dev_map[dh.testable_id].add(dh.team_member_id)

        testable_ids = []
        team_ids = []
        member_ids_list = []
        app_list = []
        feature_list = []
        description_list = []
        
        for t in testables:
            testable_ids.append(t.id)
            team_ids.append(t.team_id)
            # Convert set back to list, default to empty list if no history
            member_ids_list.append(list(dev_map.get(t.id, set())))
            app_list.append(t.app)
            feature_list.append(t.feature)
            description_list.append(t.description)

        if not testable_ids:
            print("No testable records found to ingest.")
            return

        print(f"Found {len(testable_ids)} records to ingest. Upserting into ChromaDB...")
        
        vector_store = get_vector_store()
        
        vector_store.upsert_testable_records_batch(
            testable_ids=testable_ids,
            team_ids=team_ids,
            member_ids_list=member_ids_list,
            app_list=app_list,
            feature_list=feature_list,
            description_list=description_list
        )
        print("Vector store content: ", vector_store._collection.get())

        print("Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
