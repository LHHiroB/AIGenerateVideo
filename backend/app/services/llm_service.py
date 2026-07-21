import json
import httpx
from ..config import settings
from ..schemas import LLMStoryOutput

class LLMService:
    @staticmethod
    async def generate_story(prompt: str) -> LLMStoryOutput:
        if settings.OPENAI_API_KEY:
            try:
                # Định nghĩa schema cho Structured Outputs của OpenAI
                schema = {
                    "type": "object",
                    "properties": {
                        "story_title": {
                            "type": "string",
                            "description": "Tên câu chuyện/chủ đề sinh ra"
                        },
                        "global_art_style": {
                            "type": "string",
                            "description": "Phong cách hình ảnh toàn cục cho video, mô tả bằng tiếng Anh chi tiết"
                        },
                        "character_presets": {
                            "type": "object",
                            "additionalProperties": { "type": "string" },
                            "description": "Các thiết lập nhân vật mẫu dùng trong truyện (ví dụ: 'giong_child', 'giong_hero'), mô tả chi tiết bằng tiếng Anh"
                        },
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_index": { "type": "integer" },
                                    "narration": { "type": "string", "description": "Lời thoại thuyết minh bằng tiếng Việt truyền cảm" },
                                    "character_focus": { "type": "string", "description": "Tên key của nhân vật trong character_presets hoặc 'none' nếu không tập trung vào nhân vật cụ thể nào" },
                                    "visual_prompt": { "type": "string", "description": "Mô tả chi tiết phân cảnh bằng tiếng Anh cho AI Text-to-Video" },
                                    "estimated_duration": { "type": "integer", "description": "Thời lượng ước tính của cảnh này tính bằng giây (từ 5 đến 10)" }
                                },
                                "required": ["scene_index", "narration", "character_focus", "visual_prompt", "estimated_duration"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["story_title", "global_art_style", "character_presets", "scenes"],
                    "additionalProperties": False
                }

                system_prompt = (
                    "Bạn là một biên kịch chuyên nghiệp và chuyên gia tạo prompt hình ảnh. "
                    "Hãy tạo kịch bản phân cảnh chi tiết cho chủ đề người dùng yêu cầu. "
                    "Kịch bản phải gồm ít nhất 3 phân cảnh liên tiếp, logic và hấp dẫn. "
                    "Các lời thoại thuyết minh (narration) viết bằng tiếng Việt mượt mà. "
                    "Các prompt hình ảnh (visual_prompt) viết bằng tiếng Anh chi tiết để sinh video chất lượng cao."
                )

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Chủ đề/Truyện: {prompt}"}
                            ],
                            "response_format": {
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "story_output",
                                    "strict": True,
                                    "schema": schema
                                }
                            },
                            "temperature": 0.7
                        }
                    )
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        content = res_json["choices"][0]["message"]["content"]
                        story_data = json.loads(content)
                        return LLMStoryOutput(**story_data)
                    else:
                        print(f"OpenAI API Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Failed to generate story via OpenAI: {e}")

        # --- DYNAMIC MOCK FALLBACK (Khi không có API key hoặc lỗi) ---
        print("Using Dynamic Mock Fallback for story generation.")
        mock_story = {
            "story_title": f"Hành trình {prompt}",
            "global_art_style": "Cinematic rendering, high detail, historical atmosphere, vibrant color grading, 8k resolution.",
            "character_presets": {
                "main_character": f"A noble hero representing {prompt}, wearing traditional clothes, brave expression, anime style."
            },
            "scenes": [
                {
                    "scene_index": 1,
                    "narration": f"Ngày xửa ngày xưa, câu chuyện về {prompt} bắt đầu với một khởi đầu đầy hứa hẹn tại ngôi làng yên bình.",
                    "character_focus": "main_character",
                    "visual_prompt": f"A peaceful ancient village scene, welcoming the character of {prompt}, golden hour lighting, cinematic camera work.",
                    "estimated_duration": 6
                },
                {
                    "scene_index": 2,
                    "narration": f"Vượt qua muôn vàn khó khăn thử thách, {prompt} dần chứng tỏ được lòng dũng cảm phi thường của mình.",
                    "character_focus": "main_character",
                    "visual_prompt": f"Hero facing a majestic storm or mountain challenge, looking determined, dramatic cinematic lighting.",
                    "estimated_duration": 7
                },
                {
                    "scene_index": 3,
                    "narration": f"Cuối cùng, hòa bình đã trở lại và câu chuyện về {prompt} sẽ mãi mãi được lưu truyền cho các thế hệ mai sau.",
                    "character_focus": "none",
                    "visual_prompt": f"Grand epic finale, beautiful sunset over the mountains, cinematic camera panning out, peaceful landscape.",
                    "estimated_duration": 6
                }
            ]
        }
        return LLMStoryOutput(**mock_story)

