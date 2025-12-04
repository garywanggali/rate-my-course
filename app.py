from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps

from models import db, User, School, Course, Instructor, CourseInstructor, Rating, Comment, Tag, CourseTag, RatingReaction, Report, Favorite

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rate_my_course.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您需要管理员权限才能访问此页面。')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Get top courses (only courses with ratings and approved)
    top_courses = db.session.query(
        Course,
        db.func.avg(Rating.overall_score).label('avg_score'),
        db.func.count(Rating.rating_id).label('rating_count')
    ).join(Rating, Course.course_id == Rating.course_id)\
     .filter(Course.status == 'approved')\
     .group_by(Course.course_id)\
     .having(db.func.count(Rating.rating_id) > 0)\
     .order_by(db.func.avg(Rating.overall_score).desc())\
     .limit(10).all()
    
    recent_ratings = Rating.query.join(Course).filter(Course.status == 'approved')\
        .order_by(Rating.created_at.desc()).limit(5).all()
    
    return render_template('index.html', top_courses=top_courses, recent_ratings=recent_ratings)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        country = request.form.get('country', '')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            country=country,
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/courses')
def courses():
    search = request.args.get('search', '')
    school_id = request.args.get('school_id', type=int)
    school_type = request.args.get('school_type', '')
    department = request.args.get('department', '')
    min_score = request.args.get('min_score', type=float)
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Only show approved courses to regular users
    query = Course.query.filter(Course.status == 'approved')
    
    # Track if we've joined School table
    school_joined = False
    
    if search:
        # Search in course fields, instructor names, and school names
        # Use distinct() to avoid duplicate results when a course has multiple instructors
        query = query.outerjoin(CourseInstructor).outerjoin(Instructor).outerjoin(School).filter(
            (Course.title.contains(search)) |
            (Course.code.contains(search)) |
            (Course.description.contains(search)) |
            (Instructor.name.contains(search)) |
            (School.name.contains(search))
        ).distinct()
        school_joined = True
    
    if school_id:
        query = query.filter(Course.school_id == school_id)
    
    if school_type:
        if not school_joined:
            query = query.join(School)
        query = query.filter(School.school_type == school_type)
    
    if department:
        query = query.filter(Course.department.contains(department))
    
    if tag:
        query = query.join(CourseTag).join(Tag).filter(Tag.name.contains(tag))
    
    courses = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate average scores for each course
    for course in courses.items:
        ratings = Rating.query.filter_by(course_id=course.course_id).all()
        if ratings:
            course.avg_score = sum(r.overall_score for r in ratings) / len(ratings)
            course.rating_count = len(ratings)
        else:
            course.avg_score = 0
            course.rating_count = 0
    
    schools = School.query.order_by(School.name).all()
    departments = db.session.query(Course.department).distinct().all()
    tags = Tag.query.limit(20).all()
    
    return render_template('courses.html', courses=courses, schools=schools, 
                         departments=departments, tags=tags, search=search,
                         school_id=school_id, school_type=school_type, department=department, tag=tag)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if course is approved or user is admin/creator
    if course.status != 'approved':
        if not current_user.is_authenticated or (current_user.role != 'admin' and current_user.user_id != course.created_by):
            flash('该课程正在审核中，暂时无法查看。')
            return redirect(url_for('courses'))
    
    # Get ratings with user info
    ratings = Rating.query.filter_by(course_id=course_id).order_by(Rating.created_at.desc()).all()
    
    # Calculate averages
    if ratings:
        avg_overall = sum(r.overall_score for r in ratings) / len(ratings)
        avg_difficulty = sum(r.difficulty for r in ratings) / len(ratings)
        avg_usefulness = sum(r.usefulness for r in ratings) / len(ratings)
        avg_workload = sum(r.workload for r in ratings) / len(ratings)
    else:
        avg_overall = avg_difficulty = avg_usefulness = avg_workload = 0
    
    # Get instructors
    instructors = db.session.query(Instructor).join(CourseInstructor).filter(
        CourseInstructor.course_id == course_id
    ).all()
    
    # Get tags
    course_tags = db.session.query(Tag).join(CourseTag).filter(
        CourseTag.course_id == course_id
    ).all()
    available_tags = Tag.query.order_by(Tag.name).limit(100).all()
    
    # Get user's favorite status
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.user_id,
            course_id=course_id
        ).first() is not None
    
    return render_template('course_detail.html', course=course, ratings=ratings,
                         avg_overall=avg_overall, avg_difficulty=avg_difficulty,
                         avg_usefulness=avg_usefulness, avg_workload=avg_workload,
                         instructors=instructors, course_tags=course_tags,
                         available_tags=available_tags,
                         is_favorite=is_favorite)

