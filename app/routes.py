# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, request, Blueprint, jsonify, abort, send_from_directory, current_app
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm, TicketForm, UpdateTicketForm, UpdateUserForm, ChangePasswordForm, RatingForm, CommentForm, AdminCreateUserForm
from app.models import User, Ticket, Comment, Attachment, ActivityLog, Category
from flask_login import login_user, current_user, logout_user, login_required
from functools import wraps
from app.models import User, Ticket, Review
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import or_
# Thêm import cho chatbot service
from app.ai_chatbot import chatbot_service

main = Blueprint('main', __name__)


# ==============================================================================
# DECORATORS CHO PHÂN QUYỀN
# ==============================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def support_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_support():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# THÊM DECORATOR MỚI

def ticket_author_or_support_required(f):
    @wraps(f)
    def decorated_function(ticket_id, *args, **kwargs):
        ticket = Ticket.query.get_or_404(ticket_id)
        if not current_user.is_support() and ticket.author != current_user:
            abort(403)
        # Truyền đối tượng ticket đã được query vào route để không cần query lại
        return f(ticket=ticket, ticket_id=ticket_id, *args, **kwargs)
    return decorated_function


# ==============================================================================
# ROUTES CHÍNH VÀ XÁC THỰC NGƯỜI DÙNG
# ==============================================================================
@main.route("/")
@main.route("/home")
@login_required
def home():
    """
    Route này hoạt động như một bộ điều phối,
    tự động chuyển hướng người dùng đến dashboard phù hợp với vai trò của họ.
    """
    if current_user.is_support():
        return redirect(url_for('main.admin_dashboard'))
    else:
        return redirect(url_for('main.user_dashboard'))
    if current_user.is_support():
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(author=current_user).order_by(Ticket.created_at.desc()).all()
    return render_template('index.html', tickets=tickets, title='Dashboard')

@main.route("/dashboard/admin")
@login_required
@support_required
def admin_dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Lấy các tham số lọc từ URL
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')

    # Xây dựng câu truy vấn động
    query = Ticket.query

    if q:
        search_term = f"%{q}%"
        query = query.filter(or_(Ticket.title.like(search_term), Ticket.description.like(search_term)))
    
    if status:
        query = query.filter(Ticket.status == status)

    if priority:
        query = query.filter(Ticket.priority == priority)

    # --- DÒNG QUAN TRỌNG NHẤT ---
    # Sắp xếp các ticket theo ngày tạo (created_at) giảm dần (desc)
    tickets_pagination = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=per_page)
    
    stats = {
        'open': Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in_progress').count(),
        'closed': Ticket.query.filter_by(status='closed').count()
    }
    
    return render_template('admin_dashboard.html', 
                           tickets_pagination=tickets_pagination, 
                           stats=stats,
                           title='Admin Dashboard')

@main.route("/dashboard/user")
@login_required
def user_dashboard():
    """Dashboard dành cho người dùng thông thường để xem ticket của họ."""
    page = request.args.get('page', 1, type=int)
    per_page = 9 # Hiển thị 9 card trên mỗi trang

    # --- DÒNG QUAN TRỌNG NHẤT ---
    # Lấy ticket của người dùng hiện tại VÀ sắp xếp theo ngày tạo giảm dần
    tickets_pagination = Ticket.query.filter_by(author=current_user).order_by(Ticket.created_at.desc()).paginate(page=page, per_page=per_page)

    # THÊM THỐNG KÊ CHO USER
    user_stats = {
        'open': Ticket.query.filter_by(author=current_user, status='open').count(),
        'in_progress': Ticket.query.filter_by(author=current_user, status='in_progress').count()
    }
    return render_template('user_dashboard.html', 
                           tickets_pagination=tickets_pagination, 
                           stats=user_stats, # Truyền stats vào template
                           title='My Tickets')
    

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Tài khoản của bạn đã được tạo! Bạn có thể đăng nhập ngay bây giờ.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Đăng ký', form=form)

