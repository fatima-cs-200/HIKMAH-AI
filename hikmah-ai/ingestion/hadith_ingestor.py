"""
Sahih Bukhari hadith ingestion pipeline.

Data source priority:
1. data/sahih_bukhari.json  (user-provided)
2. HuggingFace datasets
3. Built-in sample data (offline / demo fallback)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from tqdm import tqdm

from embeddings.embedder import get_embedder
from utils.config import settings
from utils.logger import logger


# Representative sample of Sahih Bukhari ahadith for offline / demo use
SAMPLE_HADITH_DATA = [
    {
        "book_name": "Revelation",
        "chapter": "How the Divine Revelation started",
        "hadith_number": 1,
        "narrator": "Umar ibn al-Khattab",
        "text": (
            "The reward of deeds depends upon the intentions and every person will get "
            "the reward according to what he has intended. So whoever emigrated for worldly "
            "benefits or for a woman to marry, his emigration was for what he emigrated for."
        ),
    },
    {
        "book_name": "Belief",
        "chapter": "The statement of the Prophet: Islam is based on five pillars",
        "hadith_number": 8,
        "narrator": "Ibn Umar",
        "text": (
            "Islam is based on five pillars: testifying that there is no god but Allah and "
            "that Muhammad is His Messenger, establishing prayer, paying Zakat, performing "
            "Hajj, and fasting in Ramadan."
        ),
    },
    {
        "book_name": "Knowledge",
        "chapter": "Seeking knowledge",
        "hadith_number": 79,
        "narrator": "Abdullah ibn Amr",
        "text": (
            "Convey from me even if it is one verse."
        ),
    },
    {
        "book_name": "Prayer",
        "chapter": "The times of prayer",
        "hadith_number": 521,
        "narrator": "Anas ibn Malik",
        "text": (
            "The Prophet said: Whoever prays the morning prayer in congregation and then "
            "remains seated remembering Allah until the sun rises, then prays two units of "
            "prayer, will have a reward like that of Hajj and Umrah."
        ),
    },
    {
        "book_name": "Fasting",
        "chapter": "The virtue of fasting",
        "hadith_number": 1904,
        "narrator": "Abu Hurairah",
        "text": (
            "Allah said: Every deed of the son of Adam is for him except fasting; it is for "
            "Me and I shall reward for it. Fasting is a shield. When any of you is fasting "
            "he should not speak obscenely or shout, and if anyone insults him or tries to "
            "fight him he should say: I am fasting."
        ),
    },
    {
        "book_name": "Zakat",
        "chapter": "Obligation of Zakat",
        "hadith_number": 1395,
        "narrator": "Ibn Abbas",
        "text": (
            "The Prophet sent Muadh to Yemen and said: Invite the people to testify that "
            "none has the right to be worshipped but Allah and I am Allah's Messenger, and "
            "if they obey you to do so, then teach them that Allah has enjoined on them five "
            "prayers in every day and night."
        ),
    },
    {
        "book_name": "Good Manners",
        "chapter": "Kindness and good character",
        "hadith_number": 6018,
        "narrator": "Abu Hurairah",
        "text": (
            "The Prophet said: The most complete of the believers in faith is the one with "
            "the best character among them, and the best of you are those who are best to "
            "their women."
        ),
    },
    {
        "book_name": "Virtues",
        "chapter": "The virtues of the Quran",
        "hadith_number": 5027,
        "narrator": "Uthman ibn Affan",
        "text": (
            "The best among you are those who learn the Quran and teach it."
        ),
    },
    {
        "book_name": "Patients",
        "chapter": "Patience during illness",
        "hadith_number": 5641,
        "narrator": "Abu Said al-Khudri",
        "text": (
            "No fatigue, nor disease, nor sorrow, nor sadness, nor hurt, nor distress "
            "befalls a Muslim, even if it were the prick he receives from a thorn, but that "
            "Allah expiates some of his sins for that."
        ),
    },
    {
        "book_name": "Tawheed",
        "chapter": "Oneness of Allah",
        "hadith_number": 7373,
        "narrator": "Abu Hurairah",
        "text": (
            "Allah said: I am as My servant thinks I am. I am with him when he makes "
            "mention of Me. If he makes mention of Me to himself, I make mention of him to "
            "Myself; and if he makes mention of Me in an assembly, I make mention of him in "
            "an assembly better than it."
        ),
    },
    {
        "book_name": "Hajj",
        "chapter": "Virtues of Hajj",
        "hadith_number": 1521,
        "narrator": "Abu Hurairah",
        "text": (
            "Whoever performs Hajj for Allah's pleasure and does not have sexual relations "
            "with his wife, and does not do evil or sins then he will return after Hajj free "
            "from all sins as if he were born anew."
        ),
    },
    {
        "book_name": "Nikah",
        "chapter": "Marriage",
        "hadith_number": 5063,
        "narrator": "Anas ibn Malik",
        "text": (
            "The Prophet said: When a man marries he has fulfilled half of the religion; "
            "so let him fear Allah regarding the remaining half."
        ),
    },
]


class HadithIngestor:
    """
    Ingests Sahih Bukhari ahadith into ChromaDB.
    """

    def __init__(self) -> None:
        self.embedder = get_embedder()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_hadith_collection,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self, force: bool = False) -> int:
        if not force and self.collection.count() > 0:
            logger.info(
                f"Hadith collection already has {self.collection.count()} records. "
                "Pass force=True to re-ingest."
            )
            return self.collection.count()

        ahadith = self._load_data()
        logger.info(f"Ingesting {len(ahadith)} ahadith …")
        self._upsert_ahadith(ahadith)
        logger.info(f"Hadith ingestion complete. Total: {self.collection.count()} records.")
        return self.collection.count()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> List[Dict[str, Any]]:
        local_path = Path("data/sahih_bukhari.json")
        if local_path.exists():
            logger.info(f"Loading hadith data from {local_path}")
            with open(local_path, encoding="utf-8") as f:
                return json.load(f)

        try:
            return self._load_from_huggingface()
        except Exception as exc:
            logger.warning(f"HuggingFace download failed ({exc}). Using sample data.")
            return SAMPLE_HADITH_DATA

    def _load_from_huggingface(self) -> List[Dict[str, Any]]:
        from datasets import load_dataset  # lazy import

        logger.info("Downloading Sahih Bukhari dataset from HuggingFace …")
        ds = load_dataset("hadith-datasets/sahih-bukhari-english", split="train", trust_remote_code=True)

        ahadith: List[Dict[str, Any]] = []
        for row in ds:
            ahadith.append(
                {
                    "book_name": row.get("book_name", "Sahih Bukhari"),
                    "chapter": row.get("chapter_name", ""),
                    "hadith_number": int(row.get("hadith_number", 0)),
                    "narrator": row.get("narrator", ""),
                    "text": row.get("text", ""),
                }
            )

        Path("data").mkdir(exist_ok=True)
        with open("data/sahih_bukhari.json", "w", encoding="utf-8") as f:
            json.dump(ahadith, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached {len(ahadith)} ahadith to data/sahih_bukhari.json")
        return ahadith

    # ------------------------------------------------------------------
    # ChromaDB upsert
    # ------------------------------------------------------------------

    def _upsert_ahadith(self, ahadith: List[Dict[str, Any]], batch_size: int = 100) -> None:
        for i in tqdm(range(0, len(ahadith), batch_size), desc="Ingesting Hadith"):
            batch = ahadith[i : i + batch_size]

            ids, documents, metadatas = [], [], []
            for h in batch:
                doc_id = f"bukhari_{h['hadith_number']}"
                text = (
                    f"Sahih Bukhari — {h['book_name']}, {h['chapter']}. "
                    f"Narrated by {h['narrator']}: {h['text']}"
                )
                ids.append(doc_id)
                documents.append(text)
                metadatas.append(
                    {
                        "source": "sahih_bukhari",
                        "book_name": h["book_name"],
                        "chapter": h["chapter"],
                        "hadith_number": h["hadith_number"],
                        "narrator": h.get("narrator", ""),
                        "text": h["text"],
                        "citation": f"Sahih Bukhari #{h['hadith_number']} — {h['book_name']}",
                    }
                )

            embeddings = self.embedder.embed_documents(documents)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
