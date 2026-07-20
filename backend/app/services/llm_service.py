import json
from ..schemas import LLMStoryOutput

class LLMService:
    @staticmethod
    async def generate_story(prompt: str) -> LLMStoryOutput:
        # Trong tương lai sẽ gọi OpenAI hoặc Claude với Structured Outputs.
        # Ở đây ta trả về dữ liệu mẫu có cấu trúc chuẩn cho truyện Thánh Gióng.
        
        mock_story = {
            "story_title": f"Sự tích {prompt}",
            "global_art_style": "3D cinematic animation style, ancient Vietnamese culture, vibrant colors, epic atmosphere, 8k resolution.",
            "character_presets": {
                "thanh_giong_child": "A 3-year-old Vietnamese boy, chubby cheeks, bright eyes, sitting silently on a bamboo mat, wearing traditional ancient short cloth.",
                "thanh_giong_hero": "A giant, muscular ancient Vietnamese warrior, fierce face, long black hair tied up, wearing iron armor, riding a fire-breathing iron horse."
            },
            "scenes": [
                {
                    "scene_index": 1,
                    "narration": f"Vào đời Hùng Vương thứ sáu, ở làng Gióng có hai vợ chồng chăm chỉ làm ăn nhưng muộn con. Họ hằng mong mỏi có một mụn con.",
                    "character_focus": "none",
                    "visual_prompt": "An ancient Vietnamese peaceful village, thatch houses, a hard-working old couple farming in the rice field, soft morning sunlight, cinematic lighting.",
                    "estimated_duration": 6
                },
                {
                    "scene_index": 2,
                    "narration": "Một hôm, người vợ ra đồng thấy một vết chân to lạ kỳ, liền đặt bàn chân mình lên ướm thử. Không ngờ về nhà bà mang thai.",
                    "character_focus": "none",
                    "visual_prompt": "Close up shot of a giant footprint in a muddy rice field, an ancient Vietnamese woman stepping her bare foot into the footprint, mystical morning glow.",
                    "estimated_duration": 7
                },
                {
                    "scene_index": 3,
                    "narration": "Lên ba tuổi, đứa trẻ vẫn không biết nói cười, đặt đâu nằm đấy khiến hai vợ chồng vô cùng lo lắng.",
                    "character_focus": "thanh_giong_child",
                    "visual_prompt": "A 3-year-old Vietnamese boy, chubby cheeks, sitting silently on a bamboo mat inside a rustic wooden house, mother looking sad in the background.",
                    "estimated_duration": 5
                }
            ]
        }
        
        return LLMStoryOutput(**mock_story)
