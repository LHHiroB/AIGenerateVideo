# TÀI LIỆU NGHIÊN CỨU & KẾ HOẠCH PHÁT TRIỂN
## HỆ THỐNG TẠO VIDEO AI TỰ ĐỘNG (80% AUTOMATED - HUMAN-IN-THE-LOOP)

---

## 1. TỔNG QUAN ĐỀ TÀI

### 1.1. Mục tiêu
Nghiên cứu và xây dựng một hệ thống (Pipeline) tự động hóa quá trình sản xuất video ngắn (Kịch bản, Phân cảnh, Giọng đọc, Tạo video, Hợp nhất) dựa trên công nghệ Generative AI. 
* **Tỷ lệ tự động hóa (80%):** Từ ý tưởng ban đầu -> Kịch bản chi tiết -> Chia phân cảnh -> Tạo giọng đọc -> Tạo video nháp -> Ghép thành phẩm.
* **Tỷ lệ can thiệp thủ công (20% - Human-in-the-loop):** Đánh giá chất lượng phân cảnh, chỉnh sửa Prompt và yêu cầu AI tạo lại (Regenerate) các phân cảnh chưa đạt yêu cầu trước khi xuất video cuối cùng.

### 1.2. Đối tượng thử nghiệm đầu tiên
* **Đề tài:** Truyện cổ tích Việt Nam (Ví dụ: Sự tích Thánh Gióng).
* **Đặc tính:** Đòi hỏi tính đồng bộ về bối cảnh cổ trang và tính nhất quán của nhân vật qua nhiều phân cảnh khác nhau.

---

## 2. KIẾN TRÚC HỆ THỐNG & CÔNG NGHỆ (TECH STACK)

Hệ thống được thiết kế theo mô hình Monolith tối giản để tối ưu tốc độ phát triển và thử nghiệm nghiên cứu.

```
+--------------------------------------------------------------+
|                    FRONTEND (HTML5 / CSS3 / JS)              |
|          - Dashboard quản lý Project                         |
|          - Giao diện Duyệt Phân Cảnh & Thay đổi Prompt      |
+------------------------------+-------------------------------+
                               | API Requests (REST)
                               v
+--------------------------------------------------------------+
|                     BACKEND (Python / FastAPI)               |
|   - State Machine Manager (SQLite)                           |
|   - AI Orchestrating Engine (Quản lý luồng gọi API)          |
|   - Video & Audio Processing Suite (MoviePy & FFmpeg)        |
+---+----------------------+-----------------------+-----------+
    |                      |                       |
    v                      v                       v
[LLM APIs]          [Audio APIs]            [Video APIs]
- OpenAI GPT-4o     - ElevenLabs API        - Runway Gen-3
- Claude 3.5        - OpenAI TTS            - Kling AI / Luma
```

* **Backend Framework:** `FastAPI` (Python). Hỗ trợ cơ chế `async/await` cực tốt cho việc gọi hàng loạt (Parallel/Concurrent) API từ các nhà cung cấp bên thứ ba nhằm tiết kiệm thời gian tạo video.
* **Database:** `SQLite` + `SQLAlchemy` (ORM). Nhẹ nhàng, không cần cài đặt server độc lập, lưu trữ toàn bộ trạng thái (State) của project và các phân cảnh.
* **Xử lý Media:** `MoviePy` kết hợp bộ mã hóa `FFmpeg`.
* **Frontend:** HTML5, Vanilla CSS, JavaScript (Fetch API). Không dùng framework nặng (React/Vue) để giữ giao diện trực quan, dễ bảo trì trực tiếp trên Backend.

---

## 3. CẤU TRÚC DỮ LIỆU CỐT LÕI (DATA SCHEMA)

Để hệ thống vận hành tự động không đứt gãy, luồng dữ liệu truyền dịch giữa các AI Agent phải được chuẩn hóa qua cấu trúc JSON nghiêm ngặt.

### 3.1. JSON Schema Đầu Ra của LLM (Kịch bản & Phân cảnh)
Khi nhận yêu cầu về một chủ đề, LLM bắt buộc phải phản hồi định dạng JSON dưới đây (Thông qua tính năng Structured Outputs của OpenAI hoặc Prompt Engineering):

