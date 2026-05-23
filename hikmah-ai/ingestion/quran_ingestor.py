"""
Quran ingestion pipeline.

Downloads the Quran dataset (English translation + Arabic) from HuggingFace,
chunks it, generates embeddings, and stores vectors in ChromaDB.

Dataset used: "tarteel-ai/everyayah" or a bundled CSV fallback.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from tqdm import tqdm

from embeddings.embedder import get_embedder
from utils.config import settings
from utils.logger import logger

# Surah names (1-114)
SURAH_NAMES = [
    "Al-Fatihah", "Al-Baqarah", "Ali 'Imran", "An-Nisa", "Al-Ma'idah",
    "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
    "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
    "An-Nahl", "Al-Isra", "Al-Kahf", "Maryam", "Ta-Ha",
    "Al-Anbya", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan",
    "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum",
    "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir",
    "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
    "Fussilat", "Ash-Shura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah",
    "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
    "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman",
    "Al-Waqi'ah", "Al-Hadid", "Al-Mujadila", "Al-Hashr", "Al-Mumtahanah",
    "As-Saf", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq",
    "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
    "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah",
    "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at", "Abasa",
    "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj",
    "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Ash-Shams", "Al-Layl", "Ad-Duha", "Ash-Sharh", "At-Tin",
    "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat",
    "Al-Qari'ah", "At-Takathur", "Al-'Asr", "Al-Humazah", "Al-Fil",
    "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
]

# Sample Quran data — a representative subset used when the full dataset
# is not yet downloaded. The ingestion script will prefer the full dataset
# from HuggingFace when available.
SAMPLE_QURAN_DATA = [
    {
        "surah_number": 1, "surah_name": "Al-Fatihah", "ayah_number": 1,
        "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "english": "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
    },
    {
        "surah_number": 1, "surah_name": "Al-Fatihah", "ayah_number": 2,
        "arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        "english": "All praise is due to Allah, Lord of the worlds.",
    },
    {
        "surah_number": 1, "surah_name": "Al-Fatihah", "ayah_number": 5,
        "arabic": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        "english": "It is You we worship and You we ask for help.",
    },
    {
        "surah_number": 2, "surah_name": "Al-Baqarah", "ayah_number": 255,
        "arabic": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
        "english": "Allah — there is no deity except Him, the Ever-Living, the Sustainer of existence. (Ayat al-Kursi)",
    },
    {
        "surah_number": 2, "surah_name": "Al-Baqarah", "ayah_number": 286,
        "arabic": "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا",
        "english": "Allah does not burden a soul beyond that it can bear.",
    },
    {
        "surah_number": 3, "surah_name": "Ali 'Imran", "ayah_number": 103,
        "arabic": "وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا",
        "english": "And hold firmly to the rope of Allah all together and do not become divided.",
    },
    {
        "surah_number": 3, "surah_name": "Ali 'Imran", "ayah_number": 185,
        "arabic": "كُلُّ نَفْسٍ ذَائِقَةُ الْمَوْتِ",
        "english": "Every soul will taste death.",
    },
    {
        "surah_number": 4, "surah_name": "An-Nisa", "ayah_number": 36,
        "arabic": "وَاعْبُدُوا اللَّهَ وَلَا تُشْرِكُوا بِهِ شَيْئًا",
        "english": "Worship Allah and associate nothing with Him, and to parents do good.",
    },
    {
        "surah_number": 17, "surah_name": "Al-Isra", "ayah_number": 23,
        "arabic": "وَقَضَىٰ رَبُّكَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَانًا",
        "english": "Your Lord has decreed that you worship none but Him, and that you be kind to parents.",
    },
    {
        "surah_number": 49, "surah_name": "Al-Hujurat", "ayah_number": 13,
        "arabic": "يَا أَيُّهَا النَّاسُ إِنَّا خَلَقْنَاكُم مِّن ذَكَرٍ وَأُنثَىٰ",
        "english": "O mankind, indeed We have created you from male and female and made you peoples and tribes that you may know one another.",
    },
    {
        "surah_number": 55, "surah_name": "Ar-Rahman", "ayah_number": 13,
        "arabic": "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ",
        "english": "So which of the favors of your Lord would you deny?",
    },
    {
        "surah_number": 94, "surah_name": "Ash-Sharh", "ayah_number": 5,
        "arabic": "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا",
        "english": "For indeed, with hardship will be ease.",
    },
    {
        "surah_number": 94, "surah_name": "Ash-Sharh", "ayah_number": 6,
        "arabic": "إِنَّ مَعَ الْعُسْرِ يُسْرًا",
        "english": "Indeed, with hardship will be ease.",
    },
    {
        "surah_number": 112, "surah_name": "Al-Ikhlas", "ayah_number": 1,
        "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
        "english": "Say, He is Allah, [who is] One.",
    },
    {
        "surah_number": 112, "surah_name": "Al-Ikhlas", "ayah_number": 2,
        "arabic": "اللَّهُ الصَّمَدُ",
        "english": "Allah, the Eternal Refuge.",
    },
]


class QuranIngestor:
    """
    Ingests Quran verses into ChromaDB.

    Priority order for data source:
    1. data/quran.json  (user-provided full dataset)
    2. HuggingFace datasets (downloaded on first run)
    3. Built-in sample data (fallback for offline / demo use)
    """

    def __init__(self) -> None:
        self.embedder = get_embedder()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_quran_collection,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self, force: bool = False) -> int:
        """
        Run the full ingestion pipeline.
        Returns the number of verses ingested.
        """
        if not force and self.collection.count() > 0:
            logger.info(
                f"Quran collection already has {self.collection.count()} verses. "
                "Pass force=True to re-ingest."
            )
            return self.collection.count()

        verses = self._load_data()
        logger.info(f"Ingesting {len(verses)} Quran verses …")
        self._upsert_verses(verses)
        logger.info(f"Quran ingestion complete. Total: {self.collection.count()} verses.")
        return self.collection.count()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> List[Dict[str, Any]]:
        local_path = Path("data/quran.json")
        if local_path.exists():
            logger.info(f"Loading Quran data from {local_path}")
            with open(local_path, encoding="utf-8") as f:
                return json.load(f)

        try:
            return self._load_from_huggingface()
        except Exception as exc:
            logger.warning(f"HuggingFace download failed ({exc}). Using sample data.")
            return SAMPLE_QURAN_DATA

    def _load_from_huggingface(self) -> List[Dict[str, Any]]:
        """
        Attempt to load the Quran dataset from HuggingFace.
        Uses 'legacy-datasets/quran_en' which provides surah/ayah/text fields.
        """
        from datasets import load_dataset  # lazy import

        logger.info("Downloading Quran dataset from HuggingFace …")
        ds = load_dataset("legacy-datasets/quran_en", split="train", trust_remote_code=True)

        verses: List[Dict[str, Any]] = []
        for row in ds:
            surah_num = int(row.get("surah", 0))
            surah_name = SURAH_NAMES[surah_num - 1] if 1 <= surah_num <= 114 else "Unknown"
            verses.append(
                {
                    "surah_number": surah_num,
                    "surah_name": surah_name,
                    "ayah_number": int(row.get("ayah", 0)),
                    "arabic": row.get("arabic", ""),
                    "english": row.get("text", ""),
                }
            )

        # Cache locally
        Path("data").mkdir(exist_ok=True)
        with open("data/quran.json", "w", encoding="utf-8") as f:
            json.dump(verses, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached {len(verses)} verses to data/quran.json")
        return verses

    # ------------------------------------------------------------------
    # ChromaDB upsert
    # ------------------------------------------------------------------

    def _upsert_verses(self, verses: List[Dict[str, Any]], batch_size: int = 100) -> None:
        for i in tqdm(range(0, len(verses), batch_size), desc="Ingesting Quran"):
            batch = verses[i : i + batch_size]

            ids, documents, metadatas = [], [], []
            for v in batch:
                doc_id = f"quran_{v['surah_number']}_{v['ayah_number']}"
                # Text used for embedding: English translation (BGE is English-optimised)
                text = (
                    f"Surah {v['surah_name']} ({v['surah_number']}:{v['ayah_number']}) — "
                    f"{v['english']}"
                )
                ids.append(doc_id)
                documents.append(text)
                metadatas.append(
                    {
                        "source": "quran",
                        "surah_number": v["surah_number"],
                        "surah_name": v["surah_name"],
                        "ayah_number": v["ayah_number"],
                        "arabic": v.get("arabic", ""),
                        "english": v["english"],
                        "citation": f"Quran {v['surah_number']}:{v['ayah_number']} ({v['surah_name']})",
                    }
                )

            embeddings = self.embedder.embed_documents(documents)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
