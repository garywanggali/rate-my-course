"""
Database initialization script with sample data
"""
from app import app, db
from models import User, School, Course, Instructor, CourseInstructor, Rating, Comment, Tag, CourseTag, Favorite
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Creating sample data...")
        
        # Create schools
        school1 = School(name="清华大学", school_type="university", country="中国", city="北京")
        school2 = School(name="北京大学", school_type="university", country="中国", city="北京")
        school3 = School(name="复旦大学", school_type="university", country="中国", city="上海")
        school4 = School(name="北京四中", school_type="high_school", country="中国", city="北京")
        school5 = School(name="上海中学", school_type="high_school", country="中国", city="上海")
        db.session.add_all([school1, school2, school3, school4, school5])
        db.session.flush()
        
        # Create users
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123", method='pbkdf2:sha256'),
            country="中国",
            role="admin"
        )
        user1 = User(
            username="student1",
            email="student1@example.com",
            password_hash=generate_password_hash("password123", method='pbkdf2:sha256'),
            country="中国"
        )
        user2 = User(
            username="student2",
            email="student2@example.com",
            password_hash=generate_password_hash("password123", method='pbkdf2:sha256'),
            country="中国"
        )
        db.session.add_all([admin, user1, user2])
        db.session.flush()
        
        # Create instructors
        instructor1 = Instructor(name="张教授", profile="计算机科学系教授，研究方向：人工智能", school_id=school1.school_id)
        instructor2 = Instructor(name="李教授", profile="数学系教授，研究方向：应用数学", school_id=school1.school_id)
        instructor3 = Instructor(name="王教授", profile="物理系教授，研究方向：量子物理", school_id=school2.school_id)
        db.session.add_all([instructor1, instructor2, instructor3])
        db.session.flush()
        
        # Create courses (approved by default for sample data)
        course1 = Course(
            code="CS101",
            title="计算机科学导论",
            description="介绍计算机科学的基本概念、历史发展和主要领域。",
            department="计算机科学系",
            school_id=school1.school_id,
            created_by=admin.user_id,
            status='approved'
        )
        course2 = Course(
            code="MATH201",
            title="高等数学",
            description="深入学习微积分、线性代数和数学分析。",
            department="数学系",
            school_id=school1.school_id,
            created_by=admin.user_id,
            status='approved'
        )
        course3 = Course(
            code="PHYS301",
            title="量子力学",
            description="量子力学的基本原理和应用。",
            department="物理系",
            school_id=school2.school_id,
            created_by=admin.user_id,
            status='approved'
        )
        course4 = Course(
            code="CS202",
            title="数据结构与算法",
            description="学习常用的数据结构和算法设计方法。",
            department="计算机科学系",
            school_id=school1.school_id,
            created_by=admin.user_id,
            status='approved'
        )
        db.session.add_all([course1, course2, course3, course4])
        db.session.flush()
        
        # Link courses and instructors
        ci1 = CourseInstructor(course_id=course1.course_id, instructor_id=instructor1.instructor_id, semester="秋季", year=2024)
        ci2 = CourseInstructor(course_id=course2.course_id, instructor_id=instructor2.instructor_id, semester="春季", year=2024)
        ci3 = CourseInstructor(course_id=course3.course_id, instructor_id=instructor3.instructor_id, semester="秋季", year=2024)
        ci4 = CourseInstructor(course_id=course4.course_id, instructor_id=instructor1.instructor_id, semester="春季", year=2024)
        db.session.add_all([ci1, ci2, ci3, ci4])
        
        # Create tags
        tag1 = Tag(name="内容扎实")
        tag2 = Tag(name="workload高")
        tag3 = Tag(name="考试友好")
        tag4 = Tag(name="容易拿A")
        tag5 = Tag(name="挑战高")
        db.session.add_all([tag1, tag2, tag3, tag4, tag5])
        db.session.flush()
        
        # Create ratings
        rating1 = Rating(
            user_id=user1.user_id,
            course_id=course1.course_id,
            overall_score=5,
            difficulty=3,
            usefulness=5,
            workload=4,
            comment_text="非常棒的课程！老师讲解清晰，内容实用。虽然作业有点多，但收获很大。",
            anonymous_flag=False
        )
        rating2 = Rating(
            user_id=user2.user_id,
            course_id=course1.course_id,
            overall_score=4,
            difficulty=2,
            usefulness=4,
            workload=3,
            comment_text="入门课程，难度适中，适合初学者。",
            anonymous_flag=False
        )
        rating3 = Rating(
            user_id=user1.user_id,
            course_id=course2.course_id,
            overall_score=3,
            difficulty=5,
            usefulness=4,
            workload=5,
            comment_text="难度很大，需要花很多时间。但学好了对后续课程帮助很大。",
            anonymous_flag=True
        )
        rating4 = Rating(
            user_id=user2.user_id,
            course_id=course4.course_id,
            overall_score=5,
            difficulty=4,
            usefulness=5,
            workload=4,
            comment_text="数据结构是编程的基础，这门课讲得很好。",
            anonymous_flag=False
        )
        db.session.add_all([rating1, rating2, rating3, rating4])
        db.session.flush()
        
        # Create course tags
        ct1 = CourseTag(course_id=course1.course_id, tag_id=tag1.tag_id, user_id=user1.user_id)
        ct2 = CourseTag(course_id=course1.course_id, tag_id=tag3.tag_id, user_id=user1.user_id)
        ct3 = CourseTag(course_id=course2.course_id, tag_id=tag2.tag_id, user_id=user1.user_id)
        ct4 = CourseTag(course_id=course2.course_id, tag_id=tag5.tag_id, user_id=user1.user_id)
        ct5 = CourseTag(course_id=course4.course_id, tag_id=tag1.tag_id, user_id=user2.user_id)
        ct6 = CourseTag(course_id=course4.course_id, tag_id=tag4.tag_id, user_id=user2.user_id)
        db.session.add_all([ct1, ct2, ct3, ct4, ct5, ct6])
        
        # Create comments
        comment1 = Comment(
            rating_id=rating1.rating_id,
            user_id=user2.user_id,
            text="同意！我也觉得这门课很棒。"
        )
        comment2 = Comment(
            rating_id=rating1.rating_id,
            user_id=user1.user_id,
            parent_comment_id=comment1.comment_id,
            text="谢谢！希望对你也有帮助。"
        )
        db.session.add_all([comment1, comment2])
        
        # Create favorites
        fav1 = Favorite(user_id=user1.user_id, course_id=course4.course_id)
        fav2 = Favorite(user_id=user2.user_id, course_id=course1.course_id)
        db.session.add_all([fav1, fav2])
        
        db.session.commit()
        print("Sample data created successfully!")
        print("\nTest accounts:")
        print("Admin: username=admin, password=admin123")
        print("Student1: username=student1, password=password123")
        print("Student2: username=student2, password=password123")

if __name__ == '__main__':
    init_database()

