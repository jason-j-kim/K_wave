"""Pitt Ads Dataset 메타데이터 파싱 및 구조화."""
import json
import os
from typing import Any


class PittAdsParser:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.annotations_dir = os.path.join(base_dir, "annotations")
        self.images_dir = os.path.join(base_dir, "images")

    def load_json(self, filename: str) -> dict[str, Any]:
        filepath = os.path.join(self.annotations_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_dataset(self) -> list[dict[str, Any]]:
        symbolism_data = self.load_json("symbolism.json")
        qa_data = self.load_json("qa.json")

        parsed_records = []
        for img_id, sym_info in symbolism_data.items():
            img_path = os.path.join(self.images_dir, f"{img_id}.jpg")
            img_qa = qa_data.get(img_id, {})

            record = {
                "ad_id": f"pitt_{img_id}",
                "image_path": img_path if os.path.exists(img_path) else None,
                "topics": sym_info.get("topics", []),
                "symbolic_message": sym_info.get("symbolism", ""),
                "action_prompt": sym_info.get("action", ""),
                "qa_pairs": img_qa.get("questions", []),
                "is_valid_media": os.path.exists(img_path),
            }
            parsed_records.append(record)
        return parsed_records


if __name__ == "__main__":
    parser = PittAdsParser(base_dir="./pitt_ads_dataset")
    dataset = parser.parse_dataset()
    print(f"파싱 완료: 총 {len(dataset)}개 광고 레코드가 인덱싱 준비되었습니다.")

    out_path = "./pitt_ads_dataset/parsed_records.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"파싱 결과 저장: {out_path}")
