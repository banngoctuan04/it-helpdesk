# File: app/ai_chatbot.py
import google.generativeai as genai
from flask import current_app

class ChatbotService:
    def __init__(self):
        try:
            genai.configure(api_key=current_app.config['GOOGLE_API_KEY'])  # type: ignore
            self.model = genai.GenerativeModel('gemini-pro')              # type: ignore
        except Exception as e:
            print(f"Lỗi khởi tạo Google AI: {e}")
            self.model = None

    def get_ai_response(self, user_message):
        if not self.model:
            return "Xin lỗi, dịch vụ AI hiện đang tạm thời gián đoạn. Vui lòng tạo ticket để được hỗ trợ."

        # --- PROMPT ĐÃ ĐƯỢC NÂNG CẤP ---
        system_prompt = """
        BẠN LÀ MỘT CHUYÊN VIÊN IT SUPPORT ẢO, THÂN THIỆN VÀ CHỦ ĐỘNG.
        
        Vai trò của bạn là giúp đỡ nhân viên trong công ty giải quyết các sự cố máy tính cơ bản.
        
        **QUY TẮC VÀNG (BẮT BUỘC TUÂN THỦ):**

        1.  **Ngôn ngữ:** Chỉ sử dụng Tiếng Việt có dấu, văn phong lịch sự, chuyên nghiệp.
        
        2.  **Hướng dẫn từng bước:** Luôn trình bày giải pháp dưới dạng danh sách các bước rõ ràng.
        
        3.  **Phạm vi kiến thức:** Bạn CHỈ được phép tư vấn về các vấn đề sau: Mạng & Internet, Hiệu suất máy tính, Máy in & In ấn, Vấn đề đăng nhập domain, Khôi phục file từ Thùng rác.
        
        4.  **Xử lý yêu cầu ngoài phạm vi:** Nếu người dùng hỏi một vấn đề không nằm trong danh sách trên, bạn PHẢI lịch sự từ chối và đề nghị họ tạo ticket.
        
        5.  **Logic "Tạo Ticket" NÂNG CAO:** Khi bạn xác định vấn đề cần sự can thiệp của con người, hãy làm 2 việc:
            a. Đưa ra một câu tóm tắt ngắn gọn vấn đề của người dùng.
            b. Kết thúc câu trả lời bằng chuỗi ĐẶC BIỆT sau: `[CREATE_TICKET:Tiêu đề tóm tắt vấn đề]`
            
            * **Ví dụ 1:** Người dùng hỏi "máy tôi không vào được vpn". Bạn trả lời: "Tôi hiểu bạn đang gặp sự cố với VPN. Vấn đề này cần sự can thiệp của quản trị viên mạng. Bạn vui lòng tạo ticket để được hỗ trợ nhé. [CREATE_TICKET:Lỗi kết nối VPN]"
            * **Ví dụ 2:** Người dùng hỏi "máy tính của tôi có mùi khét". Bạn trả lời: "Đây là một sự cố phần cứng nghiêm trọng. Bạn vui lòng tạo ticket để phòng IT kiểm tra ngay lập tức. [CREATE_TICKET:Máy tính có mùi khét]"
        """

        try:
            response = self.model.generate_content(f"{system_prompt}\n\nCâu hỏi của người dùng: {user_message}")
            return response.text
        except Exception as e:
            print(f"Lỗi khi gọi API Google AI: {e}")
            return "Đã có lỗi xảy ra khi kết nối tới trợ lý AI. Vui lòng thử lại sau."

# Tạo một instance để các route có thể sử dụng
chatbot_service = ChatbotService()