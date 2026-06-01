# Individual Report: Lab 3 - Chatbot vs ReAct Agent

* **Student Name**: Phạm Thành Nam
* **Student ID**: 2A202600832
* **Date**: June 2026

---

# I. Đóng góp kỹ thuật (15 điểm)

## Mô tả đóng góp

Trong bài Lab 3, nhiệm vụ chính của tôi là thiết kế và triển khai hệ thống logging cho ReAct Agent nhằm theo dõi toàn bộ quá trình suy luận và thực thi của agent. Hệ thống logging được xây dựng để ghi nhận đầy đủ các chỉ số quan trọng như thời gian thực thi, số lượng token sử dụng và các bước suy luận của agent.

## Các module đã triển khai

* `AgentLogger`
* Tích hợp logging vào vòng lặp ReAct Agent
* Ghi nhận các sự kiện:

  * User Input
  * LLM Call
  * Tool Call
  * Tool Result
  * Final Answer

## Điểm nổi bật trong mã nguồn

### 1. Quản lý Session và Step

Mỗi phiên làm việc được gán một `session_id` duy nhất bằng UUID.

```python
self.session_id = session_id or str(uuid.uuid4())
self.step_counter = 1
```

Mỗi sự kiện phát sinh trong quá trình chạy agent đều được đánh số thứ tự tăng dần giúp dễ dàng theo dõi luồng thực thi.

### 2. Ghi nhận Timestamp

```python
"timestamp": datetime.utcnow().isoformat() + "Z"
```

Mọi log đều chứa thời gian theo chuẩn UTC ISO-8601 để đảm bảo tính nhất quán giữa các môi trường triển khai.

### 3. Đo Latency

Thời gian thực thi của từng lời gọi LLM hoặc Tool được đo riêng biệt.

```python
start_time = time.time()

response = llm.invoke(messages)

latency_ms = int((time.time() - start_time) * 1000)
```

Chỉ số này giúp đánh giá hiệu năng của hệ thống và xác định các thành phần gây chậm.

### 4. Theo dõi Token Usage

```python
input_tokens = response.usage["prompt_tokens"]
output_tokens = response.usage["completion_tokens"]
```

Thông tin token được lấy trực tiếp từ phản hồi của API để phục vụ việc theo dõi chi phí sử dụng mô hình.

## Tương tác với vòng lặp ReAct

Hệ thống logging được tích hợp trực tiếp vào vòng lặp ReAct.

Mỗi bước của agent đều được ghi lại theo thứ tự:

1. User Input
2. LLM Call
3. Tool Call
4. Tool Result
5. Final Answer

Ngoài các thông tin cơ bản, log còn lưu:

* Thought của agent
* Tên mô hình sử dụng
* Dữ liệu đầu vào
* Dữ liệu đầu ra

Điều này giúp dễ dàng tái hiện lại toàn bộ quá trình suy luận của agent khi cần phân tích hoặc debug.

---

# II. Nghiên cứu tình huống Debugging (10 điểm)

## Mô tả vấn đề

Trong quá trình kiểm thử, agent nhiều lần gọi lại cùng một tool mặc dù đã nhận được kết quả hợp lệ từ lần gọi trước.

Ví dụ:

```text
Action: Grade_Search_Tool(student_id="SV001")

Observation: Đã tìm thấy điểm số.

Action: Grade_Search_Tool(student_id="SV001")
```

Hiện tượng này làm tăng số lần gọi tool không cần thiết, tăng độ trễ và tiêu tốn thêm token.

## Nguồn log

```json
{
  "step": 8,
  "event": "tool_result",
  "tool_name": "Grade_Search_Tool"
}

{
  "step": 9,
  "event": "llm_call",
  "output": "Action: Grade_Search_Tool(student_id='SV001')"
}
```

Thông qua log có thể thấy agent tiếp tục gọi lại tool ngay sau khi đã nhận được kết quả.

## Chẩn đoán nguyên nhân

Nguyên nhân xuất phát từ prompt của agent.

Prompt chưa hướng dẫn rõ rằng khi đã có dữ liệu cần thiết thì agent phải chuyển sang bước phân tích thay vì tiếp tục gọi lại tool.

Do đó mô hình không nhận biết được khi nào cần dừng thu thập dữ liệu.

