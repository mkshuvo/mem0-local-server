"""
Mem0 Local Service Engine
Provides 100% local, self-contained vector memory storage, semantic search,
and metadata management without requiring external API keys.
"""

import os
import sqlite3
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

COLLECTION_NAME = "mem0_memories"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384


class Mem0Service:
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # SQLite metadata & history DB
        self.db_path = os.path.join(self.data_dir, "memories.db")
        self._init_sqlite()

        # FastEmbed local embedding model
        embedding_cache = os.path.join(self.data_dir, "models")
        os.makedirs(embedding_cache, exist_ok=True)
        self.embed_model = TextEmbedding(
            model_name=EMBEDDING_MODEL_NAME,
            cache_dir=embedding_cache
        )

        # Local persistent Qdrant vector store
        qdrant_path = os.path.join(self.data_dir, "qdrant")
        os.makedirs(qdrant_path, exist_ok=True)
        self.qdrant = QdrantClient(path=qdrant_path)
        self._init_qdrant()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    user_id TEXT DEFAULT 'default',
                    project TEXT DEFAULT 'general',
                    category TEXT DEFAULT 'general',
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    conversation_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    previous_content TEXT,
                    new_content TEXT,
                    metadata_change TEXT,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_proj ON memories(project)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_cat ON memories(category)")
            conn.commit()

    def _init_qdrant(self):
        collections = [c.name for c in self.qdrant.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )

    def _get_embedding(self, text: str) -> List[float]:
        embeddings = list(self.embed_model.embed([text]))
        return embeddings[0].tolist()

    def add_memory(
        self,
        content: str,
        user_id: str = "default",
        project: str = "general",
        category: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store a new memory with vector embedding and metadata."""
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty")

        mem_id = str(uuid.uuid4())
        now = time.time()
        tags_json = json.dumps(tags or [])
        meta_json = json.dumps(metadata or {})

        # Compute embedding
        vector = self._get_embedding(content)

        # Store in SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (id, content, user_id, project, category, tags, metadata, conversation_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (mem_id, content, user_id, project, category, tags_json, meta_json, conversation_id, now, now)
            )
            cursor.execute(
                """
                INSERT INTO memory_history (memory_id, action, previous_content, new_content, metadata_change, timestamp)
                VALUES (?, 'CREATE', NULL, ?, ?, ?)
                """,
                (mem_id, content, meta_json, now)
            )
            conn.commit()

        # Store in Qdrant
        self.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=mem_id,
                    vector=vector,
                    payload={
                        "id": mem_id,
                        "content": content,
                        "user_id": user_id,
                        "project": project,
                        "category": category,
                        "tags": tags or [],
                        "conversation_id": conversation_id,
                        "created_at": now,
                        "updated_at": now
                    }
                )
            ]
        )

        return self.get_memory(mem_id)

    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        project: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search + metadata filtering."""
        query = query.strip()
        if not query:
            return self.list_memories(user_id=user_id, project=project, category=category, limit=limit)["memories"]

        query_vector = self._get_embedding(query)

        # Build Qdrant filter conditions
        must_conditions = []
        if user_id and user_id != "all":
            must_conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        if project and project != "all":
            must_conditions.append(FieldCondition(key="project", match=MatchValue(value=project)))
        if category and category != "all":
            must_conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))

        qdrant_filter = Filter(must=must_conditions) if must_conditions else None

        results = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=limit * 2,
            score_threshold=min_score if min_score > 0 else None
        )

        memories = []
        for point in results.points:
            mem = self.get_memory(str(point.id))
            if mem:
                mem["relevance_score"] = round(float(point.score), 4)
                memories.append(mem)

        # If tag filtering is needed in addition
        if tags:
            memories = [
                m for m in memories
                if any(t in m.get("tags", []) for t in tags)
            ]

        return memories[:limit]

    def list_memories(
        self,
        user_id: Optional[str] = None,
        project: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all memories with pagination and filtering."""
        where_clauses = []
        params = []

        if user_id and user_id != "all":
            where_clauses.append("user_id = ?")
            params.append(user_id)
        if project and project != "all":
            where_clauses.append("project = ?")
            params.append(project)
        if category and category != "all":
            where_clauses.append("category = ?")
            params.append(category)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count total
            cursor.execute(f"SELECT COUNT(*) FROM memories {where_sql}", params)
            total = cursor.fetchone()[0]

            # Fetch rows
            query_params = list(params) + [limit, offset]
            cursor.execute(
                f"""
                SELECT id, content, user_id, project, category, tags, metadata, conversation_id, created_at, updated_at
                FROM memories
                {where_sql}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                query_params
            )
            rows = cursor.fetchall()

        memories = [self._row_to_memory(r) for r in rows]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "memories": memories
        }

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a single memory by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, user_id, project, category, tags, metadata, conversation_id, created_at, updated_at
                FROM memories
                WHERE id = ?
                """,
                (memory_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                """
                SELECT id, action, previous_content, new_content, metadata_change, timestamp
                FROM memory_history
                WHERE memory_id = ?
                ORDER BY timestamp ASC
                """,
                (memory_id,)
            )
            history_rows = cursor.fetchall()

        mem = self._row_to_memory(row)
        mem["history"] = [
            {
                "id": hr[0],
                "action": hr[1],
                "previous_content": hr[2],
                "new_content": hr[3],
                "metadata_change": json.loads(hr[4]) if hr[4] else None,
                "timestamp": hr[5]
            }
            for hr in history_rows
        ]
        return mem

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        project: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing memory."""
        current = self.get_memory(memory_id)
        if not current:
            return None

        new_content = content.strip() if content is not None else current["content"]
        new_project = project if project is not None else current["project"]
        new_category = category if category is not None else current["category"]
        new_tags = tags if tags is not None else current["tags"]
        new_metadata = metadata if metadata is not None else current["metadata"]
        now = time.time()

        content_changed = new_content != current["content"]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE memories
                SET content = ?, project = ?, category = ?, tags = ?, metadata = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_content, new_project, new_category, json.dumps(new_tags), json.dumps(new_metadata), now, memory_id)
            )
            cursor.execute(
                """
                INSERT INTO memory_history (memory_id, action, previous_content, new_content, metadata_change, timestamp)
                VALUES (?, 'UPDATE', ?, ?, ?, ?)
                """,
                (memory_id, current["content"] if content_changed else None, new_content if content_changed else None, json.dumps(new_metadata), now)
            )
            conn.commit()

        # Update Qdrant
        vector = self._get_embedding(new_content) if content_changed else None
        if vector:
            self.qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=vector,
                        payload={
                            "id": memory_id,
                            "content": new_content,
                            "user_id": current["user_id"],
                            "project": new_project,
                            "category": new_category,
                            "tags": new_tags,
                            "conversation_id": current["conversation_id"],
                            "created_at": current["created_at"],
                            "updated_at": now
                        }
                    )
                ]
            )
        else:
            self.qdrant.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "project": new_project,
                    "category": new_category,
                    "tags": new_tags,
                    "updated_at": now
                },
                points=[memory_id]
            )

        return self.get_memory(memory_id)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from SQLite and Qdrant."""
        current = self.get_memory(memory_id)
        if not current:
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory_history WHERE memory_id = ?", (memory_id,))
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()

        self.qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[memory_id]
        )
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for the dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT project, COUNT(*) FROM memories GROUP BY project")
            projects = dict(cursor.fetchall())

            cursor.execute("SELECT category, COUNT(*) FROM memories GROUP BY category")
            categories = dict(cursor.fetchall())

            cursor.execute("SELECT user_id, COUNT(*) FROM memories GROUP BY user_id")
            users = dict(cursor.fetchall())

        collection_info = self.qdrant.get_collection(collection_name=COLLECTION_NAME)
        vector_count = collection_info.points_count or 0

        return {
            "total_memories": total,
            "vector_count": vector_count,
            "projects": projects,
            "categories": categories,
            "users": users,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "vector_size": VECTOR_SIZE,
            "status": "healthy"
        }

    def export_data(self) -> Dict[str, Any]:
        """Export all memories and history for backup."""
        all_memories = self.list_memories(limit=100000)["memories"]
        return {
            "exported_at": time.time(),
            "count": len(all_memories),
            "memories": [self.get_memory(m["id"]) for m in all_memories]
        }

    def import_data(self, data: Dict[str, Any]) -> int:
        """Import memories from a JSON backup."""
        memories = data.get("memories", [])
        count = 0
        for item in memories:
            self.add_memory(
                content=item["content"],
                user_id=item.get("user_id", "default"),
                project=item.get("project", "general"),
                category=item.get("category", "general"),
                tags=item.get("tags", []),
                metadata=item.get("metadata", {}),
                conversation_id=item.get("conversation_id")
            )
            count += 1
        return count

    def _row_to_memory(self, row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "content": row[1],
            "user_id": row[2],
            "project": row[3],
            "category": row[4],
            "tags": json.loads(row[5]) if row[5] else [],
            "metadata": json.loads(row[6]) if row[6] else {},
            "conversation_id": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        }