```json
{
  "story_title": "Truyện cổ tích Thánh Gióng",
  "global_art_style": "3D cinematic animation style, ancient Vietnamese culture, vibrant colors, epic atmosphere, 8k resolution.",
  "character_presets": {
    "thanh_giong_child": "A 3-year-old Vietnamese boy, chubby cheeks, bright eyes, sitting silently on a bamboo mat, wearing traditional ancient short cloth.",
    "thanh_giong_hero": "A giant, muscular ancient Vietnamese warrior, fierce face, long black hair tied up, wearing iron armor, riding a fire-breathing iron horse."
  },
  "scenes": [
    {
      "scene_index": 1,
      "narration": "Vào đời Hùng Vương thứ sáu, ở làng Gióng có hai vợ chồng chăm chỉ làm ăn nhưng muộn con.",
      "character_focus": "none",
      "visual_prompt": "An ancient Vietnamese peaceful village, thatch houses, a hard-working old couple farming in the rice field, soft morning sunlight, cinematic lighting.",
      "estimated_duration": 6
    },
    {
      "scene_index": 2,
      "narration": "Một hôm, người vợ ra đồng thấy một vết chân to, liền đặt bàn chân mình lên ướm thử. Không ngờ về nhà liền mang thai.",
      "character_focus": "none",
      "visual_prompt": "Close up shot of a giant footprint in a muddy rice field, an ancient Vietnamese woman stepping her bare foot into the footprint, mystical morning glow.",
      "estimated_duration": 7
    },
    {
      "scene_index": 3,
      "narration": "Lên ba tuổi, đứa trẻ vẫn không biết nói cười, đặt đâu nằm đấy.",
      "character_focus": "thanh_giong_child",
      "visual_prompt": "A 3-year-old Vietnamese boy, chubby cheeks, sitting silently on a bamboo mat inside a rustic wooden house, mother looking sad in the background.",
      "estimated_duration": 5
    }
  ]
}
```

### 3.2. Cấu trúc Cơ sở dữ liệu (SQLite Schema)

#### Bảng `projects`
* `id`: INTEGER (Primary Key)
* `title`: VARCHAR
* `status`: VARCHAR (`draft`, `generating`, `pending_review`, `completed`)
* `created_at`: TIMESTAMP

#### Bảng `scenes`
* `id`: INTEGER (Primary Key)
* `project_id`: INTEGER (Foreign Key)
* `scene_index`: INTEGER
* `narration`: TEXT (Nội dung thuyết minh)
* `visual_prompt`: TEXT (Mô tả hình ảnh cho AI Video)
* `character_focus`: VARCHAR (Khóa ánh xạ tới preset nhân vật)
* `audio_path`: VARCHAR (Đường dẫn file tiếng `.mp3`)
* `video_path`: VARCHAR (Đường dẫn file hình `.mp4`)
* `status`: VARCHAR (`pending`, `processing`, `success`, `failed`)

---

## 4. QUY TRÌNH VẬN HÀNH CHI TIẾT (PIPELINE STEP-BY-STEP)

### Bước 1: Khởi tạo & Tạo kịch bản cấu trúc (Tự động)
1. Người dùng nhập tên đề tài: "Truyện Thánh Gióng".
2. Backend gửi yêu cầu kèm **System Prompt** tới LLM.
   * *System Prompt Chiến lược:* Ép LLM hoạt động như một Giám đốc nghệ thuật kiêm Biên kịch. Yêu cầu tạo ra tính nhất quán bằng cách xây dựng `character_presets` và nối các preset này vào `visual_prompt` của từng phân cảnh một cách tự động.

### Bước 2: Phân rã dữ liệu & Lập lịch tác vụ (Tự động)
1. Hệ thống tiếp nhận JSON từ LLM, bóc tách thông tin và ghi đè vào bảng `projects` và `scenes` với trạng thái `pending`.
2. Hệ thống kích hoạt đồng thời 2 Task workers:
   * **Task Audio:** Duyệt qua các dòng `narration`, gọi sang ElevenLabs API để chuyển đổi Text-to-Speech $ightarrow$ Lưu file vào `/static/audio/{project_id}_{scene_index}.mp3`.
   * **Task Video:** Duyệt qua các dòng `visual_prompt`. Để đảm bảo đồng bộ, Backend tự động gộp chuỗi: `Final Prompt = global_art_style + character_presets[character_focus] + visual_prompt`. Gọi sang AI Video API (Runway/Kling) $ightarrow$ Lưu file nháp vào `/static/video/{project_id}_{scene_index}.mp4`.

