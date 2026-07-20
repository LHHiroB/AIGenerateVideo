# QUY TRÌNH VẬN HÀNH CHI TIẾT (PIPELINE STEP-BY-STEP)

Quy trình tự động kết hợp sự kiểm duyệt thủ công (Human-in-the-loop) để tối ưu hóa chất lượng sản phẩm video.

## Quy trình 4 bước chính

### Bước 1: Khởi tạo & Tạo kịch bản cấu trúc (Tự động)
1. Người dùng nhập tên đề tài: "Truyện Thánh Gióng".
2. Backend gửi yêu cầu kèm **System Prompt** tới LLM.
   * *System Prompt Chiến lược:* Yêu cầu LLM hoạt động như một Giám đốc nghệ thuật kiêm Biên kịch. Đảm bảo tính nhất quán bằng cách tự động xây dựng `character_presets` và ánh xạ các preset này vào `visual_prompt` của từng phân cảnh.

### Bước 2: Phân rã dữ liệu & Lập lịch tác vụ (Tự động)
1. Hệ thống tiếp nhận JSON từ LLM, bóc tách thông tin và ghi vào bảng `projects` và `scenes` với trạng thái `pending`.
2. Hệ thống kích hoạt đồng thời 2 Task workers chạy nền:
   * **Task Audio:** Duyệt qua các dòng `narration`, gọi sang ElevenLabs API để chuyển đổi Text-to-Speech $\rightarrow$ Lưu file vào `/static/audio/{project_id}_{scene_index}.mp3`.
   * **Task Video:** Duyệt qua các dòng `visual_prompt`. Backend tự động gộp chuỗi: `Final Prompt = global_art_style + character_presets[character_focus] + visual_prompt`. Gọi sang AI Video API (Runway/Kling) $\rightarrow$ Lưu file nháp vào `/static/video/{project_id}_{scene_index}.mp4`.

### Bước 3: Giao diện kiểm duyệt Human-in-the-loop (Thủ công - 20%)
Khi các tác vụ tự động hoàn tất, Project chuyển sang trạng thái `pending_review`. Người dùng mở giao diện UI HTML để kiểm duyệt:
1. **Duyệt luồng:** Xem tuần tự từng phân cảnh gồm Video chạy song song với Tiếng đọc thoại.
2. **Xử lý ngoại lệ (Sửa lỗi hình ảnh):** Nếu phân cảnh có hình ảnh không đạt yêu cầu, người dùng chỉnh sửa trực tiếp chuỗi `visual_prompt` trên ô nhập liệu và bấm **"Regenerate Video"**.
3. Backend nhận tín hiệu, chạy riêng lẻ phân cảnh đó, cập nhật lại DB và tải file mới đè lên file cũ.

### Bước 4: Hợp nhất và Xuất bản thành phẩm (Tự động)
Sau khi người dùng nhấn **"Approve & Merge"**:
1. Backend gọi module xử lý Media lấy toàn bộ các file hình và tiếng đã hoàn thiện từ DB.
2. Ép thời gian hiển thị của video phân cảnh bằng đúng thời gian chạy của file audio phân cảnh tương ứng.
3. Sử dụng `concatenate_videoclips` của MoviePy để nối mượt và xuất file `final_output.mp4`.
