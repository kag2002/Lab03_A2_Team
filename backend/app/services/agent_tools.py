import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root directory to system path to import security module
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from security.rule_base import validate_tool_call, validate_tool_result, SecurityContext
from app.services.grade_service import grade_service

logger = logging.getLogger("app.services.agent_tools")

# ---------------------------------------------------------------------------
# Skill-specific, score-tiered study plan playbook
# Each entry: (skill_key) -> (tier: "low"|"mid"|"high") -> plan data
# ---------------------------------------------------------------------------
SKILL_PLAYBOOK: Dict[str, Dict[str, Dict[str, Any]]] = {
    "listening": {
        "low": {
            "label": "Nền tảng yếu (dưới 50 điểm) — Cần học lại từ đầu",
            "daily": "60 phút/ngày",
            "advice": [
                "**Tuần 1-2 — Xây nền tảng từ vựng:** Nghe lại 500 từ TOEIC cơ bản (actions, objects, office, travel). Dùng Anki để luyện nhận diện âm.",
                "**Tuần 3 — Luyện Part 1 & 2:** Tập mô tả tranh bằng cách che đáp án, nghe rồi chọn. Với Part 2, nhận diện loại câu hỏi (Wh-, Yes/No, Tag question) TRƯỚC khi nghe.",
                "**Tuần 4 — Luyện Part 3 & 4:** Đọc câu hỏi TRƯỚC khi băng phát. Bắt từ khóa (subject + verb + object). Chấp nhận bỏ qua câu khó, giữ nhịp.",
            ],
            "resources": ["TOEIC Listening ETS (Level 3-4)", "Listening Power 1", "App: ELSA Speak"],
        },
        "mid": {
            "label": "Trung bình (50–74 điểm) — Cải thiện tốc độ & diệt bẫy đồng âm",
            "daily": "40 phút/ngày",
            "advice": [
                "**Giai đoạn 1 — Diệt bẫy đồng âm:** Mỗi ngày làm 10 câu Part 1-2 tập trung vào các từ phát âm gần giống (sheet/seat, leave/live). Ghi chú mỗi bẫy gặp phải.",
                "**Giai đoạn 2 — Nâng tốc xử lý Part 3-4:** Thực hành Note-taking (ghi tắt từ khóa trong lúc nghe). Làm Full Part 3 trong 13 phút chuẩn.",
                "**Giai đoạn 3 — Phân tích sai:** Mỗi câu sai phải nghe lại ít nhất 3 lần, ghi ra lý do (từ đồng âm? Câu trả lời gián tiếp? Nghe nhầm chủ thể?).",
            ],
            "resources": ["ETS TOEIC Listening RC (2023-2024)", "Hackers TOEIC Listening", "YouTube: MochaMommy – TOEIC Part 3&4 tips"],
        },
        "high": {
            "label": "Khá (75–89 điểm) — Tinh chỉnh để đạt điểm tuyệt đối",
            "daily": "25 phút/ngày",
            "advice": [
                "**Duy trì & nâng cao:** Làm 1 Full Practice Test Listening/tuần. Mục tiêu sai không quá 3 câu.",
                "**Tập trung câu cạm bẫy:** Ôn lại loại câu inference (hàm ý gì?), câu hỏi về giọng điệu (tone), và câu 'Not stated in conversation'.",
                "**Shadowing nâng cao:** Nghe và nói lại đồng thời theo các đoạn Part 4 để cải thiện phản xạ nghe.",
            ],
            "resources": ["ETS TOEIC 2024 RC+LC Vol.3", "TOEIC Trainer – Advanced Listening"],
        },
    },
    "reading": {
        "low": {
            "label": "Nền tảng yếu (dưới 50 điểm) — Cần ôn toàn bộ ngữ pháp cơ bản",
            "daily": "60 phút/ngày",
            "advice": [
                "**Tuần 1 — Ngữ pháp nền tảng (Part 5):** Ôn lại: 12 thì động từ, Dạng từ (noun/verb/adj/adv), Mệnh đề quan hệ (who/which/that), Giới từ thường gặp (in/on/at/for/since).",
                "**Tuần 2 — Từ vựng theo chủ đề:** Học 20 từ TOEIC/ngày theo chủ đề (Finance, HR, Travel, Technology). Ưu tiên collocations như 'submit a report', 'place an order'.",
                "**Tuần 3-4 — Đọc hiểu Part 6 & 7:** Luyện Skimming (đọc lướt headline + first sentence mỗi đoạn trong 30 giây). Tập bắt từ khóa câu hỏi rồi tìm vùng trả lời tương ứng.",
            ],
            "resources": ["Grammar In Use (Murphy) – Unit 1-20", "TOEIC Vocabulary 600 (Barron's)", "App: Duolingo TOEIC path"],
        },
        "mid": {
            "label": "Trung bình (50–74 điểm) — Tăng tốc đọc & giảm sai do bẫy",
            "daily": "45 phút/ngày",
            "advice": [
                "**Giai đoạn 1 — Diệt lỗi Part 5:** Làm 20 câu Part 5/ngày, tập trung vào: chọn dạng từ đúng (word form), liên từ nối (although/however/therefore), câu điều kiện (If clause).",
                "**Giai đoạn 2 — Nâng tốc Part 7:** Tăng tốc đọc lên 200 words/phút bằng cách đọc một đoạn Part 7 mỗi ngày KHÔNG tra từ điển. Luyện riêng câu hỏi NOT TRUE/EXCEPT.",
                "**Giai đoạn 3 — Double/Triple Passage:** Xác định thông tin thuộc đoạn nào TRƯỚC khi đọc kỹ — chiến lược thiết yếu để tiết kiệm thời gian.",
            ],
            "resources": ["Hackers TOEIC Reading", "TOEIC Practice ETS 2023", "Kaplan TOEIC Premier"],
        },
        "high": {
            "label": "Khá (75–89 điểm) — Hoàn thiện kỹ năng suy luận & quản lý thời gian",
            "daily": "30 phút/ngày",
            "advice": [
                "**Tập trung câu inference & paraphrase:** Ôn câu 'What does the author imply?', 'Which is closest in meaning to...?'. Đây là dạng sai phổ biến ở mức điểm cao.",
                "**Luyện quản lý thời gian:** Làm Full Reading Part (100 câu) trong 75 phút chuẩn. Mục tiêu: không bỏ trắng câu nào.",
                "**Review lỗi theo pattern:** Phân loại các câu sai thành nhóm (Ngữ pháp / Từ vựng / Suy luận đọc hiểu) để biết nhóm nào còn yếu.",
            ],
            "resources": ["ETS TOEIC 2024 Vol.3 – Reading", "Collins Practice Tests for TOEIC"],
        },
    },
    "speaking": {
        "low": {
            "label": "Nền tảng yếu (dưới 50 điểm) — Xây dựng phản xạ nói cơ bản",
            "daily": "50 phút/ngày",
            "advice": [
                "**Tuần 1 — Phát âm & Read Aloud (Part 1-2):** Đọc to 5 đoạn văn ngắn/ngày. Dùng ELSA Speak để kiểm tra phát âm. Tập trọng âm, linking sounds và intonation câu hỏi vs câu khẳng định.",
                "**Tuần 2 — Mô tả hình ảnh (Part 3):** Áp dụng công thức SPEC: Subject – Predicate – Environment – Comment. Tập mô tả 3 ảnh/ngày trong 30 giây/ảnh, ghi âm lại để nghe lại.",
                "**Tuần 3-4 — Trả lời câu hỏi (Part 4-6):** Dùng cấu trúc PREP: Point – Reason – Example – Point lại. Ghi âm và so sánh với mẫu câu trả lời native speaker.",
            ],
            "resources": ["TOEIC Speaking Official Guide (ETS)", "App: ELSA Speak", "YouTube: English Speaking Practice (Level 1)"],
        },
        "mid": {
            "label": "Trung bình (50–74 điểm) — Nâng độ lưu loát & phong phú từ vựng",
            "daily": "35 phút/ngày",
            "advice": [
                "**Giai đoạn 1 — Giảm filler words:** Ghi âm 3 câu trả lời/ngày. Đếm số lần dùng 'uh/um/er'. Mục tiêu: giảm xuống dưới 2 lần/câu trả lời 45 giây.",
                "**Giai đoạn 2 — Phong phú hóa từ vựng:** Học 10 từ chuyên ngành Business/HR/Logistics/ngày. Ứng dụng ngay vào câu trả lời mẫu Part 5-7.",
                "**Giai đoạn 3 — Đề xuất giải pháp (Part 5-6):** Luyện cấu trúc 'The best solution would be... because... However, we should also consider...' để câu trả lời có chiều sâu.",
            ],
            "resources": ["TOEIC Speaking & Writing ETS Official", "Hackers TOEIC Speaking", "App: Speechling"],
        },
        "high": {
            "label": "Khá (75–89 điểm) — Tinh chỉnh ngữ điệu & tính thuyết phục",
            "daily": "20 phút/ngày",
            "advice": [
                "**Tập trung ngữ điệu tự nhiên:** Luyện shadowing theo Business English Pod hoặc BBC Global News. Bắt chước cả nhịp, stress và pause của speaker.",
                "**Nâng độ phức tạp câu:** Thực hành dùng subordinate clauses ('Although...', 'Given that...', 'Not only... but also...') để tăng điểm Grammatical Range.",
                "**Thi thử có phản hồi:** Đăng ký 1 buổi TOEIC Speaking mock test có chấm điểm giáo viên để biết điểm còn thiếu ở tiêu chí nào chính xác.",
            ],
            "resources": ["Official TOEIC Speaking Sample Answers", "Business English Pod Podcast"],
        },
    },
    "writing": {
        "low": {
            "label": "Nền tảng yếu (dưới 50 điểm) — Xây dựng kỹ năng viết câu cơ bản",
            "daily": "50 phút/ngày",
            "advice": [
                "**Tuần 1 — Viết câu từ tranh (Part 1):** Học 3 cấu trúc nền: S+V+O (chủ động), S+be+V-ed (bị động), There is/are+N (mô tả sự tồn tại). Viết 5 câu từ ảnh mỗi ngày.",
                "**Tuần 2 — Email trả lời (Part 2):** Học format email chuẩn: Opening – Body (2-3 ý) – Closing. Luyện 3 dạng phổ biến: xác nhận đơn hàng, phản hồi khiếu nại, hẹn lịch họp.",
                "**Tuần 3-4 — Bài luận ý kiến (Part 3):** Áp dụng công thức 5 đoạn: Intro (nêu quan điểm) → Body 1 (lý do + ví dụ) → Body 2 (lý do + ví dụ) → Counterargument → Conclusion.",
            ],
            "resources": ["TOEIC Writing Official Guide (ETS)", "Oxford Writing for Business", "Grammarly (kiểm tra lỗi tự động)"],
        },
        "mid": {
            "label": "Trung bình (50–74 điểm) — Tăng độ phức tạp & giảm lỗi ngữ pháp",
            "daily": "40 phút/ngày",
            "advice": [
                "**Giai đoạn 1 — Giảm lỗi ngữ pháp:** Viết 1 đoạn 80-100 từ/ngày. Copy vào Grammarly Premium để phát hiện lỗi. Lập danh sách lỗi lặp lại để tập trung ôn.",
                "**Giai đoạn 2 — Email Part 2 nâng cao:** Học email chuyên nghiệp đủ: Lời chào → Mục đích → Chi tiết → Hành động mong muốn → Ký tên. Hoàn thành trong 10 phút.",
                "**Giai đoạn 3 — Bài luận Part 3:** Tập tạo outline trong 2 phút trước khi viết. Dùng đa dạng linking words (Furthermore, In contrast, As a result) để nối ý mạch lạc.",
            ],
            "resources": ["Hackers TOEIC Writing", "TOEIC Writing ETS Practice Sets 2023", "Hemingway Editor (đánh giá độ phức tạp câu văn)"],
        },
        "high": {
            "label": "Khá (75–89 điểm) — Tinh chỉnh lập luận & văn phong",
            "daily": "25 phút/ngày",
            "advice": [
                "**Tập trung tính thuyết phục của bài luận:** Luyện lập luận phản biện (Counterargument) và cách bác bỏ có lý (Rebuttal). Đây là yếu tố phân biệt điểm 8 với điểm 10.",
                "**Đa dạng hóa cấu trúc câu:** Mỗi bài luận cần có ít nhất 3 cấu trúc: Simple – Compound – Complex. Tránh lặp cùng một pattern.",
                "**Chấm điểm chéo:** Nộp bài cho giáo viên hoặc dùng TOEIC Writing Scoring Rubric để tự đánh giá theo 4 tiêu chí: Content / Organization / Vocabulary / Grammar.",
            ],
            "resources": ["ETS TOEIC Writing Sample Essays (Band 8-9)", "Academic Writing for Business (Cambridge)"],
        },
    },
}