### Bước 3: Giao diện kiểm duyệt Human-in-the-loop (Thủ công - 20%)
Khi các tác vụ tự động hoàn tất, Project chuyển sang trạng thái `pending_review`. Người dùng mở giao diện UI HTML để kiểm duyệt:
1. **Duyệt luồng:** Xem tuần tự từng phân cảnh gồm Video chạy song song với Tiếng đọc thoại.
2. **Xử lý ngoại lệ (Sửa lỗi hình ảnh):** Nếu phân cảnh 3 nhân vật Thánh Gióng nhìn quá già hoặc bối cảnh sai, người dùng chỉnh sửa trực tiếp chuỗi `visual_prompt` trên ô nhập liệu và bấm **"Regenerate Video"**.
3. Backend nhận tín hiệu, chạy riêng lẻ phân cảnh đó, cập nhật lại DB và tải file mới đè lên file cũ.

### Bước 4: Hợp nhất và Xuất bản thành phẩm (Tự động)
Sau khi người dùng nhấn **"Approve & Merge"**:
1. Backend gọi module xử lý Media lấy toàn bộ các file hình và tiếng đã hoàn thiện từ DB.
2. Ép thời gian hiển thị của video phân cảnh bằng đúng thời gian chạy của file audio phân cảnh tương ứng.
3. Sử dụng `concatenate_videoclips` của MoviePy để nối mượt và xuất file `final_output.mp4`.

---

## 5. MÃ NGUỒN PHÁT TRIỂN CORE BACKEND (MOCKUP CODE)

### 5.1. Module gọi API Video & Đồng bộ hóa dữ liệu
```python
import asyncio
import httpx
from sqlalchemy.orm import Session
import time

# Giả lập cấu trúc xử lý tạo Video bất đồng bộ từ API (ví dụ Kling/Runway)
async def generate_scene_video_api(scene_id: int, full_prompt: str, db: Session):
    # 1. Cập nhật trạng thái đang xử lý
    update_scene_status(scene_id, "processing", db)
    
    # 2. Gửi request tới API bên thứ 3
    api_url = "https://api.runwayml.com/v1/tasks" # Hoặc Kling AI tùy thuộc tích hợp
    headers = {"Authorization": "Bearer YOUR_API_KEY"}
    payload = {
        "task_type": "text_to_video",
        "prompt": full_prompt,
        "aspect_ratio": "16:9"
    }
    
    async with httpx.AsyncClient() as client:
        # Gọi lệnh khởi tạo task tạo video
        response = await client.post(api_url, json=payload, headers=headers)
        task_data = response.json()
        task_id = task_data.get("id")
        
        # 3. Polling kiểm tra trạng thái video hoàn thành (Vì tạo video AI mất từ 1-3 phút)
        while True:
            await asyncio.sleep(15) # Chờ 15 giây mỗi lần kiểm tra
            status_check = await client.get(f"{api_url}/{task_id}", headers=headers)
            result = status_check.json()
            
            if result["status"] == "SUCCEEDED":
                video_download_url = result["output_url"]
                # Tiến hành tải video về thư mục cục bộ
                local_path = f"static/video/scene_{scene_id}.mp4"
                await download_file(video_download_url, local_path)
                
                # Cập nhật DB
                update_scene_paths_and_status(scene_id, video_path=local_path, status="success", db=db)
                break
            elif result["status"] == "FAILED":
                update_scene_status(scene_id, "failed", db)
                break
```

