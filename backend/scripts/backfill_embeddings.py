"""
Backfill embeddings for existing articles using Voyage AI.

Usage:
    cd backend
    python scripts/backfill_embeddings.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from dotenv import load_dotenv

load_dotenv()

VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-3"
BATCH_SIZE = 64  # Voyage API max per request


async def embed_batch(texts: list[str]) -> list[list[float] | None]:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            VOYAGE_API_URL,
            headers={"Authorization": f"Bearer {VOYAGE_API_KEY}"},
            json={"input": texts, "model": MODEL},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]


async def main():
    from supabase import create_client

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch all articles without embeddings
    resp = (
        supabase.table("articles")
        .select("id, title, ai_summary")
        .is_("embedding", "null")
        .limit(1000)
        .execute()
    )
    articles = resp.data or []
    print(f"Found {len(articles)} articles without embeddings")

    if not articles:
        print("Nothing to do.")
        return

    # Process in batches
    total_done = 0
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i : i + BATCH_SIZE]
        texts = [f"{a['title']} {a.get('ai_summary') or ''}"[:4000] for a in batch]

        print(f"Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} articles)...", end=" ")
        embeddings = await embed_batch(texts)

        # Update each article
        for article, emb in zip(batch, embeddings):
            if emb:
                supabase.table("articles").update({"embedding": emb}).eq(
                    "id", article["id"]
                ).execute()

        total_done += len(batch)
        print(f"done. ({total_done}/{len(articles)})")
        await asyncio.sleep(0.5)  # Be nice to the API

    print(f"\nFinished! {total_done} articles now have embeddings.")


if __name__ == "__main__":
    asyncio.run(main())