@app.route('/course/<int:course_id>/rate', methods=['POST'])
@login_required
def rate_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user already rated this course
    existing_rating = Rating.query.filter_by(
        user_id=current_user.user_id,
        course_id=course_id
    ).first()
    
    if existing_rating:
        flash('You have already rated this course. You can edit your rating.')
        return redirect(url_for('course_detail', course_id=course_id))
    
    rating = Rating(
        user_id=current_user.user_id,
        course_id=course_id,
        overall_score=request.form.get('overall_score', type=int),
        difficulty=request.form.get('difficulty', type=int),
        usefulness=request.form.get('usefulness', type=int),
        workload=request.form.get('workload', type=int),
        comment_text=request.form.get('comment_text', ''),
        anonymous_flag=request.form.get('anonymous_flag') == 'on'
    )
    
    db.session.add(rating)
    
    # Add tags
    tag_names = request.form.getlist('tags')
    for tag_name in tag_names:
        if tag_name.strip():
            tag = Tag.query.filter_by(name=tag_name.strip()).first()
            if not tag:
                tag = Tag(name=tag_name.strip())
                db.session.add(tag)
                db.session.flush()
            
            course_tag = CourseTag(
                course_id=course_id,
                tag_id=tag.tag_id,
                user_id=current_user.user_id
            )
            db.session.add(course_tag)
    
    db.session.commit()
    flash('Rating submitted successfully!')
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/rating/<int:rating_id>/comment', methods=['POST'])
@login_required
def add_comment(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    parent_id = request.form.get('parent_comment_id', type=int)
    
    comment = Comment(
        rating_id=rating_id,
        user_id=current_user.user_id,
        parent_comment_id=parent_id if parent_id else None,
        text=request.form.get('text', '')
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return redirect(url_for('course_detail', course_id=rating.course_id))

@app.route('/rating/<int:rating_id>/reaction', methods=['POST'])
@login_required
def add_reaction(rating_id):
    reaction_type = request.form.get('reaction_type')
    
    # Check if user already reacted
    existing = RatingReaction.query.filter_by(
        user_id=current_user.user_id,
        rating_id=rating_id
    ).first()
    
    if existing:
        existing.reaction_type = reaction_type
    else:
        reaction = RatingReaction(
            user_id=current_user.user_id,
            rating_id=rating_id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
    
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/course/<int:course_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(course_id):
    favorite = Favorite.query.filter_by(
        user_id=current_user.user_id,
        course_id=course_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        action = 'removed'
    else:
        favorite = Favorite(
            user_id=current_user.user_id,
            course_id=course_id
        )
        db.session.add(favorite)
        action = 'added'
    
    db.session.commit()
    return jsonify({'status': 'success', 'action': action})

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    ratings = Rating.query.filter_by(user_id=user_id).order_by(Rating.created_at.desc()).all()
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    favorite_courses = [Course.query.get(f.course_id) for f in favorites]
    
    return render_template('user_profile.html', user=user, ratings=ratings,
                         favorite_courses=favorite_courses)

@app.route('/instructor/<int:instructor_id>')
def instructor_profile(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    
    # Get courses taught by this instructor
    courses = db.session.query(Course).join(CourseInstructor).filter(
        CourseInstructor.instructor_id == instructor_id
    ).all()
    
    # Calculate average rating
    all_ratings = []
    for course in courses:
        course_ratings = Rating.query.filter_by(course_id=course.course_id).all()
        all_ratings.extend(course_ratings)
    
    avg_score = sum(r.overall_score for r in all_ratings) / len(all_ratings) if all_ratings else 0
    
    return render_template('instructor_profile.html', instructor=instructor,
                         courses=courses, avg_score=avg_score, rating_count=len(all_ratings))

@app.route('/rankings')
def rankings():
    school_id = request.args.get('school_id', type=int)
    department = request.args.get('department', '')
    
    query = db.session.query(
        Course,
        db.func.avg(Rating.overall_score).label('avg_score'),
        db.func.count(Rating.rating_id).label('rating_count')
    ).join(Rating, Course.course_id == Rating.course_id)\
     .filter(Course.status == 'approved')\
     .group_by(Course.course_id)\
     .having(db.func.count(Rating.rating_id) > 0)
    
    if school_id:
        query = query.filter(Course.school_id == school_id)
    
    if department:
        query = query.filter(Course.department.contains(department))
    
    top_courses = query.order_by(
        db.func.avg(Rating.overall_score).desc()
    ).limit(10).all()
    
    schools = School.query.all()
    departments = db.session.query(Course.department).distinct().all()
    
    return render_template('rankings.html', top_courses=top_courses,
                         schools=schools, departments=departments,
                         school_id=school_id, department=department)

@app.route('/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        code = request.form.get('code', '')
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        department = request.form.get('department', '')
        school_id = request.form.get('school_id', type=int)
        
        if not title or not school_id:
            flash('课程名称和学校是必填项')
            return redirect(url_for('create_course'))
        
        # Set status: approved for admin, pending for students
        status = 'approved' if current_user.role == 'admin' else 'pending'
        
        course = Course(
            code=code,
            title=title,
            description=description,
            department=department,
            school_id=school_id,
            created_by=current_user.user_id,
            status=status
        )
        db.session.add(course)
        db.session.flush()
        
        # Add instructor if provided
        instructor_name = request.form.get('instructor_name', '')
        if instructor_name:
            instructor = Instructor.query.filter_by(name=instructor_name, school_id=school_id).first()
            if not instructor:
                instructor = Instructor(name=instructor_name, school_id=school_id)
                db.session.add(instructor)
                db.session.flush()
            
            ci = CourseInstructor(
                course_id=course.course_id,
                instructor_id=instructor.instructor_id,
                semester=request.form.get('semester', ''),
                year=request.form.get('year', type=int)
            )
            db.session.add(ci)
        
        db.session.commit()
        
        if status == 'approved':
            flash('课程创建成功！')
            return redirect(url_for('course_detail', course_id=course.course_id))
        else:
            flash('课程已提交，等待管理员审核。审核通过后即可在课程列表中看到。')
            return redirect(url_for('my_courses'))
    
    schools = School.query.all()
    return render_template('create_course.html', schools=schools)

@app.route('/report', methods=['POST'])
@login_required
def report():
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id', type=int)
    reason = request.form.get('reason', '')
    
    report = Report(
        reporter_id=current_user.user_id,
        reported_entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        status='pending'
    )
    
    db.session.add(report)
    db.session.commit()
    
    flash('Report submitted. Thank you for helping maintain the quality of our platform.')
    return redirect(request.referrer or url_for('index'))

@app.route('/my-courses')
@login_required
def my_courses():
    """显示用户提交的课程"""
    courses = Course.query.filter_by(created_by=current_user.user_id)\
        .order_by(Course.created_at.desc()).all()
    return render_template('my_courses.html', courses=courses)

@app.route('/admin/pending-courses')
@admin_required
def pending_courses():
    """管理员查看待审核的课程"""
    pending = Course.query.filter_by(status='pending')\
        .order_by(Course.created_at.desc()).all()
    # Get creators for each course
    for course in pending:
        if course.created_by:
            course.creator = User.query.get(course.created_by)
        else:
            course.creator = None
    return render_template('admin/pending_courses.html', courses=pending)

@app.route('/admin/course/<int:course_id>/approve', methods=['POST'])
@admin_required
def approve_course(course_id):
    """管理员审核通过课程"""
    course = Course.query.get_or_404(course_id)
    course.status = 'approved'
    db.session.commit()
    flash(f'课程 "{course.title}" 已审核通过。')
    return redirect(url_for('pending_courses'))

@app.route('/admin/course/<int:course_id>/reject', methods=['POST'])
@admin_required
def reject_course(course_id):
    """管理员拒绝课程"""
    course = Course.query.get_or_404(course_id)
    course.status = 'rejected'
    db.session.commit()
    flash(f'课程 "{course.title}" 已拒绝。')
    return redirect(url_for('pending_courses'))

@app.route('/admin/schools')
@admin_required
def admin_schools():
    """管理员查看所有学校"""
    schools = School.query.order_by(School.name).all()
    # Get course count for each school
    for school in schools:
        school.course_count = Course.query.filter_by(school_id=school.school_id, status='approved').count()
        school.instructor_count = Instructor.query.filter_by(school_id=school.school_id).count()
    return render_template('admin/schools.html', schools=schools)

@app.route('/admin/school/create', methods=['GET', 'POST'])
@admin_required
def create_school():
    """管理员创建学校"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        school_type = request.form.get('school_type', 'university')
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        
        if not name:
            flash('学校名称是必填项')
            return redirect(url_for('create_school'))
        
        if school_type not in ['high_school', 'university']:
            school_type = 'university'
        
        # Check if school already exists
        existing = School.query.filter_by(name=name).first()
        if existing:
            flash('该学校已存在')
            return redirect(url_for('create_school'))
        
        school = School(
            name=name,
            school_type=school_type,
            country=country if country else None,
            city=city if city else None
        )
        db.session.add(school)
        db.session.commit()
        
        flash(f'学校 "{name}" 创建成功！')
        return redirect(url_for('admin_schools'))
    
    return render_template('admin/create_school.html')

@app.route('/admin/school/<int:school_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_school(school_id):
    """管理员编辑学校"""
    school = School.query.get_or_404(school_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        school_type = request.form.get('school_type', 'university')
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        
        if not name:
            flash('学校名称是必填项')
            return redirect(url_for('edit_school', school_id=school_id))
        
        if school_type not in ['high_school', 'university']:
            school_type = 'university'
        
        # Check if name conflicts with another school
        existing = School.query.filter(School.name == name, School.school_id != school_id).first()
        if existing:
            flash('该学校名称已被使用')
            return redirect(url_for('edit_school', school_id=school_id))
        
        school.name = name
        school.school_type = school_type
        school.country = country if country else None
        school.city = city if city else None
        db.session.commit()
        
        flash(f'学校信息已更新')
        return redirect(url_for('admin_schools'))
    
    return render_template('admin/edit_school.html', school=school)

@app.route('/admin/school/<int:school_id>/delete', methods=['POST'])
@admin_required
def delete_school(school_id):
    """管理员删除学校"""
    school = School.query.get_or_404(school_id)
    
    # Check if school has courses or instructors
    course_count = Course.query.filter_by(school_id=school_id).count()
    instructor_count = Instructor.query.filter_by(school_id=school_id).count()
    
    if course_count > 0 or instructor_count > 0:
        flash(f'无法删除学校 "{school.name}"，因为该学校下还有 {course_count} 门课程和 {instructor_count} 位教师。')
        return redirect(url_for('admin_schools'))
    
    db.session.delete(school)
    db.session.commit()
    flash(f'学校 "{school.name}" 已删除')
    return redirect(url_for('admin_schools'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

