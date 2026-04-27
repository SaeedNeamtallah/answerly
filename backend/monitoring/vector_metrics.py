"""
Qdrant (Vector DB) Monitoring
"""

import logging
import requests
from prometheus_client import Gauge

logger = logging.getLogger(__name__)

# ------------------------
# Prometheus Metrics
# ------------------------

QDRANT_COLLECTIONS_COUNT = Gauge(
    "qdrant_collections_count",
    "Number of collections in Qdrant"
)

QDRANT_VECTORS_COUNT = Gauge(
    "qdrant_vectors_count",
    "Number of vectors per collection",
    ["collection_name"]
)

# ------------------------
# Config
# ------------------------

QDRANT_URL = "http://localhost:6381"

# ------------------------
# Update Metrics
# ------------------------

async def update_vector_metrics():
    try:
        # هات كل collections
        res = requests.get(f"{QDRANT_URL}/collections")
        data = res.json()

        collections = data.get("result", {}).get("collections", [])
        QDRANT_COLLECTIONS_COUNT.set(len(collections))

        # لكل collection هات عدد ال vectors
        for col in collections:
            name = col["name"]

            info = requests.get(f"{QDRANT_URL}/collections/{name}")
            info_data = info.json()

            vectors = info_data.get("result", {}).get("points_count", 0)

            QDRANT_VECTORS_COUNT.labels(collection_name=name).set(vectors)

    except Exception as e:
        logger.warning(f"Qdrant metrics failed: {str(e)}")