# KIẾN TRÚC HỆ THỐNG & CẤU TRÚC DỮ LIỆU

Hệ thống được thiết kế theo mô hình Monolith tối giản để tối ưu tốc độ phát triển và thử nghiệm nghiên cứu.

## 1. Kiến trúc hệ thống (Tech Stack)

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

* **Backend Framework:** `FastAPI` (Python). Hỗ trợ cơ chế `async/await` rất tốt cho việc gọi hàng loạt (Parallel/Concurrent) API từ các nhà cung cấp bên thứ ba nhằm tiết kiệm thời gian tạo video.
* **Database:** `SQLite` + `SQLAlchemy` (ORM). Nhẹ nhàng, không cần cài đặt server độc lập, lưu trữ toàn bộ trạng thái (State) của project và các phân cảnh.
* **Xử lý Media:** `MoviePy` kết hợp bộ mã hóa `FFmpeg`.
* **Frontend:** HTML5, Vanilla CSS, JavaScript (Fetch API). Không dùng framework nặng (React/Vue) để giữ giao diện trực quan, dễ bảo trì trực tiếp trên Backend.

---

## 2. Cấu trúc dữ liệu cốt lõi (Data Schema)

### 2.1. JSON Schema Đầu Ra của LLM (Kịch bản & Phân cảnh)
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

### 2.2. Cấu trúc Cơ sở dữ liệu (SQLite Schema)

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
