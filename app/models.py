# -*- coding: utf-8 -*-
from datetime import datetime
from . import db, login_manager # Đảm bảo import đúng cách
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # --- THÊM MỚI ---
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    department = db.Column(db.String(100))
    last_login_at = db.Column(db.DateTime, nullable=True)
    # ------------------
    role = db.Column(db.Enum('user', 'support', 'admin'), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.created_by', backref='author', lazy=True, cascade="all, delete-orphan")
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to', backref='assignee', lazy=True)
    reviews_received = db.relationship('Review', backref='employee', lazy='dynamic', foreign_keys='Review.reviewed_employee_id', cascade="all, delete-orphan")
    # attachments_uploaded sẽ được truy cập qua Attachment.uploader

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_support(self):
        return self.role in ['support', 'admin']

    def __repr__(self):
        return f'<User {self.username}>'

# THÊM MỚI
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Enum('low', 'medium', 'high'), nullable=False, default='medium')
    status = db.Column(db.Enum('open', 'in_progress', 'closed'), nullable=False, default='open')
    # --- THÊM MỚI ---
    resolution_details = db.Column(db.Text)
    closed_at = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    # ------------------
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    review = db.relationship('Review', backref='ticket', uselist=False, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    # Thêm relationship mới
    activity_logs = db.relationship('ActivityLog', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # --- THÊM MỚI ---
    is_internal = db.Column(db.Boolean, default=False)
    # ------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    author = db.relationship('User')

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    # --- THÊM MỚI ---
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uploader = db.relationship('User') # Để dễ truy cập thông tin người upload
    # ------------------
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False, unique=True)
    reviewed_employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Review for Ticket {self.ticket_id} - {self.rating} stars>'

# Thêm model mới hoàn toàn
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship('User')

    def __repr__(self):
        return f'<ActivityLog {self.id} for Ticket {self.ticket_id}>'