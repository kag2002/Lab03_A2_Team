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
                # course_name = norm_args.get("course_name") # available if needed
                
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
                    status = "Khá/Tốt" if score >= 80 else ("Cần cải thiện" if score >= 50 else "Yếu")
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
                    elif "p2" in part_l or "hỏi" in part_l:
                        gaps.append(f"[{part}] Yếu phản xạ trả lời gián tiếp hoặc các câu hỏi phủ định, câu hỏi đuôi.")
                    elif "p3" in part_l or "p4" in part_l or "đoạn thoại" in part_l or "bài nói" in part_l:
                        gaps.append(f"[{part}] Tốc độ đọc câu hỏi chậm, chưa biết kỹ năng quét từ khóa và bắt từ đồng nghĩa (synonyms).")
                    elif "p5" in part_l or "ngữ pháp" in part_l:
                        gaps.append(f"[{part}] Hổng kiến thức ngữ pháp cơ bản (mệnh đề quan hệ, dạng từ, liên từ nối, giới từ).")
                    elif "p6" in part_l or "điền" in part_l:
                        gaps.append(f"[{part}] Gặp khó khăn khi lựa chọn câu thích hợp nhất điền vào khoảng trống, liên kết đoạn kém.")
                    elif "p7" in part_l or "đọc hiểu" in part_l:
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
                
                plan_steps = []
                plan_steps.append(f"### Lộ trình học cá nhân hóa trong thời gian {duration}:")
                for i, topic in enumerate(weak_topics, 1):
                    plan_steps.append(f"**Giai đoạn {i}: Cải thiện kỹ năng {topic}**")
                    plan_steps.append(f"- Học từ vựng chuyên đề & cấu trúc ngữ pháp liên quan đến {topic} (30 phút/ngày).")
                    plan_steps.append(f"- Thực hành giải đề chi tiết các phần liên quan, phân tích sâu các câu làm sai để tránh lặp lại lỗi cũ.")
                    plan_steps.append(f"- Làm bài test rút gọn (Mini-test) giới hạn thời gian để tăng tốc độ phản xạ.")
                plan_steps.append("**Đánh giá định kỳ:** Thực hành thi thử toàn phần (Full Mock Test) mỗi cuối tuần để theo dõi sự cải thiện điểm số.")
                
                result = {
                    "status": "success",
                    "study_plan": "\n\n".join(plan_steps)
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
