# Hệ thống IT Helpdesk chuyên nghiệp

Đây là một dự án ứng dụng web được xây dựng bằng Flask, mô phỏng một hệ thống quản lý yêu cầu hỗ trợ (IT Helpdesk) nội bộ cho doanh nghiệp. Dự án phù hợp cho báo cáo thực tập hoặc làm sản phẩm trong portfolio.

![Screenshot của ứng dụng](link_den_anh_screenshot_cua_ban.png)

## Tính năng nổi bật

* **Quản lý Người dùng & Phân quyền:** Đăng ký, đăng nhập, phân quyền (Admin, Support, User).
* **Hệ thống Ticket:** Người dùng tạo ticket, Admin/Support xử lý, cập nhật trạng thái, giao việc.
* **Tương tác thời gian thực:** Trao đổi qua lại trong ticket bằng hệ thống bình luận.
* **Đính kèm File:** Người dùng có thể đính kèm file ảnh/tài liệu khi tạo ticket.
* **Hệ thống Đánh giá:** Người dùng đánh giá chất lượng hỗ trợ sau khi ticket được đóng.
* **Dashboard Trực quan:**
    * **Admin Dashboard:** Thống kê, tìm kiếm, lọc ticket nâng cao.
    * **User Dashboard:** Giao diện card hiện đại, chỉ hiển thị ticket cá nhân.
* **Trợ lý AI (Chatbot):** Tích hợp Google Gemini API để tự động trả lời các câu hỏi IT cơ bản, giảm tải cho nhân viên.
* **Thông báo qua Email:** Tự động gửi email khi có ticket mới.
* **Báo cáo & Phân tích:** Trang Analytics với biểu đồ trực quan về hiệu suất của đội ngũ.

## Công nghệ sử dụng

* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
* **Frontend:** HTML, CSS, JavaScript, Chart.js
* **Database:** MySQL
* **AI:** Google Generative AI (Gemini)

## Hướng dẫn Cài đặt & Chạy

**Yêu cầu:** Python 3.8+, pip, MySQL Server.

1.  **Clone repository:**
    ```bash
    git clone [URL-repository-cua-ban]
    cd it-helpdesk-system
    ```
2.  **Tạo môi trường ảo và cài đặt thư viện:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Trên Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Cấu hình Database & API Keys:**
    * Tạo file `.env` từ file `.env.example` (nếu có).
    * Điền các thông tin `DATABASE_URL`, `SECRET_KEY`, `GOOGLE_API_KEY`, và các biến `MAIL_` vào file `.env`.
4.  **Khởi tạo Database:**
    ```bash
    # Đăng nhập vào mysql và tạo database
    # CREATE DATABASE helpdesk_db;
    # Chạy script để tạo bảng và dữ liệu mẫu
    mysql -u root -p < database_setup.sql
    ```
5.  **Chạy ứng dụng:**
    ```bash
    python run.py
    ```
    Truy cập vào `http://127.0.0.1:5000`.

## Tài khoản mẫu

* **Admin:** `tuanadmin@example.com` / `admin`


Chạy chương trình
Tóm tắt nhanh
Mở terminal tại thư mục dự án
Kích hoạt venv: .\venv\Scripts\Activate
(Nếu cần) Cài thư viện: pip install -r requirements.txt
Chạy: python run.py
Truy cập: http://localhost:5000