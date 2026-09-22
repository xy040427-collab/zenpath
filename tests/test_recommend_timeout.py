import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
import app.models.models
from app.routes import jiangsu_recommend as route


class RecommendationTimeout(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = create_async_engine('sqlite+aiosqlite:///' + self.tmp.name + '/test.db')
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        self.tmp.cleanup()

    async def save(self):
        async with self.sessions() as db:
            await db.execute(text('SELECT 1'))
            return await route._save_jiangsu_report(db, route.JiangsuRecommendRequest(score=600),
                {'冲': [], '稳': [], '保': []}, 20000, 'user_input', '物理等科目类', 600)

    async def test_parallel_reports_do_not_hold_writer_during_ai(self):
        entered = 0
        ready = asyncio.Event()
        async def ai(*args):
            nonlocal entered
            # Acquiring an independent SQLite write lock must succeed while AI waits.
            async with self.engine.connect() as conn:
                await conn.execute(text('BEGIN IMMEDIATE'))
                await conn.rollback()
            entered += 1
            if entered == 2:
                ready.set()
            await asyncio.wait_for(ready.wait(), 2)
            return {}
        with patch('app.services.report_ai_writer.generate_ai_narratives', side_effect=ai):
            ids = await asyncio.gather(self.save(), self.save())
        self.assertEqual(entered, 2)
        self.assertTrue(all(ids))
        self.assertNotEqual(*ids)
        async with self.engine.connect() as conn:
            self.assertEqual((await conn.execute(text('SELECT count(*) FROM reports'))).scalar(), 2)
            self.assertEqual((await conn.execute(text('SELECT count(*) FROM sessions'))).scalar(), 1)

    async def test_ai_timeout_still_saves_data_report(self):
        real_wait_for = asyncio.wait_for
        async def slow(*args):
            await asyncio.sleep(10)
        async def short_wait(coro, timeout):
            self.assertEqual(timeout, 20.0)
            return await real_wait_for(coro, .01)
        with patch('app.services.report_ai_writer.generate_ai_narratives', side_effect=slow), patch.object(route.asyncio, 'wait_for', side_effect=short_wait):
            report_id = await self.save()
        self.assertTrue(report_id)
        async with self.engine.connect() as conn:
            value = (await conn.execute(text('SELECT report_json FROM reports'))).scalar()
            self.assertIn('"ai_generation_status": "timeout"', value)

    async def test_metadata_preserves_sources_without_vector_model(self):
        rows = [{'metadata': {'school_name': '测试大学', 'doc_type': 'school_profile', 'source_url': 'https://example.org/source', 'title': '简介'}}]
        with patch.object(route, '_get_rag_docstore', return_value=rows):
            data = route._get_rag_evidence_batch({'稳': [{'school_name': '测试大学'}]})
        self.assertTrue(data['测试大学']['school_profile_available'])
        self.assertEqual(data['测试大学']['sources'][0]['source_url'], 'https://example.org/source')

if __name__ == '__main__':
    unittest.main()
