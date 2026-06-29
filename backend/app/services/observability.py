"""
Observability — 日志监控 + 缓存
Step 19: 日志监控
Step 21: Cache缓存
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RecommendLogger:
    """
    推荐请求日志记录器
    每次请求记录完整链路信息
    """
    
    def __init__(self):
        self.logs = []
    
    def record_request(self, user_query: str, parsed_profile: dict):
        """记录原始请求和解析结果"""
        entry = {
            'user_query': user_query,
            'parsed_profile': parsed_profile,
            'sql_filters': {},
            'sql_results_count': 0,
            'risk_algorithm_version': 'v1',
            'retrieved_chunks': [],
            'reranked_chunks': [],
            'final_answer': '',
            'warnings': [],
            'created_at': datetime.utcnow().isoformat(),
        }
        self.logs.append(entry)
        return entry
    
    def update_sql(self, entry: dict, sql_filters: dict, results_count: int):
        entry['sql_filters'] = sql_filters
        entry['sql_results_count'] = results_count
    
    def update_chunks(self, entry: dict, retrieved: list, reranked: list):
        entry['retrieved_chunks'] = [
            {'chunk_id': c.get('chunk_id'), 'doc_type': c.get('doc_type'), 'title': c.get('title')}
            for c in retrieved
        ]
        entry['reranked_chunks'] = [
            {'chunk_id': c.get('chunk_id'), 'doc_type': c.get('doc_type'), 'title': c.get('title')}
            for c in reranked
        ]
    
    def update_result(self, entry: dict, answer: str, warnings: list):
        entry['final_answer'] = answer[:200]  # 只存前200字符
        entry['warnings'] = warnings
    
    def get_log(self) -> dict:
        return self.logs[-1] if self.logs else {}


# 简单的缓存
class RecommendCache:
    """
    推荐结果缓存
    基于用户画像hash缓存常见查询
    """
    
    def __init__(self, max_size: int = 50):
        self.cache: dict[str, dict] = {}
        self.max_size = max_size
    
    def _make_key(self, profile: dict) -> str:
        """根据用户画像生成缓存key"""
        key_data = {
            'province': profile.get('province'),
            'score': profile.get('score'),
            'rank': profile.get('rank'),
            'major_prefs': sorted(profile.get('major_preferences', [])),
            'city_prefs': sorted(profile.get('city_preferences', [])),
            'risk': profile.get('risk_preference'),
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, profile: dict) -> Optional[dict]:
        key = self._make_key(profile)
        return self.cache.get(key)
    
    def set(self, profile: dict, result: dict):
        key = self._make_key(profile)
        if len(self.cache) >= self.max_size:
            # 简单LRU：删第一个
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = result
    
    def invalidate(self, profile: dict):
        """当用户修改分数/位次时，清除缓存"""
        key = self._make_key(profile)
        self.cache.pop(key, None)
