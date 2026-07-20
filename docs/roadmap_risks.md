# LỘ TRÌNH TRIỂN KHAI & QUẢN TRỊ RỦI RO

Kế hoạch chi tiết để hiện thực hóa sản phẩm trong vòng 4 tuần và cách giảm thiểu rủi ro kỹ thuật cũng như chi phí.

## 1. Lộ trình 4 Tuần Nghiên Cứu

* **Tuần 1: Thiết lập lõi và Prompt Engineering**
  * Viết mã nguồn kết nối LLM (OpenAI/Claude). Tối ưu hệ thống System Prompt để đảm bảo 100% trả về đúng định dạng cấu trúc JSON không bị gãy (Sử dụng Pydantic trong FastAPI để validate dữ liệu đầu ra).
  * Đăng ký và test kết nối API của ElevenLabs và Runway/Kling AI.
* **Tuần 2: Xây dựng Cơ sở dữ liệu và Cơ chế Task Worker xếp hàng (Queue)**
  * Thiết kế DB SQLite để kiểm soát trạng thái các thực thể.
  * Viết các hàm chạy nền xử lý tải file từ API về máy chủ.
  * Dựng cấu trúc Frontend HTML thô để đổ dữ liệu từ DB lên màn hình.
* **Tuần 3: Tích hợp Giao diện tương tác HITL & Engine Xử lý Media**
  * Hoàn thiện chức năng truyền dữ liệu ngược từ giao diện khi người dùng sửa đổi Prompt -> Chạy lại tác vụ sinh video đơn lẻ.
  * Viết module logic tính toán căn chỉnh thời gian bằng MoviePy để đồng bộ hóa hoàn toàn âm thanh và chuyển động hình ảnh.
* **Tuần 4: Đo lường, Đánh giá và Tối ưu đề tài**
  * Tiến hành chạy thử nghiệm hệ thống thực tế với 3 kịch bản truyện cổ tích khác nhau.
  * Tính toán chỉ số: Tổng chi phí API cho 1 phút video, Thời gian xử lý trung bình, Tỷ lệ can thiệp thủ công thực tế.

---

## 2. Các thách thức lớn và giải pháp giảm thiểu (Risk Mitigation)

### 2.1. Vấn đề đồng bộ nhất quán nhân vật (Character Consistency)
* **Rủi ro:** AI video tạo ra nhân vật ở phân cảnh này nhìn hoàn toàn khác phân cảnh kia.
* **Giải pháp:** Tận dụng tối đa tính năng `character_presets` trong dữ liệu JSON. Ngoài ra, thiết kế luồng tạo ảnh nhân vật mẫu trước (Text-to-Image), sau đó dùng chính ảnh cố định đó làm đầu vào (Image-to-Video) cho mọi phân cảnh để khóa gương mặt nhân vật.

### 2.2. Chi phí và Giới hạn băng thông API (Rate Limit / Cost)
* **Rủi ro:** Quá trình thử nghiệm tạo đi tạo lại hàng loạt video có thể gây tốn kém chi phí API lớn.
* **Giải pháp:** Ở giai đoạn phát triển, cấu hình module Video ở chế độ "Mock" (sử dụng video mẫu có sẵn) để kiểm tra luồng UI/UX. Chỉ kích hoạt API thật khi test thực tế kịch bản. Sử dụng độ phân giải thấp (720p) hoặc thời lượng ngắn để tối ưu chi phí.

### 2.3. Lỗi hết thời gian chờ (Timeout) khi gọi API Video
* **Rủi ro:** Tạo video bằng AI mất khá nhiều thời gian (1-3 phút), nếu gọi API theo kiểu đồng bộ, HTTP request sẽ bị ngắt kết nối giữa chừng.
* **Giải pháp:** Sử dụng cơ chế Webhook hoặc thiết kế luồng kiểm tra trạng thái chủ động (Polling với `asyncio.sleep`).