## Giải pháp

Tôi đã bổ sung thêm ví dụ vào system prompt:

```text
Thought: Tôi đã có dữ liệu điểm số.

Action: Score_Analyzer(...)
```

thay vì:

```text
Action: Grade_Search_Tool(...)
```

Sau khi cập nhật prompt, agent đã chuyển sang bước phân tích đúng như mong muốn và không còn lặp lại hành động cũ.

Hệ thống logging đóng vai trò quan trọng trong việc xác định nguyên nhân vì toàn bộ Thought, Action và Observation đều được ghi lại đầy đủ.

---

# III. Nhận xét cá nhân: Chatbot và ReAct Agent (10 điểm)

## 1. Khả năng suy luận

So với chatbot thông thường, ReAct Agent có khả năng suy luận tốt hơn trong các tác vụ nhiều bước.

Chatbot thường tạo câu trả lời trực tiếp từ tri thức của mô hình.

Trong khi đó, ReAct Agent hoạt động theo chu trình:

```text
Thought → Action → Observation
```

Nhờ đó agent có thể:

* Chia nhỏ bài toán
* Lựa chọn tool phù hợp
* Điều chỉnh hành động dựa trên kết quả nhận được

Đối với các bài toán yêu cầu phân tích dữ liệu hoặc lập kế hoạch học tập, ReAct Agent cho kết quả chính xác và có cấu trúc hơn.

## 2. Độ tin cậy

Trong các tác vụ đơn giản, ReAct Agent đôi khi hoạt động kém hiệu quả hơn chatbot.

Ví dụ:

* Câu hỏi kiến thức đơn giản
* Chào hỏi
* Truy vấn một bước

Nguyên nhân:

* Cần thêm bước suy luận
* Tốn nhiều token hơn
* Có thể chọn sai tool

Trong những trường hợp này chatbot thường phản hồi nhanh hơn và tiết kiệm tài nguyên hơn.

## 3. Vai trò của Observation

Observation là yếu tố quan trọng nhất giúp agent đưa ra quyết định tiếp theo.

Ví dụ:

```text
Observation:
Writing = 4.5
Speaking = 5.0
```

Agent có thể suy luận:

```text
Thought:
Writing là kỹ năng yếu nhất.
Cần gọi Learning_Gap_Detector.
```

Nếu không có Observation, agent sẽ không có thông tin để điều chỉnh hành động ở bước tiếp theo.

Do đó Observation đóng vai trò như một cơ chế phản hồi giúp agent hoạt động linh hoạt hơn.

---

# IV. Hướng phát triển trong tương lai (5 điểm)

## Khả năng mở rộng

Sử dụng cơ chế xử lý bất đồng bộ (Asynchronous Processing) kết hợp với hàng đợi tác vụ như:

* Celery
* RabbitMQ
* Kafka

để hỗ trợ nhiều người dùng đồng thời.

## An toàn

Xây dựng một Supervisor Agent có nhiệm vụ kiểm tra:

* Action được sinh ra
* Tool được lựa chọn
* Kết quả cuối cùng

trước khi thực thi.

Điều này giúp giảm rủi ro từ các hành động không mong muốn hoặc hallucination.

## Hiệu năng

Áp dụng Vector Database để quản lý mô tả tool và truy xuất ngữ cảnh.

Lợi ích:

* Giảm kích thước prompt
* Tăng tốc độ lựa chọn tool
* Mở rộng tốt khi số lượng tool tăng lên

Ngoài ra có thể bổ sung thêm các chỉ số:

* Tổng chi phí sử dụng mô hình
* Tỷ lệ thành công của tác vụ
* Thời gian hoàn thành trung bình

để phục vụ việc giám sát hệ thống trong môi trường thực tế.

---

# Kết luận

Thông qua bài Lab 3, tôi hiểu rõ hơn sự khác biệt giữa Chatbot truyền thống và ReAct Agent. Đóng góp chính của tôi là xây dựng hệ thống logging cho agent nhằm ghi nhận đầy đủ Timestamp, Latency và Token Usage. Hệ thống này giúp tăng khả năng quan sát, hỗ trợ debug hiệu quả và tạo nền tảng cho việc mở rộng cũng như tối ưu hóa agent trong các dự án thực tế.
