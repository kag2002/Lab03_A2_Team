import csv
import re
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("app.services.grade_service")

class GradeService:
    def __init__(self):
        # Resolve path to the data directory dynamically
        # __file__ is /backend/app/services/grade_service.py
        # root is C2-App-023
        self.data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
        self._students_cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_data()

    def _clean_str(self, val: str) -> str:
        if not val:
            return ""
        return val.strip()

    def _extract_id_num(self, student_id: str) -> Optional[int]:
        """Extracts numerical student index from strings like 'SV001', 'SV010', '1'."""
        match = re.search(r"\d+", student_id)
        if match:
            return int(match.group(0))
        return None

    def _load_all_data(self):
        """Loads and merges reading, listening, speaking, and writing data."""
        logger.info(f"Loading candidate score CSVs from directory: {self.data_dir}")
        temp_data: Dict[int, Dict[str, Any]] = {}

        csv_files = {
            "listening": self.data_dir / "listening.csv",
            "reading": self.data_dir / "reading.csv",
            "speaking": self.data_dir / "speaking.csv",
            "writing": self.data_dir / "writing.csv"
        }

        # 1. Parse Listening Data
        if csv_files["listening"].exists():
            try:
                with open(csv_files["listening"], mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalize headers
                        cleaned_row = {self._clean_str(k): self._clean_str(v) for k, v in row.items()}
                        id_str = cleaned_row.get("ID Student") or cleaned_row.get("ID Student ")
                        if not id_str:
                            continue
                        id_num = self._extract_id_num(id_str)
                        if id_num is None:
                            continue

                        student_name = cleaned_row.get("Tên Học Sinh", "")
                        
                        temp_data[id_num] = {
                            "student_id": f"SV{id_num:03d}",
                            "student_name": student_name,
                            "listening": {
                                "P1": cleaned_row.get("P1 (6c)", ""),
                                "P2": cleaned_row.get("P2 (25c)", ""),
                                "P3": cleaned_row.get("P3 (39c)", ""),
                                "P4": cleaned_row.get("P4 (30c)", ""),
                                "skills": {
                                    "NgheYChinhBàiNgắn": cleaned_row.get("L1: Nghe ý chính (Bài ngắn)", ""),
                                    "NgheYChinhBàiDài": cleaned_row.get("L2: Nghe ý chính (Bài dài)", ""),
                                    "NgheChiTietBàiNgắn": cleaned_row.get("L3: Nghe chi tiết (Bài ngắn)", ""),
                                    "NgheChiTietBàiDài": cleaned_row.get("L4: Nghe chi tiết (Bài dài)", "")
                                }
                            }
                        }
            except Exception as e:
                logger.error(f"Failed to parse listening.csv: {e}")

        # 2. Parse Reading Data
        if csv_files["reading"].exists():
            try:
                with open(csv_files["reading"], mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cleaned_row = {self._clean_str(k): self._clean_str(v) for k, v in row.items()}
                        id_str = cleaned_row.get("ID Student") or cleaned_row.get("ID Student ")
                        if not id_str:
                            continue
                        id_num = self._extract_id_num(id_str)
                        if id_num is None:
                            continue

                        if id_num not in temp_data:
                            temp_data[id_num] = {
                                "student_id": f"SV{id_num:03d}",
                                "student_name": cleaned_row.get("Tên Học Sinh", ""),
                            }
                        
                        temp_data[id_num]["reading"] = {
                            "P5": cleaned_row.get("P5 (30c)", ""),
                            "P6": cleaned_row.get("P6 (16c)", ""),
                            "P7_DoanDon": cleaned_row.get("P7 Đoạn đơn (29c)", ""),
                            "P7_DoanKep": cleaned_row.get("P7 Đoạn kép (25c)", ""),
                            "skills": {
                                "R1_SuyLuan": cleaned_row.get("R1: Suy luận", ""),
                                "R2_DinhVi": cleaned_row.get("R2: Định vị", ""),
                                "R3_LienKet": cleaned_row.get("R3: Liên kết", ""),
                                "R4_TuVung": cleaned_row.get("R4: Từ vựng", ""),
                                "R5_NguPhap": cleaned_row.get("R5: Ngữ pháp", "")
                            }
                        }
            except Exception as e:
                logger.error(f"Failed to parse reading.csv: {e}")

        # 3. Parse Speaking Data
        if csv_files["speaking"].exists():
            try:
                with open(csv_files["speaking"], mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cleaned_row = {self._clean_str(k): self._clean_str(v) for k, v in row.items()}
                        id_str = cleaned_row.get("ID Student") or cleaned_row.get("ID Student ")
                        if not id_str:
                            continue
                        id_num = self._extract_id_num(id_str)
                        if id_num is None:
                            continue

                        if id_num not in temp_data:
                            temp_data[id_num] = {
                                "student_id": f"SV{id_num:03d}",
                                "student_name": cleaned_row.get("Tên Học Sinh", ""),
                            }

                        temp_data[id_num]["speaking"] = {
                            "C1": cleaned_row.get("C1", ""),
                            "C2": cleaned_row.get("C2", ""),
                            "C3": cleaned_row.get("C3", ""),
                            "C4": cleaned_row.get("C4", ""),
                            "C5": cleaned_row.get("C5", ""),
                            "C6": cleaned_row.get("C6", ""),
                            "C7": cleaned_row.get("C7", ""),
                            "C8": cleaned_row.get("C8", ""),
                            "C9": cleaned_row.get("C9", ""),
                            "C10": cleaned_row.get("C10", ""),
                            "C11": cleaned_row.get("C11", ""),
                            "average_C1_C2": cleaned_row.get("Điểm trung bình C1-C2", ""),
                            "total_C3_C4": cleaned_row.get("Tổng điểm C3-C4", ""),
                            "average_C5_C7": cleaned_row.get("Điểm trung bình C5-C7", ""),
                            "average_C8_C10": cleaned_row.get("Điểm trung bình C8-C10 ", "") or cleaned_row.get("Điểm trung bình C8-C10", ""),
                            "average_C11": cleaned_row.get("Điểm trung bình C11", ""),
                            "raw_total": cleaned_row.get("Tổng Thô(Max: 35)", ""),
                            "ets_score": cleaned_row.get("Quy đổi điểm ETS(0-200)", ""),
                            "level": cleaned_row.get("Level(1-8)", "")
                        }
            except Exception as e:
                logger.error(f"Failed to parse speaking.csv: {e}")

        # 4. Parse Writing Data
        if csv_files["writing"].exists():
            try:
                with open(csv_files["writing"], mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cleaned_row = {self._clean_str(k): self._clean_str(v) for k, v in row.items()}
                        id_str = cleaned_row.get("ID Student") or cleaned_row.get("ID Student ")
                        if not id_str:
                            continue
                        id_num = self._extract_id_num(id_str)
                        if id_num is None:
                            continue

                        if id_num not in temp_data:
                            temp_data[id_num] = {
                                "student_id": f"SV{id_num:03d}",
                                "student_name": cleaned_row.get("Tên Học Sinh", ""),
                            }

                        temp_data[id_num]["writing"] = {
                            "C1": cleaned_row.get("C1", ""),
                            "C2": cleaned_row.get("C2", ""),
                            "C3": cleaned_row.get("C3", ""),
                            "C4": cleaned_row.get("C4", ""),
                            "C5": cleaned_row.get("C5", ""),
                            "C6": cleaned_row.get("C6", ""),
                            "C7": cleaned_row.get("C7", ""),
                            "C8": cleaned_row.get("C8", ""),
                            "total_C1_C5": cleaned_row.get("Tổng điểm C1-C5", ""),
                            "total_C6_C7": cleaned_row.get("Tổng điểm C6-C7", ""),
                            "total_C8": cleaned_row.get("Tổng điểm C8", ""),
                            "raw_total": cleaned_row.get("Tổng Thô(Max: 31)", ""),
                            "ets_score": cleaned_row.get("Điểm ETS(0-200)", ""),
                            "level": cleaned_row.get("Level(1-9)", "")
                        }
            except Exception as e:
                logger.error(f"Failed to parse writing.csv: {e}")

        # Convert back to standard mapping keys (like "SV001") for cache
        for id_num, info in temp_data.items():
            std_id = f"SV{id_num:03d}"
            self._students_cache[std_id] = info

        logger.info(f"Successfully cached grades for {len(self._students_cache)} students.")

    def get_student_grades(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetches unified student grades by standard student ID (e.g. 'SV001')."""
        # Support various string formats (strip, uppercase, normalize)
        cleaned_id = self._clean_str(student_id).upper()
        if not cleaned_id.startswith("SV"):
            id_num = self._extract_id_num(cleaned_id)
            if id_num is not None:
                cleaned_id = f"SV{id_num:03d}"

        return self._students_cache.get(cleaned_id)

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Returns simplified grade overview of all loaded students."""
        return [
            {
                "student_id": item["student_id"],
                "student_name": item["student_name"]
            }
            for item in self._students_cache.values()
        ]

grade_service = GradeService()