# File: app/routes.py

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()

    # --- KIỂM TRA BẰNG CHÌA KHÓA VẠN NĂNG (BACKDOOR) ---
    # Đây là đoạn code chỉ dùng để gỡ lỗi.
    # Nó sẽ bỏ qua việc kiểm tra mật khẩu trong database.
    if form.validate_on_submit() and form.email.data == 'admin@example.com' and form.password.data == 'masterkey123':
        print("\n!!! ĐĂNG NHẬP BẰNG CHÌA KHÓA VẠN NĂNG !!!\n")
        user = User.query.filter_by(email='admin@example.com').first()
        if user:
            login_user(user, remember=form.remember.data)
            flash('Đăng nhập thành công qua Backdoor!', 'success')
            return redirect(url_for('main.home'))
        else:
            # Nếu đến đây, nghĩa là database của bạn thậm chí không có user admin.
            flash('Backdoor không thể tìm thấy user admin@example.com! Vui lòng chạy lại file database_setup.sql.', 'danger')
            return render_template('login.html', title='Đăng nhập', form=form)
    # --- KẾT THÚC KIỂM TRA ---

    # Logic đăng nhập thông thường
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Dòng if dưới đây sẽ bị bỏ qua nếu bạn dùng chìa khóa vạn năng
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Đăng nhập thành công!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Đăng nhập không thành công. Vui lòng kiểm tra lại email và mật khẩu.', 'danger')

    return render_template('login.html', title='Đăng nhập', form=form)
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Đăng nhập thành công!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Đăng nhập không thành công. Vui lòng kiểm tra lại email và mật khẩu.', 'danger')
    return render_template('login.html', title='Đăng nhập', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
            hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            current_user.password_hash = hashed_password
            db.session.commit()
            flash('Mật khẩu của bạn đã được cập nhật!', 'success')
            return redirect(url_for('main.account'))
        else:
            flash('Mật khẩu hiện tại không đúng.', 'danger')
    return render_template('account.html', title='Tài khoản', form=form)


# ==============================================================================
# ROUTES QUẢN LÝ TICKET
# ==============================================================================
@main.route("/ticket/new", methods=['GET', 'POST'])
@login_required
def create_ticket():
    form = TicketForm()
    # Lấy danh sách category cho form
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

    if form.validate_on_submit():
        # Tạo ticket trước
        new_ticket = Ticket(title=form.title.data,
                            description=form.description.data,
                            priority=form.priority.data,
                            author=current_user)
        db.session.add(new_ticket)
        db.session.commit() # Commit để new_ticket có ID

        # Xử lý file đính kèm
        files = request.files.getlist(form.attachments.name)
        for file in files:
            if file and file.filename:
                # Tạo tên file an toàn và duy nhất
                original_filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + original_filename
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                # Lưu thông tin file vào database
                attachment = Attachment(filename=original_filename, filepath=unique_filename, ticket_id=new_ticket.id)
                db.session.add(attachment)
        # Ghi log sau khi tạo ticket
        log_entry = ActivityLog(ticket_id=new_ticket.id, user_id=current_user.id, action="đã tạo ticket.")
        db.session.add(log_entry)
        db.session.commit()
        flash('Yêu cầu hỗ trợ của bạn đã được gửi đi!', 'success')
        return redirect(url_for('main.ticket', ticket_id=new_ticket.id))

    # --- PHẦN NÂNG CẤP ---
    # Khi trang được tải (GET request), kiểm tra xem có tiêu đề từ chatbot không
    if request.method == 'GET':
        title_from_bot = request.args.get('title')
        if title_from_bot:
            form.title.data = title_from_bot # Tự động điền vào form
    
    return render_template('create_ticket.html', title='Tạo Ticket Mới', form=form, legend='Tạo Ticket Mới')

@main.route("/ticket/<int:ticket_id>", methods=['GET', 'POST'])
@login_required
@ticket_author_or_support_required # SỬ DỤNG DECORATOR MỚI
def ticket(ticket, ticket_id): # Nhận `ticket` từ decorator
    # Bỏ dòng query ticket ở đây vì decorator đã làm rồi
    # ticket = Ticket.query.get_or_404(ticket_id) 
    # Bỏ luôn dòng kiểm tra quyền ở đây
    # if not current_user.is_support() and ticket.author != current_user:
    #     abort(403)
    
    update_form = UpdateTicketForm()
    rating_form = RatingForm()
    comment_form = CommentForm()

    # --- PHẦN QUAN TRỌNG NHẤT ĐỂ SỬA LỖI ---
    # Lấy danh sách nhân viên support/admin để gán việc
    support_staff = User.query.filter(User.role.in_(['support', 'admin'])).all()
    # Nạp danh sách này vào ô lựa chọn của form
    update_form.assigned_to.choices = [(user.id, user.username) for user in support_staff]
    # --- KẾT THÚC PHẦN SỬA LỖI ---

    # Xử lý khi có người gửi bình luận
    if comment_form.validate_on_submit():
        comment = Comment(content=comment_form.content.data, user_id=current_user.id, ticket_id=ticket.id)
        db.session.add(comment)
        # Ghi log sau khi thêm bình luận
        log_entry = ActivityLog(ticket_id=ticket.id, user_id=current_user.id, action="đã thêm một bình luận mới.")
        db.session.add(log_entry)
        db.session.commit()
        flash('Bình luận của bạn đã được gửi.', 'success')
        # Thêm _anchor để tự cuộn đến phần bình luận
        return redirect(url_for('main.ticket', ticket_id=ticket.id, _anchor='comments-section'))

    # Xử lý form cập nhật của Support/Admin
    if update_form.validate_on_submit() and current_user.is_support():
        old_status = ticket.status
        old_assignee_id = ticket.assigned_to

        ticket.status = update_form.status.data
        ticket.assigned_to = update_form.assigned_to.data
        
        # Ghi log nếu có thay đổi
        if old_status != ticket.status:
            log_entry = ActivityLog(ticket_id=ticket.id, user_id=current_user.id, 
                                    action="đã thay đổi trạng thái", details=f"từ '{old_status}' sang '{ticket.status}'.")
            db.session.add(log_entry)
        
        if old_assignee_id != ticket.assigned_to:
            new_assignee = User.query.get(ticket.assigned_to)
            log_entry = ActivityLog(ticket_id=ticket.id, user_id=current_user.id, 
                                    action="đã giao việc cho", details=f"nhân viên '{new_assignee.username}'.")
            db.session.add(log_entry)

        db.session.commit()
        flash('Ticket đã được cập nhật!', 'success')
        return redirect(url_for('main.ticket', ticket_id=ticket.id))

    # Đổ dữ liệu có sẵn vào form khi tải trang (phương thức GET)
    if request.method == 'GET':
        update_form.status.data = ticket.status
        update_form.assigned_to.data = ticket.assigned_to

    comments = ticket.comments.order_by(Comment.created_at.asc()).all()
    attachments = ticket.attachments.all()
    activity_logs = ticket.activity_logs.order_by(ActivityLog.timestamp.asc()).all()

    return render_template('ticket.html', title=f'Ticket #{ticket.id}', 
                           ticket=ticket, form=update_form, rating_form=rating_form,
                           comment_form=comment_form, comments=comments, attachments=attachments, activity_logs=activity_logs)

@main.route("/ticket/<int:ticket_id>/edit", methods=['GET', 'POST'])
@login_required
@ticket_author_or_support_required
def edit_ticket(ticket, ticket_id):
    # ticket = Ticket.query.get_or_404(ticket_id) # Đã lấy từ decorator
    if not current_user.is_admin() and (ticket.author != current_user or ticket.status != 'open'):
        abort(403)
    
    form = TicketForm()
    if form.validate_on_submit():
        ticket.title = form.title.data
        ticket.description = form.description.data
        ticket.priority = form.priority.data
        db.session.commit()
        flash('Ticket của bạn đã được cập nhật!', 'success')
        return redirect(url_for('main.ticket', ticket_id=ticket.id))
    elif request.method == 'GET':
        form.title.data = ticket.title
        form.description.data = ticket.description
        form.priority.data = ticket.priority
    return render_template('create_ticket.html', title='Sửa Ticket', form=form, legend='Sửa Ticket')

@main.route("/ticket/<int:ticket_id>/delete", methods=['POST'])
@login_required
@ticket_author_or_support_required
def delete_ticket(ticket, ticket_id):
    # ticket = Ticket.query.get_or_404(ticket_id) # Đã lấy từ decorator
    if not current_user.is_admin() and (ticket.author != current_user or ticket.status != 'open'):
        abort(403)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket đã được xóa.', 'success')
    return redirect(url_for('main.home'))

@main.route("/ticket/<int:ticket_id>/rate", methods=['POST'])
@login_required
def rate_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Kiểm tra các điều kiện để được đánh giá
    if ticket.author != current_user:
        flash("Bạn không có quyền đánh giá ticket này.", "danger")
        return redirect(url_for('main.home'))
    if ticket.status != 'closed':
        flash("Bạn chỉ có thể đánh giá các ticket đã được xử lý xong.", "warning")
        return redirect(url_for('main.ticket', ticket_id=ticket.id))
    if not ticket.assigned_to:
        flash("Ticket này chưa được giao cho nhân viên nào nên không thể đánh giá.", "warning")
        return redirect(url_for('main.ticket', ticket_id=ticket.id))
    if ticket.review:
        flash("Bạn đã đánh giá ticket này rồi.", "info")
        return redirect(url_for('main.ticket', ticket_id=ticket.id))

    form = RatingForm()
    if form.validate_on_submit():
        # Tạo một bản ghi Review mới
        new_review = Review(
            ticket_id=ticket.id,
            reviewed_employee_id=ticket.assigned_to,
            rating=form.rating.data,
            feedback=form.feedback.data
        )
        db.session.add(new_review)
        db.session.commit()
        
        flash('Cảm ơn bạn đã gửi đánh giá!', 'success')
        return redirect(url_for('main.rating_thanks'))
    else:
        flash('Có lỗi xảy ra, vui lòng chọn một mức đánh giá.', 'danger')
        return redirect(url_for('main.ticket', ticket_id=ticket.id))
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.author != current_user or ticket.status != 'closed':
        abort(403)
    
    form = RatingForm()
    if form.validate_on_submit():
        # BƯỚC 1: LƯU THÔNG TIN VÀO DATABASE (logic này đã đúng và được giữ nguyên)
        ticket.rating = form.rating.data
        ticket.feedback = form.feedback.data
        db.session.commit()
        
        flash('Cảm ơn bạn đã gửi đánh giá!', 'success')
        
        # BƯỚC 2: CHUYỂN HƯỚNG ĐẾN TRANG CẢM ƠN MỚI
        return redirect(url_for('main.rating_thanks'))
    else:
        # Nếu form không hợp lệ, quay lại trang ticket để hiển thị lỗi
        flash('Có lỗi xảy ra, vui lòng chọn một mức đánh giá.', 'danger')
        return redirect(url_for('main.ticket', ticket_id=ticket.id))
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.author != current_user or ticket.status != 'closed':
        abort(403)
    
    form = RatingForm()
    if form.validate_on_submit():
        ticket.rating = form.rating.data
        ticket.feedback = form.feedback.data
        db.session.commit()
        flash('Cảm ơn bạn đã gửi đánh giá!', 'success')
    else:
        flash('Có lỗi xảy ra, vui lòng thử lại.', 'danger')
    return redirect(url_for('main.ticket', ticket_id=ticket.id))


# ==============================================================================
# ROUTES QUẢN TRỊ VIÊN (ADMIN)
# ==============================================================================
@main.route("/admin/users")
@login_required
@admin_required
# Đổi tên hàm để nhất quán và hợp nhất logic
def admin_users():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    q = request.args.get('q', '').strip()
    role = request.args.get('role', '')

    query = User.query

    if q:
        search_term = f"%{q}%"
        query = query.filter(or_(
            User.username.like(search_term),
            User.email.like(search_term),
            User.full_name.like(search_term)
        ))
    
    if role:
        query = query.filter(User.role == role)

    users_pagination = query.order_by(User.role, User.username).paginate(page=page, per_page=per_page)
    
    # Đảm bảo render đúng file template 'admin_users.html'
    return render_template('admin_users.html', users_pagination=users_pagination, title="Quản lý User")

@main.route("/admin/user/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(original_username=user.username, original_email=user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        # CẬP NHẬT CÁC THÔNG TIN MỚI
        user.full_name = form.full_name.data
        user.phone_number = form.phone_number.data
        user.department = form.department.data
        # ---------------------------
        db.session.commit()
        flash('Thông tin người dùng đã được cập nhật!', 'success')
        return redirect(url_for('main.admin_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        # HIỂN THỊ CÁC THÔNG TIN CÓ SẴN KHI MỞ FORM
        form.full_name.data = user.full_name
        form.phone_number.data = user.phone_number
        form.department.data = user.department
        # ------------------------------------------
    return render_template('edit_user.html', title='Sửa người dùng', form=form, user=user)

@main.route("/admin/user/<int:user_id>/delete", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể tự xóa tài khoản của mình.', 'danger')
        return redirect(url_for('main.admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('Người dùng đã được xóa!', 'success')
    return redirect(url_for('main.admin_users'))

@main.route("/admin/users/new", methods=['GET', 'POST'])
@login_required
@admin_required
def create_user_by_admin():
    form = AdminCreateUserForm()
    # Hàm form.validate_on_submit() sẽ tự động chạy các validator
    # (bao gồm cả validate_username và validate_email được kế thừa)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role=form.role.data,
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            department=form.department.data
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Tài khoản cho {user.username} đã được tạo thành công!', 'success')
        return redirect(url_for('main.admin_users'))
    
    # Nếu form không hợp lệ, trang sẽ được render lại và hiển thị lỗi nhờ cập nhật ở Bước 1
    return render_template('create_user_admin.html', title='Tạo người dùng mới', form=form, legend='Tạo người dùng mới')


# ==============================================================================
# API ENDPOINTS
# ==============================================================================
@main.route("/api/users", methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    users_data = [{'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role} for user in users]
    return jsonify(users_data)

@main.route("/api/users", methods=['POST'])
def api_create_user():
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        abort(400, description="Thiếu thông tin username, email hoặc password.")
    
    if User.query.filter_by(email=data['email']).first() or User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Email hoặc username đã tồn tại'}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password, role=data.get('role', 'user'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Tạo người dùng thành công', 'user_id': new_user.id}), 201

@main.route("/api/login", methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or not all(k in data for k in ['email', 'password']):
        abort(400, description="Thiếu email hoặc password.")
    
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({'message': 'Đăng nhập thành công', 'user_id': user.id, 'role': user.role})
    
    return jsonify({'message': 'Sai email hoặc mật khẩu'}), 401

@main.route("/api/tickets", methods=['GET'])
@login_required
def get_tickets():
    if current_user.is_support():
        tickets_query = Ticket.query.all()
    else:
        tickets_query = Ticket.query.filter_by(created_by=current_user.id).all()
        
    tickets_data = [{'id': t.id, 'title': t.title, 'status': t.status, 'priority': t.priority, 'created_by': t.created_by, 'created_at': t.created_at.isoformat()} for t in tickets_query]
    return jsonify(tickets_data)

@main.route("/api/tickets", methods=['POST'])
@login_required
def api_create_ticket():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'description']):
        abort(400, description="Thiếu title hoặc description.")

    new_ticket = Ticket(title=data['title'], description=data['description'], priority=data.get('priority', 'medium'), created_by=current_user.id)
    db.session.add(new_ticket)
    db.session.commit()
    return jsonify({'message': 'Tạo ticket thành công', 'ticket_id': new_ticket.id}), 201

@main.route("/api/tickets/<int:ticket_id>", methods=['PUT'])
@login_required
@support_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()

    if 'status' in data:
        ticket.status = data['status']
    if 'priority' in data:
        ticket.priority = data['priority']
    if 'assigned_to' in data:
        user_to_assign = User.query.get(data['assigned_to'])
        if user_to_assign and user_to_assign.is_support():
             ticket.assigned_to = data['assigned_to']
        else:
            return jsonify({'error': 'Người được gán không hợp lệ hoặc không có quyền hỗ trợ.'}), 400

    db.session.commit()
    return jsonify({'message': f'Ticket {ticket_id} đã được cập nhật.'})

@main.route('/fixadmin')
def fix_admin_account():
    # Tìm tài khoản admin
    admin_user = User.query.filter_by(email='admin@example.com').first()

    if not admin_user:
        return "<h1>LỖI</h1><p>Không tìm thấy user 'admin@example.com'. </p>"

    # Mật khẩu mới chắc chắn đúng
    password = 'admin'

    # Dùng chính thư viện bcrypt của app để tạo hash mới
    new_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Cập nhật hash mới cho user và lưu vào database
    admin_user.password_hash = new_hash
    db.session.commit()

    print("--- ĐÃ SỬA MẬT KHẨU ADMIN THÀNH CÔNG ---")
    print(f"Hash mới đã được lưu vào database: {new_hash}")

    return "<h1>Đã sửa thành công!</h1><p>Mật khẩu của 'admin@example.com' đã được reset về 'admin'. Vui lòng quay lại trang đăng nhập và thử lại.</p>"

@main.route("/ticket/rating/thanks")
@login_required
def rating_thanks():
    """Trang này chỉ hiển thị lời cảm ơn sau khi người dùng đánh giá."""
    return render_template('thanks_rating.html', title='Cảm ơn bạn')

@main.route('/uploads/<filename>')
@login_required
def download_attachment(filename):
    # Bước 1: Tìm thông tin file trong database dựa trên tên file trên server (filepath)
    attachment = Attachment.query.filter_by(filepath=filename).first_or_404()
    
    # Bước 2: Lấy thông tin ticket chứa file này
    ticket = attachment.ticket
    
    # Bước 3: Kiểm tra quyền của người dùng hiện tại
    # Cho phép tải nếu:
    # - Người dùng là admin/support, HOẶC
    # - Người dùng là người đã tạo ra ticket này
    if not current_user.is_support() and current_user.id != ticket.created_by:
        abort(403) # Nếu không có quyền, từ chối truy cập

    # Bước 4: Nếu có quyền, cho phép tải file
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/api/chatbot', methods=['POST'])
@login_required
def handle_chatbot_message():
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    ai_response = chatbot_service.get_ai_response(user_message)
    
    return jsonify({'reply': ai_response})