def _get_skill_key(topic_str: str) -> str:
    """Extract normalized skill name from 'SkillName:score' or plain 'SkillName'."""
    base = topic_str.split(":")[0].strip().lower()
    for key in SKILL_PLAYBOOK:
        if key in base or base in key:
            return key
    return ""


def _get_score(topic_str: str) -> Optional[float]:
    """Extract numeric score from 'SkillName:score' format, e.g. 'Reading:45' -> 45.0."""
    parts = topic_str.split(":")
    if len(parts) >= 2:
        try:
            return float(parts[1].strip())
        except ValueError:
            pass
    return None


def _get_tier(score: Optional[float]) -> str:
    if score is None or score < 50:
        return "low"
    if score < 75:
        return "mid"
    return "high"


class AgentTools:
    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Validates, executes, and validates the output of the specified tool.
        If a validation error occurs, it returns an error response with findings metadata.
        """
        logger.info(f"Initiating execution for tool '{tool_name}' with args {args}...")

        # 1. Validate the tool call parameters using security rule_base
        call_decision = validate_tool_call(tool_name, args, context)
        if not call_decision.allowed:
            findings = [f"{f.rule_id}: {f.message}" for f in call_decision.findings]
            logger.warning(f"Tool call blocked by security layer: {findings}")
            return {
                "status": "error",
                "error_code": "SECURITY_BLOCKED",
                "message": "Yêu cầu gọi tool bị chặn bởi lớp bảo mật do vi phạm quy tắc an toàn dữ liệu.",
                "findings": findings
            }

        # Retrieve normalized arguments
        norm_args = call_decision.normalized_args if call_decision.normalized_args is not None else args

        # 2. Execute the tool logic
        result = {}
        try:
            if tool_name == "Grade_Search_Tool":
                student_id = norm_args.get("student_id")

                grades = grade_service.get_student_grades(student_id)
                if not grades:
                    result = {
                        "status": "error",
                        "message": f"Không tìm thấy thông tin điểm của học sinh với mã '{student_id}'."
                    }
                else:
                    result = {
                        "status": "success",
                        "student_id": grades["student_id"],
                        "student_name": grades["student_name"],
                        "listening": grades.get("listening", {}),
                        "reading": grades.get("reading", {}),
                        "speaking": grades.get("speaking", {}),
                        "writing": grades.get("writing", {})
                    }

            elif tool_name == "Score_Analyzer":
                scores = norm_args.get("scores", {})
                analysis = []
                for skill, score in scores.items():
                    if score >= 75:
                        status = "Khá/Tốt"
                    elif score >= 50:
                        status = "Cần cải thiện"
                    else:
                        status = "Yếu — Cần ưu tiên ôn tập"
                    analysis.append(f"- Kỹ năng {skill}: {score}/100 ({status})")

                weakest = min(scores.items(), key=lambda x: x[1]) if scores else ("N/A", 100)
                strongest = max(scores.items(), key=lambda x: x[1]) if scores else ("N/A", 0)

                result = {
                    "status": "success",
                    "analysis_report": "\n".join(analysis),
                    "strongest_skill": strongest[0],
                    "weakest_skill": weakest[0]
                }

            elif tool_name == "Learning_Gap_Detector":
                low_score_parts = norm_args.get("low_score_parts", [])
                gaps = []
                for part in low_score_parts:
                    part_l = part.lower()
                    if "p1" in part_l or "tranh" in part_l:
                        gaps.append(f"[{part}] Thiếu từ vựng miêu tả hoạt động/vật thể, hay bị lừa ở đáp án sử dụng từ đồng âm phát âm gần giống.")
                    elif "p2" in part_l or "hoi" in part_l:
                        gaps.append(f"[{part}] Yếu phản xạ trả lời gián tiếp hoặc các câu hỏi phủ định, câu hỏi đuôi.")
                    elif "p3" in part_l or "p4" in part_l or "thoai" in part_l or "noi" in part_l:
                        gaps.append(f"[{part}] Tốc độ đọc câu hỏi chậm, chưa biết kỹ năng quét từ khóa và bắt từ đồng nghĩa (synonyms).")
                    elif "p5" in part_l or "ngu phap" in part_l or "grammar" in part_l:
                        gaps.append(f"[{part}] Hổng kiến thức ngữ pháp cơ bản (mệnh đề quan hệ, dạng từ, liên từ nối, giới từ).")
                    elif "p6" in part_l or "dien" in part_l:
                        gaps.append(f"[{part}] Gặp khó khăn khi lựa chọn câu thích hợp nhất điền vào khoảng trống, liên kết đoạn kém.")
                    elif "p7" in part_l or "doc hieu" in part_l or "reading" in part_l:
                        gaps.append(f"[{part}] Tốc độ đọc chậm, kỹ năng Skimming & Scanning chưa tốt, hay bị bẫy ở câu hỏi suy luận (inference).")
                    else:
                        gaps.append(f"[{part}] Cần cải thiện nền tảng từ vựng, ngữ pháp và rèn luyện kỹ năng giải quyết dạng bài tương ứng.")

                result = {
                    "status": "success",
                    "detected_gaps": gaps
                }

            elif tool_name == "Study_Plan_Generator":
                weak_topics = norm_args.get("weak_topics", [])
                duration = norm_args.get("duration", "4 tuần")

                plan_sections: List[str] = []
                plan_sections.append(f"### Lộ trình học tập cá nhân hóa — {duration}\n")
                plan_sections.append(
                    "_Kế hoạch được tổng hợp dựa trên điểm thực tế của từng kỹ năng, "
                    "không phải template cố định._\n"
                )

                for i, topic in enumerate(weak_topics, 1):
                    skill_key = _get_skill_key(topic)
                    score = _get_score(topic)
                    tier = _get_tier(score)
                    playbook = SKILL_PLAYBOOK.get(skill_key)

                    skill_display = topic.split(":")[0].strip().capitalize()
                    score_display = f"{int(score)}/100" if score is not None else "chưa có điểm"

                    if not playbook:
                        # Fallback for skills not in playbook
                        plan_sections.append(
                            f"**Giai đoạn {i}: {skill_display}** (điểm: {score_display})\n"
                            f"- Ôn lại toàn bộ nền tảng kiến thức kỹ năng này từ cơ bản.\n"
                            f"- Làm bài tập thực hành có phản hồi từ giáo viên.\n"
                            f"- Thi thử định kỳ mỗi cuối tuần để theo dõi tiến độ.\n"
                        )
                        continue

                    tier_data = playbook[tier]
                    advice_lines = "\n".join(f"  {line}" for line in tier_data["advice"])
                    resources_str = " | ".join(tier_data["resources"])

                    plan_sections.append(
                        f"**Giai đoạn {i}: {skill_display}** — Điểm hiện tại: **{score_display}**\n"
                        f"> 📊 {tier_data['label']}\n"
                        f"> ⏱ Đề xuất: **{tier_data['daily']}**\n\n"
                        f"{advice_lines}\n\n"
                        f"📚 Tài liệu gợi ý: {resources_str}"
                    )

                plan_sections.append(
                    "\n---\n"
                    "**Đánh giá định kỳ:**\n"
                    "- Làm Full Mock Test (toàn phần) vào cuối mỗi tuần.\n"
                    "- So sánh điểm từng kỳ để theo dõi tiến độ thực sự.\n"
                    "- Điều chỉnh thời lượng học theo kỹ năng cải thiện nhanh/chậm nhất."
                )

                result = {
                    "status": "success",
                    "study_plan": "\n\n".join(plan_sections)
                }

            elif tool_name == "Stop":
                result = {
                    "status": "completed",
                    "message": "Nhiệm vụ đã hoàn thành xuất sắc. Dừng vòng lặp gọi công cụ."
                }
            else:
                result = {
                    "status": "error",
                    "message": f"Công cụ '{tool_name}' chưa được triển khai logic trên hệ thống."
                }
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            result = {
                "status": "error",
                "message": f"Lỗi hệ thống xảy ra khi thực thi công cụ: {str(e)}"
            }

        # 3. Validate the tool execution result using security rule_base
        res_decision = validate_tool_result(tool_name, result, context)
        if not res_decision.allowed:
            findings = [f"{f.rule_id}: {f.message}" for f in res_decision.findings]
            logger.warning(f"Tool result blocked by security layer: {findings}")
            return {
                "status": "error",
                "error_code": "SECURITY_RESULT_BLOCKED",
                "message": "Kết quả trả về của tool bị chặn bởi lớp bảo mật.",
                "findings": findings
            }

        final_res = res_decision.normalized_args if res_decision.normalized_args is not None else result
        return final_res

agent_tools = AgentTools()