### 5.2. Module Hợp nhất Video (MoviePy Engine)
```python
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import os

def build_final_movie(scenes_data, output_filename="final_story.mp4"):
    """
    scenes_data: List các dict chứa đường dẫn video và audio của từng phân cảnh
    [{"video": "static/video/scene_1.mp4", "audio": "static/audio/scene_1.mp3"}]
    """
    final_clips = []
    
    for scene in scenes_data:
        if not os.path.exists(scene["video"]) or not os.path.exists(scene["audio"]):
            continue
            
        video_clip = VideoFileClip(scene["video"])
        audio_clip = AudioFileClip(scene["audio"])
        
        # Khớp thời lượng video theo độ dài tệp âm thanh thuyết minh
        duration = audio_clip.duration
        
        # Nếu video ngắn hơn audio, lặp lại khung hình cuối (Freeze frame) hoặc làm chậm tốc độ
        if video_clip.duration < duration:
            video_clip = video_clip.set_duration(duration)
        else:
            video_clip = video_clip.subclip(0, duration)
            
        # Thêm audio vào video phân cảnh
        video_clip = video_clip.set_audio(audio_clip)
        final_clips.append(video_clip)
        
    if final_clips:
        # Hợp nhất tất cả phân cảnh theo thứ tự mượt mà
        final_video = concatenate_videoclips(final_clips, method="compose")
        final_video.write_videofile(
            output_filename, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            threads=4
        )
        return True
    return False
```

---

## 6. GIAO DIỆN KIỂM DUYỆT TỐI GIẢN (HTML/CSS)

