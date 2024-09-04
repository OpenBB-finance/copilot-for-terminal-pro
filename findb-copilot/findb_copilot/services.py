import os
from typing import Literal

import httpx
import jwt
from fastapi import HTTPException

from .models import VectorSearchResult


class VectorSearchService:
    def __init__(self):
        self._vector_url = os.getenv("FIN_DB_HOST_URL")
        self._access_token = jwt.encode({"scopes": ["findb"]}, os.getenv("SECRET_KEY"), algorithm="HS256")

    async def search(
        self,
        query: str,
        symbol: str,
        document_type: Literal["sec_filing", "earnings_transcript"] | None = None,
        form_type: Literal["10-K", "10-Q"] | None = None,
        fiscal_year: int | None = None,
        fiscal_quarter: Literal["Q1", "Q2", "Q3", "FY"] | None = None,
        limit: int = 12,
    ) -> list[VectorSearchResult]:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self._access_token}"}
            payload = {
                "query": query,
                "symbol": symbol,
                "form_type": form_type,
                "fiscal_year": fiscal_year,
                "fiscal_quarter": fiscal_quarter,
                "document_type": document_type,
                "limit": limit,
            }
            r = await client.post(self._vector_url + "/v1/documents/search", json=payload, headers=headers)
            if r.status_code == 200:
                results = []
                for result in r.json():
                    results.append(VectorSearchResult(**result))
                return results
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Something went wrong with the vector database: {r.content}",
                )
