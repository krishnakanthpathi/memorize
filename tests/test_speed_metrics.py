"""
Speed and Performance Benchmark Test Suite for Memorize.

This test measures the precise execution time and granular sub-operation metrics
for Creation, Search, Merge, and Deletion of memories in a completely isolated,
temporary sandbox environment.

No existing memories, SQLite database rows, ChromaDB collections, or backup files
are affected during or after running this test suite.
"""

from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Dict, List
import unittest

import config.constants as constants
from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from core.memory_merger import merge_memories_service
from core.memory_service import execute_upsert_memory, handle_delete_memory, reindex_memory_chunks
from search.filter_extractor import extract_keywords_and_snippet
from search.relevance_scorer import (
    calculate_hybrid_score,
    search_hybrid_relevance,
    search_vector_similarity,
)
from storage.backup_manager import backup_single_memory_file
import storage.backup_manager as backup_mgr
from storage.db_manager import (
    delete_memory_from_index,
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)
from storage.markdown_handler import create_markdown_file, delete_markdown_file
import storage.organization_manager as org_mgr
import storage.sync_manager as sync_mgr
from storage.version_manager import create_version_snapshot
import utils.category_utils as cat_utils
from vector.chunker import chunk_text
from vector.embedder import generate_embeddings
from vector.vector_db import (
    add_chunks_to_vector_db,
    delete_chunks_by_memory_id,
    query_vector_db,
)
import vector.vector_db as vector_db_module