Giao diện được hiển thị trực tiếp bằng một file HTML duy nhất kết nối với các API của FastAPI thông qua Fetch JavaScript.

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>AI Video Generator - Human In The Loop Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; color: #333; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .project-header { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .scene-card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: table; width: 100%; box-sizing: border-box; }
        .scene-col { display: table-cell; vertical-align: top; padding: 10px; }
        .col-info { width: 10%; font-weight: bold; font-size: 18px; color: #4a5568; }
        .col-text { width: 45%; }
        .col-media { width: 45%; text-align: center; background: #fafafa; border-radius: 6px; }
        textarea { width: 100%; height: 80px; margin-top: 10px; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; resize: vertical; }
        video { width: 100%; max-height: 200px; border-radius: 4px; background: #000; }
        audio { width: 100%; margin-top: 10px; }
        .btn { background: #3182ce; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 10px; }
        .btn:hover { background: #2b6cb0; }
        .btn-regenerate { background: #dd6b20; }
        .btn-regenerate:hover { background: #c05621; }
        .btn-submit-all { background: #38a169; width: 100%; padding: 15px; font-size: 18px; margin-top: 20px; }
        .btn-submit-all:hover { background: #2f855a; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; background: #feebc8; color: #c05621; }
        .status-success { background: #c6f6d5; color: #22543d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="project-header">
            <h2>Dự án: Thánh Gióng <span class="status-badge">Đang đợi duyệt (Pending Review)</span></h2>
            <p>Kiểm tra nội dung, âm thanh và hình ảnh của từng phân cảnh dưới đây trước khi xuất bản bản dựng cuối cùng.</p>
        </div>

        <!-- Mẫu lặp phân cảnh (Sẽ render động bằng JS) -->
        <div class="scene-card">
            <div class="scene-col col-info">Scene 1</div>
            <div class="scene-col col-text">
                <label><strong>Lời thoại thuyết minh:</strong></label>
                <p>Ngày xưa, vào đời Hùng Vương thứ sáu, ở làng Gióng có hai vợ chồng chăm chỉ làm ăn nhưng muộn con.</p>
                
                <label><strong>Prompt Hình Ảnh AI (Có thể chỉnh sửa):</strong></label>
                <textarea id="prompt_1">3D cinematic animation style, ancient Vietnamese peaceful village, thatch houses, an old couple farming in the rice field, soft morning sunlight.</textarea>
                <button class="btn btn-regenerate" onclick="regenerateVideo(1)">Tạo lại Video phân cảnh này</button>
            </div>
            <div class="scene-col col-media">
                <video src="static/video/scene_1.mp4" controls></video>
                <audio src="static/audio/scene_1.mp3" controls></audio>
                <div style="margin-top:5px;"><span class="status-badge status-success">Đã Hoàn Thành</span></div>
            </div>
        </div>

        <button class="btn btn-submit-all">TIẾN HÀNH HỢP NHẤT VIDEO THÀNH PHẨM (MERGE VIDEO)</button>
    </div>

    <script>
        async function regenerateVideo(sceneId) {
            const promptText = document.getElementById(`prompt_${sceneId}`).value;
            alert(`Đang gửi yêu cầu tạo lại video cho phân cảnh ${sceneId} với Prompt mới...`);
            // Viết Fetch API gửi lên FastAPI xử lý lại task đơn lẻ ở đây
        }
    </script>
</body>
</html>
```

---

## 7. LỘ TRÌNH TRIỂN KHAI (ROADMAP) VÀ QUẢN TRỊ RỦI RO

### 7.1. Lộ trình 4 Tuần Nghiên Cứu
* **Tuần 1: Thiết lập lõi và Prompt Engineering**
  * Viết mã nguồn kết nối LLM (OpenAI/Claude). Tối ưu hệ thống System Prompt để đảm bảo 100% trả về đúng định dạng cấu trúc JSON không bị gãy (Sử dụng Pydantic trong FastAPI để validate dữ liệu đầu ra).
  * Đăng ký và test kết nối API của ElevenLabs và Runway/Kling AI.
* **Tuần 2: Xây dựng Cơ sở dữ liệu và Cơ chế Task Worker xếp hàng (Queue)**
  * Thiết kế DB SQLite để kiểm soát trạng thái các thực thể.
  * Viết các hàm chạy nền xử lý tải file từ API về máy chủ.
  * Dựng cấu trúc Frontend HTML thô để đổ dữ liệu từ DB lên màn hình.
* **Tuần 3: Tích hợp Giao diện tương tác HITL & Engine Kết nối Media**
  * Hoàn thiện chức năng truyền dữ liệu ngược từ giao diện khi người dùng sửa đổi Prompt -> Chạy lại tác vụ đơn lẻ.
  * Viết module logic tính toán căn chỉnh thời gian bằng MoviePy để đồng bộ hóa hoàn toàn âm thanh và chuyển động hình ảnh.
* **Tuần 4: Đo lường, Đánh giá và Tối ưu đề tài**
  * Tiến hành chạy thử nghiệm hệ thống thực tế với 3 kịch bản truyện cổ tích khác nhau.
  * Tính toán chỉ số: Tổng chi phí API cho 1 phút video, Thời gian xử lý trung bình, Tỷ lệ can thiệp thủ công thực tế (Đếm số lần phải bấm Regenerate).

### 7.2. Các thách thức lớn và giải pháp giảm thiểu (Risk Mitigation)

1. **Vấn đề đồng bộ nhất quán nhân vật (Character Consistency):**
   * *Rủi ro:* AI video tạo ra nhân vật Thánh Gióng ở phân cảnh 3 nhìn hoàn toàn khác với phân cảnh 4.
   * *Giải pháp:* Tận dụng tối đa tính năng `character_presets` trong dữ liệu JSON. Ngoài ra, nếu dùng các API tiên tiến (như Kling AI), hệ thống Backend có thể thiết kế luồng tạo ảnh nhân vật mẫu trước (Text-to-Image), sau đó dùng chính ảnh cố định đó làm đầu vào (Image-to-Video) cho mọi phân cảnh để khóa gương mặt nhân vật cố định.
2. **Chi phí và Giới hạn băng thông API (Rate Limit / Cost):**
   * *Rủi ro:* Quá trình thử nghiệm tạo đi tạo lại hàng loạt video có thể gây tốn kém chi phí API rất lớn.
   * *Giải pháp:* Ở giai đoạn phát triển, cấu hình module Video ở chế độ "Mock" (sử dụng video mẫu có sẵn trong máy) để kiểm tra luồng UI/UX của hệ thống. Chỉ kích hoạt gọi API thật khi test thực tế kịch bản. Sử dụng độ phân giải thấp (720p) hoặc thời lượng ngắn (4-5s) để tối ưu chi phí trong giai đoạn nghiên cứu khoa học.
3. **Lỗi hết thời gian chờ (Timeout) khi gọi API Video:**
   * *Rủi ro:* Tạo video bằng AI mất khá nhiều thời gian, nếu gọi API theo kiểu đồng bộ (Synchronous), HTTP request sẽ bị ngắt kết nối giữa chừng gây lỗi hệ thống.
   * *Giải pháp:* Sử dụng cơ chế Webhook (nếu API bên thứ 3 hỗ trợ) hoặc thiết kế luồng kiểm tra trạng thái chủ động (Polling với `asyncio.sleep`) như đoạn mã mẫu tại Mục 5.1.
