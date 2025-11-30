"""Qdrant vector search tool with additional filtering capabilities."""

import json
import os
from typing import Any

from crewai_tools import QdrantVectorSearchTool


class OverloadQdrantTool(QdrantVectorSearchTool):
    """Extended Qdrant vector search tool with dynamic filtering support.

    This tool extends QdrantVectorSearchTool to allow additional filtering
    at query time via filter_by and filter_value parameters.
    """

    def _run(
        self,
        query: str,
        filter_by: str | None = None,
        filter_value: Any | None = None,
    ) -> str:
        """Perform vector similarity search with optional additional filtering.

        Args:
            query: The search query string.
            filter_by: Optional field name to filter by.
            filter_value: Optional value to filter on (used with filter_by).

        Returns:
            JSON string containing search results with distance, context, and metadata.
        """
        # Start with existing filter from config, or create empty filter
        search_filter = (
            self.qdrant_config.filter.model_copy()
            if self.qdrant_config.filter is not None
            else self.qdrant_package.http.models.Filter(must=[])
        )

        # Add additional filter if provided
        if filter_by and filter_value is not None:
            if not hasattr(search_filter, "must") or not isinstance(
                search_filter.must, list
            ):
                search_filter.must = []
            search_filter.must.append(
                self.qdrant_package.http.models.FieldCondition(
                    key=filter_by,
                    match=self.qdrant_package.http.models.MatchValue(
                        value=filter_value
                    ),
                )
            )

        # Generate query vector using custom embedding function or default OpenAI
        query_vector = (
            self.custom_embedding_fn(query)
            if self.custom_embedding_fn
            else (
                lambda: __import__("openai")
                .Client(api_key=os.getenv("OPENAI_API_KEY"))
                .embeddings.create(input=[query], model="text-embedding-3-large")
                .data[0]
                .embedding
            )()
        )

        # Perform the search
        if self.client is None:
            raise RuntimeError("Qdrant client is not initialized")
        results = self.client.query_points(
            collection_name=self.qdrant_config.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=self.qdrant_config.limit,
            score_threshold=self.qdrant_config.score_threshold,
        )

        # Format results
        return_list = []

        for p in results.points:
            return_dict = {}
            return_dict["distance"] = p.score
            return_dict["metadata"] = {}
            for key, value in p.payload.items():
                if key == "text":
                    return_dict["context"] = value
                else:
                    return_dict["metadata"][key] = value
            return_list.append(return_dict)

        return json.dumps(
            return_list,
            indent=2,
        )
