from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(255))
    country = db.Column(db.String(100))
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('Rating', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')
    reactions = db.relationship('RatingReaction', backref='user', lazy=True)
    reports = db.relationship('Report', foreign_keys='Report.reporter_id', backref='reporter', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def get_id(self):
        return self.user_id

class School(db.Model):
    __tablename__ = 'school'
    
    school_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    school_type = db.Column(db.String(20), default='university')  # 'high_school' or 'university'
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    
    # Relationships
    courses = db.relationship('Course', backref='school', lazy=True)
    instructors = db.relationship('Instructor', backref='school', lazy=True)

class Course(db.Model):
    __tablename__ = 'course'
    
    course_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))
    school_id = db.Column(db.Integer, db.ForeignKey('school.school_id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))  # 创建者
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('Rating', backref='course', lazy=True, cascade='all, delete-orphan')
    course_instructors = db.relationship('CourseInstructor', backref='course', lazy=True, cascade='all, delete-orphan')
    course_tags = db.relationship('CourseTag', backref='course', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='course', lazy=True, cascade='all, delete-orphan')

class Instructor(db.Model):
    __tablename__ = 'instructor'
    
    instructor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    profile = db.Column(db.Text)
    school_id = db.Column(db.Integer, db.ForeignKey('school.school_id'))
    
    # Relationships
    course_instructors = db.relationship('CourseInstructor', backref='instructor', lazy=True, cascade='all, delete-orphan')

class CourseInstructor(db.Model):
    __tablename__ = 'course_instructor'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.instructor_id'), nullable=False)
    semester = db.Column(db.String(50))
    year = db.Column(db.Integer)
    
    db.UniqueConstraint('course_id', 'instructor_id', name='unique_course_instructor')

class Rating(db.Model):
    __tablename__ = 'rating'
    
    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    overall_score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    usefulness = db.Column(db.Integer, nullable=False)
    workload = db.Column(db.Integer, nullable=False)
    comment_text = db.Column(db.Text)
    anonymous_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='rating', lazy=True, cascade='all, delete-orphan')
    reactions = db.relationship('RatingReaction', backref='rating', lazy=True, cascade='all, delete-orphan')
    # Note: Reports are accessed via Report.query.filter_by(reported_entity_type='rating', entity_id=rating_id)
    
    db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_rating')

class Comment(db.Model):
    __tablename__ = 'comment'
    
    comment_id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey('rating.rating_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.comment_id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for nested comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[comment_id]), lazy=True)

class Tag(db.Model):
    __tablename__ = 'tag'
    
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    course_tags = db.relationship('CourseTag', backref='tag', lazy=True)

class CourseTag(db.Model):
    __tablename__ = 'course_tag'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.tag_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RatingReaction(db.Model):
    __tablename__ = 'rating_reaction'
    
    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey('rating.rating_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # 'helpful' or 'not_helpful'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    db.UniqueConstraint('rating_id', 'user_id', name='unique_rating_user_reaction')

class Report(db.Model):
    __tablename__ = 'report'
    
    report_id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    reported_entity_type = db.Column(db.String(20), nullable=False)  # 'rating', 'comment', 'tag'
    entity_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'resolved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Favorite(db.Model):
    __tablename__ = 'favorite'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_favorite')