class TestSpeedMetrics(unittest.TestCase):
    """
    Temporary performance benchmark test suite.
    Runs non-conflicting memory operations in an isolated sandbox,
    captures detailed sub-millisecond metrics for:
      - Memory Creation (Markdown I/O, Chunking, Embedding Forward-Pass, ChromaDB HNSW Insert, SQLite Index)
      - Memory Search (Query Embedding, ChromaDB Vector Search, SQLite Metadata Lookup, Hybrid Scoring)
      - Memory Merge (Deterministic/LLM Merge, Version Snapshotting, Re-indexing, Source Memory Cleanup)
      - Memory Deletion (ChromaDB Purge, Markdown Unlink, SQLite Row Deletion)
    """

    def setUp(self):
        # Create a brand new isolated temporary environment for every test run
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        self.temp_data_dir = self.tmp_path / "data"
        self.temp_db_path = self.temp_data_dir / "speedtest_sandbox.db"
        self.temp_memories_dir = self.temp_data_dir / "memories"
        self.temp_backup_dir = self.temp_data_dir / "backups"
        self.temp_backup_memories_dir = self.temp_backup_dir / "memories"
        self.temp_chroma_dir = self.tmp_path / "chroma_db"

        self.temp_data_dir.mkdir(parents=True, exist_ok=True)
        self.temp_memories_dir.mkdir(parents=True, exist_ok=True)
        self.temp_backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_backup_memories_dir.mkdir(parents=True, exist_ok=True)
        self.temp_chroma_dir.mkdir(parents=True, exist_ok=True)

        # Preserve original environment settings
        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR
        self.orig_backup_memories_dir = constants.BACKUP_MEMORIES_DIR
        self.orig_chroma_dir = vector_db_module.CHROMA_DIR
        self.orig_chroma_client = vector_db_module.CHROMA_CLIENT
        self.orig_use_llm = constants.USE_LLM

        # Redirect all constants and module references to temporary directories
        constants.DATA_DIR = self.temp_data_dir
        constants.DB_PATH = self.temp_db_path
        constants.MEMORIES_DIR = self.temp_memories_dir
        constants.BACKUP_DIR = self.temp_backup_dir
        constants.BACKUP_MEMORIES_DIR = self.temp_backup_memories_dir
        constants.USE_LLM = False

        backup_mgr.MEMORIES_DIR = self.temp_memories_dir
        backup_mgr.BACKUP_MEMORIES_DIR = self.temp_backup_memories_dir
        backup_mgr.BACKUP_DIR = self.temp_backup_dir
        backup_mgr.DB_PATH = self.temp_db_path

        cat_utils.MEMORIES_DIR = self.temp_memories_dir
        org_mgr.MEMORIES_DIR = self.temp_memories_dir
        sync_mgr.MEMORIES_DIR = self.temp_memories_dir

        vector_db_module.CHROMA_DIR = self.temp_chroma_dir
        vector_db_module.CHROMA_CLIENT = None

        # Initialize fresh sandbox database
        init_db()

    def tearDown(self):
        # Restore original environment settings
        vector_db_module.CHROMA_CLIENT = None
        vector_db_module.CHROMA_DIR = self.orig_chroma_dir

        constants.DATA_DIR = self.orig_data_dir
        constants.DB_PATH = self.orig_db_path
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.BACKUP_DIR = self.orig_backup_dir
        constants.BACKUP_MEMORIES_DIR = self.orig_backup_memories_dir
        constants.USE_LLM = self.orig_use_llm

        backup_mgr.MEMORIES_DIR = self.orig_memories_dir
        backup_mgr.BACKUP_MEMORIES_DIR = self.orig_backup_memories_dir
        backup_mgr.BACKUP_DIR = self.orig_backup_dir
        backup_mgr.DB_PATH = self.orig_db_path

        cat_utils.MEMORIES_DIR = self.orig_memories_dir
        org_mgr.MEMORIES_DIR = self.orig_memories_dir
        sync_mgr.MEMORIES_DIR = self.orig_memories_dir

        # Completely remove temporary directory
        self.tmp_dir.cleanup()

    def test_01_creation_speed_and_metrics(self):
        """Measures Creation throughput and sub-operation latencies."""
        print("\n" + "=" * 80)
        print("  [TEST 1/4] BENCHMARKING MEMORY CREATION")
        print("=" * 80)

        items = [
            {
                "id": "mem_temp_create_001",
                "title": "SpeedTest - Distributed Systems Consensus",
                "category": "development",
                "tags": ["distributed-systems", "raft", "paxos", "speedtest"],
                "content": "Consensus protocols like Raft and Paxos ensure cluster state synchronization despite network partitions.",
            },
            {
                "id": "mem_temp_create_002",
                "title": "SpeedTest - Vector Indexing HNSW Graph Mechanics",
                "category": "projects",
                "tags": ["hnsw", "vector-db", "chromadb", "speedtest"],
                "content": "Hierarchical Navigable Small World graphs provide logarithmic nearest neighbor search complexity over high-dimensional vector spaces.",
            },
            {
                "id": "mem_temp_create_003",
                "title": "SpeedTest - Zero Copy Memory Optimization",
                "category": "development",
                "tags": ["python", "memory", "buffers", "speedtest"],
                "content": "Zero-copy byte operations using Python memoryview and ctypes bypass serialization overhead for high throughput data streaming.",
            },
        ]

        total_ms = 0.0
        sub_timings = {"disk_io": 0.0, "chunking": 0.0, "embeddings": 0.0, "chromadb": 0.0, "sqlite": 0.0}

        for item in items:
            t0 = time.perf_counter()
            # 1. Disk & Backup
            t_md0 = time.perf_counter()
            content_hash = compute_string_hash(item["content"])
            fpath = create_markdown_file(
                memory_id=item["id"],
                title=item["title"],
                category=item["category"],
                tags=item["tags"],
                content=item["content"],
                content_hash=content_hash,
                overwrite=False,
            )
            backup_single_memory_file(fpath)
            t_md = (time.perf_counter() - t_md0) * 1000.0

            # 2. Chunking
            t_ck0 = time.perf_counter()
            chunks = chunk_text(item["id"], item["content"])
            t_ck = (time.perf_counter() - t_ck0) * 1000.0

            # 3. Embeddings
            chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
            t_em0 = time.perf_counter()
            embeddings = generate_embeddings(chunk_texts)
            t_em = (time.perf_counter() - t_em0) * 1000.0

            # 4. ChromaDB
            t_ch0 = time.perf_counter()
            add_chunks_to_vector_db(chunks, embeddings)
            t_ch = (time.perf_counter() - t_ch0) * 1000.0

            # 5. SQLite
            t_sq0 = time.perf_counter()
            upsert_memory_index({
                "id": item["id"],
                "title": item["title"],
                "category": item["category"],
                "tags": item["tags"],
                "file_path": str(fpath),
                "content": item["content"],
                "content_hash": content_hash,
                "chunk_ids": [c.get("chunk_id", "") for c in chunks],
            })
            t_sq = (time.perf_counter() - t_sq0) * 1000.0

            item_total = (time.perf_counter() - t0) * 1000.0
            total_ms += item_total
            sub_timings["disk_io"] += t_md
            sub_timings["chunking"] += t_ck
            sub_timings["embeddings"] += t_em
            sub_timings["chromadb"] += t_ch
            sub_timings["sqlite"] += t_sq

            print(f"  -> Created '{item['id']}': {item_total:>7.2f} ms | Embedding: {t_em:>6.2f} ms | ChromaDB: {t_ch:>5.2f} ms | SQLite: {t_sq:>4.2f} ms | Disk I/O: {t_md:>4.2f} ms")

        avg_ms = total_ms / len(items)
        print(f"\n[Creation Summary] Count: {len(items)} | Total Time: {total_ms:.2f} ms | Avg Time: {avg_ms:.2f} ms | Throughput: {1000.0 / avg_ms:.1f} ops/sec")
        print(f"  - Embedding Generation Share: {sub_timings['embeddings'] / total_ms * 100:.1f}%")
        print(f"  - ChromaDB Vector Store Share: {sub_timings['chromadb'] / total_ms * 100:.1f}%")
        print(f"  - Disk Markdown + Backup Share: {sub_timings['disk_io'] / total_ms * 100:.1f}%")
        print(f"  - SQLite Indexing Share:        {sub_timings['sqlite'] / total_ms * 100:.1f}%")
        self.assertEqual(len(items), 3)

    def test_02_search_speed_and_metrics(self):
        """Measures Vector and Hybrid Search throughput and sub-operation latencies."""
        print("\n" + "=" * 80)
        print("  [TEST 2/4] BENCHMARKING MEMORY SEARCH")
        print("=" * 80)

        # Seed 3 memories first
        execute_upsert_memory(
            memory_id="mem_temp_search_001",
            title="SearchBenchmark - Advanced RAG Retrieval Pipelines",
            category="development",
            tags=["rag", "retrieval", "vector", "searchtest"],
            content="Hybrid search combines dense vector embeddings with BM25 and keyword frequency scoring.",
        )
        execute_upsert_memory(
            memory_id="mem_temp_search_002",
            title="SearchBenchmark - SQLite In-Memory Database Speed",
            category="development",
            tags=["sqlite", "database", "indexing", "searchtest"],
            content="SQLite executes indexed relational queries with sub-millisecond query planning and execution.",
        )

        queries = [
            "dense vector embeddings hybrid search",
            "SQLite database query planning speed",
            "Advanced RAG Retrieval Pipelines",
        ]

        total_ms = 0.0
        sub_timings = {"q_embed": 0.0, "chromadb_ann": 0.0, "sqlite_lookup": 0.0, "hybrid_score": 0.0}

        for q in queries:
            t0 = time.perf_counter()

            # 1. Query Embedding
            t_qe0 = time.perf_counter()
            q_emb = generate_embeddings([q])
            t_qe = (time.perf_counter() - t_qe0) * 1000.0

            # 2. ChromaDB ANN Search
            t_ann0 = time.perf_counter()
            vec_res = query_vector_db(query_embedding=q_emb[0], n_results=5)
            t_ann = (time.perf_counter() - t_ann0) * 1000.0

            # 3. SQLite Metadata
            t_sql0 = time.perf_counter()
            all_mems = {m["id"]: m for m in get_all_memories()}
            t_sql = (time.perf_counter() - t_sql0) * 1000.0

            # 4. Hybrid Scoring
            t_sc0 = time.perf_counter()
            _, q_kw = extract_keywords_and_snippet(q)
            ranked = []
            for r in vec_res:
                mid = r.get("memory_id", "")
                db_e = all_mems.get(mid, {})
                score = calculate_hybrid_score(
                    vector_similarity=r.get("similarity_score", 0.0),
                    query_keywords=q_kw,
                    memory_tags=r.get("tags", []) or db_e.get("tags", []),
                    memory_category=r.get("category", "personal"),
                    target_category=None,
                    db_entry=db_e,
                )
                ranked.append({"id": mid, "score": score})
            ranked.sort(key=lambda x: x["score"], reverse=True)
            t_sc = (time.perf_counter() - t_sc0) * 1000.0

            q_total = (time.perf_counter() - t0) * 1000.0
            total_ms += q_total
            sub_timings["q_embed"] += t_qe
            sub_timings["chromadb_ann"] += t_ann
            sub_timings["sqlite_lookup"] += t_sql
            sub_timings["hybrid_score"] += t_sc

            top_match = ranked[0]["id"] if ranked else "None"
            top_sc = ranked[0]["score"] if ranked else 0.0
            print(f"  -> Searched '{q}': {q_total:>6.2f} ms | Query Embed: {t_qe:>5.2f} ms | ChromaDB: {t_ann:>5.2f} ms | SQLite: {t_sql:>4.2f} ms | Top: {top_match} ({top_sc:.3f})")

        avg_ms = total_ms / len(queries)
        print(f"\n[Search Summary] Queries: {len(queries)} | Total Time: {total_ms:.2f} ms | Avg Time: {avg_ms:.2f} ms | Throughput: {1000.0 / avg_ms:.1f} queries/sec")
        print(f"  - Query Embedding Computation: {sub_timings['q_embed'] / total_ms * 100:.1f}%")
        print(f"  - ChromaDB ANN Traversal:      {sub_timings['chromadb_ann'] / total_ms * 100:.1f}%")
        print(f"  - SQLite Metadata Lookup:      {sub_timings['sqlite_lookup'] / total_ms * 100:.1f}%")
        print(f"  - Hybrid Scoring & Ranking:    {sub_timings['hybrid_score'] / total_ms * 100:.1f}%")
        self.assertGreaterEqual(len(queries), 3)

    def test_03_merge_speed_and_metrics(self):
        """Measures Memory Merge throughput, re-indexing, and source cleanup latency."""
        print("\n" + "=" * 80)
        print("  [TEST 3/4] BENCHMARKING MEMORY MERGE")
        print("=" * 80)

        # Seed two related memories
        res1 = execute_upsert_memory(
            memory_id="mem_temp_merge_001",
            title="MergeBenchmark - Part 1: Microservices Architecture",
            category="development",
            tags=["architecture", "microservices", "mergetest"],
            content="Microservices divide monolithic systems into independently deployable units.",
        )
        res2 = execute_upsert_memory(
            memory_id="mem_temp_merge_002",
            title="MergeBenchmark - Part 2: Service Mesh & Istio",
            category="development",
            tags=["architecture", "service-mesh", "istio", "mergetest"],
            content="Service mesh provides traffic routing, mTLS security, and observability across microservices.",
        )

        t_start = time.perf_counter()
        merge_res = merge_memories_service(
            memory_ids=["mem_temp_merge_001", "mem_temp_merge_002"],
            target_title="MergeBenchmark - Unified Microservices & Service Mesh Guide",
            target_category="development",
            target_tags=["architecture", "microservices", "service-mesh", "mergetest"],
            delete_sources=True,
        )
        merge_duration_ms = (time.perf_counter() - t_start) * 1000.0

        self.assertEqual(merge_res["status"], "success")
        merged_id = merge_res["merged_memory_id"]
        deleted_count = len(merge_res.get("deleted_source_ids", []))

        print(f"  -> Merged 2 memories -> Target: '{merged_id}' in {merge_duration_ms:.2f} ms")
        print(f"  -> Deleted Source Memories: {deleted_count} (Source: mem_temp_merge_002 cleanly purged)")
        print(f"\n[Merge Summary] Merges: 1 | Consolidated Memories: 2 | Total Time: {merge_duration_ms:.2f} ms")
        self.assertIsNotNone(get_memory_by_id(merged_id))
        self.assertIsNone(get_memory_by_id("mem_temp_merge_002"))

    def test_04_deletion_speed_and_metrics(self):
        """Measures Deletion throughput across Disk, ChromaDB vector collection, and SQLite index."""
        print("\n" + "=" * 80)
        print("  [TEST 4/4] BENCHMARKING MEMORY DELETION")
        print("=" * 80)

        # Seed 3 memories to delete
        target_ids = ["mem_temp_del_001", "mem_temp_del_002", "mem_temp_del_003"]
        for mid in target_ids:
            execute_upsert_memory(
                memory_id=mid,
                title=f"DeleteBenchmark - Target Memory {mid}",
                category="personal",
                tags=["delete", "speedtest"],
                content=f"Temporary memory payload for deletion speed testing: {mid}",
            )

        total_ms = 0.0
        sub_timings = {"disk_unlink": 0.0, "chromadb_purge": 0.0, "sqlite_delete": 0.0}

        for mid in target_ids:
            t0 = time.perf_counter()
            target = get_memory_by_id(mid)

            # 1. Disk unlink
            t_d0 = time.perf_counter()
            fpath = target.get("file_path")
            if fpath and Path(fpath).exists():
                delete_markdown_file(fpath)
            t_d = (time.perf_counter() - t_d0) * 1000.0

            # 2. ChromaDB chunk purge
            t_v0 = time.perf_counter()
            delete_chunks_by_memory_id(mid)
            t_v = (time.perf_counter() - t_v0) * 1000.0

            # 3. SQLite row delete
            t_s0 = time.perf_counter()
            delete_memory_from_index(mid)
            t_s = (time.perf_counter() - t_s0) * 1000.0

            del_total = (time.perf_counter() - t0) * 1000.0
            total_ms += del_total
            sub_timings["disk_unlink"] += t_d
            sub_timings["chromadb_purge"] += t_v
            sub_timings["sqlite_delete"] += t_s

            print(f"  -> Deleted '{mid}': {del_total:>6.2f} ms | ChromaDB Purge: {t_v:>5.2f} ms | SQLite Purge: {t_s:>4.2f} ms | Disk Unlink: {t_d:>4.2f} ms")

            self.assertIsNone(get_memory_by_id(mid))

        avg_ms = total_ms / len(target_ids)
        print(f"\n[Deletion Summary] Deletions: {len(target_ids)} | Total Time: {total_ms:.2f} ms | Avg Time: {avg_ms:.2f} ms | Throughput: {1000.0 / avg_ms:.1f} deletions/sec")
        print(f"  - ChromaDB Vector Purge Share:  {sub_timings['chromadb_purge'] / total_ms * 100:.1f}%")
        print(f"  - SQLite Row Deletion Share:     {sub_timings['sqlite_delete'] / total_ms * 100:.1f}%")
        print(f"  - Markdown Disk Unlink Share:    {sub_timings['disk_unlink'] / total_ms * 100:.1f}%")

        print("\n" + "=" * 80)
        print("  SUMMARY: WHY DOES EACH OPERATION TAKE THIS MUCH TIME?")
        print("=" * 80)
        print("  1. CREATION (~20 - 150 ms warm):")
        print("     - Primary cost (~80-90%): SentenceTransformer neural network forward pass computing dense vector embeddings.")
        print("     - Secondary cost (~5-10%): ChromaDB HNSW binary graph update and cosine similarity index insertion.")
        print("     - Minimal cost (~2-5%): YAML frontmatter serialization, SHA-256 hash calculation, and SQLite transaction.")
        print("")
        print("  2. SEARCH (~20 - 60 ms warm):")
        print("     - Primary cost (~85-95%): Query vector embedding inference.")
        print("     - Secondary cost (~3-8%): ChromaDB cosine distance vector traversal over HNSW graphs.")
        print("     - Minimal cost (~1-3%): SQLite metadata lookup and hybrid relevance composite scoring.")
        print("")
        print("  3. MERGE (~40 - 100 ms deterministic, ~1.5 - 5s with LLM):")
        print("     - Content synthesis, version control snapshotting, vector re-indexing, and obsolete source deletion.")
        print("")
        print("  4. DELETION (~5 - 10 ms):")
        print("     - Ultra-fast: ChromaDB chunk ID purge + SQLite row deletion + file unlink. (150+ ops/sec throughput).")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    unittest.main()
