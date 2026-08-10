"""CLIP 임베딩 + FAISS 로컬 벡터 인덱스 구축."""
import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from pitt_ads_parser import PittAdsParser


def build_vector_index(parsed_records: list, index_path: str) -> None:
    model = SentenceTransformer("clip-ViT-B-32")

    corpus = [
        f"Topic: {', '.join(r['topics'])} | "
        f"Symbolism: {r['symbolic_message']} | "
        f"Action: {r['action_prompt']}"
        for r in parsed_records
    ]

    print("벡터 임베딩 생성 중...")
    embeddings = model.encode(corpus, batch_size=64, show_progress_bar=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    embeddings = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    faiss.write_index(index, index_path)
    print(f"FAISS 벡터 인덱스 구축 완료: {index.ntotal}개 항목 등록됨.")
    print(f"인덱스 저장 위치: {index_path}")


if __name__ == "__main__":
    base_dir = "./pitt_ads_dataset"
    parser = PittAdsParser(base_dir=base_dir)
    dataset = parser.parse_dataset()

    valid_records = [r for r in dataset if r["is_valid_media"]]
    print(
        f"전체 {len(dataset)}개 중 {len(valid_records)}개 유효 레코드로 인덱스 구축."
    )

    index_path = os.path.join(base_dir, "pitt_ads_faiss.index")
    build_vector_index(valid_records, index_path)

    id_map_path = os.path.join(base_dir, "pitt_ads_id_map.json")
    id_map = [r["ad_id"] for r in valid_records]
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    print(f"ID 매핑 저장: {id_map_path}")
