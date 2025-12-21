from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import School, Category, Course, Instructor, CourseInstructor


class Command(BaseCommand):
    help = "Create demo school, category, and an approved course for front-end testing"

    def handle(self, *args, **options):
        # Ensure a school exists
        school, _ = School.objects.get_or_create(
            school_id=10001,
            defaults={
                "name": "示例大学",
                "school_type": "university",
                "country": "中国",
                "city": "北京",
            },
        )

        # Ensure a category exists
        category = Category.objects.filter(name="计算机").first()
        if not category:
            category = Category.objects.create(category_id=20001, name="计算机")

        # Ensure an admin user exists
        User = get_user_model()
        admin_user = User.objects.filter(username="admin").first()

        # Create an approved course
        course, created = Course.objects.get_or_create(
            course_id=30001,
            defaults={
                "code": "CS101",
                "title": "计算机科学导论（示例）",
                "description": "示例课程，用于前端列表验证。",
                "school": school,
                "category": category,
                "created_by": admin_user,
                "status": "approved",
                "created_at": timezone.now(),
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Demo course created and approved."))
        else:
            # ensure course is approved
            if course.status != "approved":
                course.status = "approved"
                course.save(update_fields=["status"])
            self.stdout.write("Demo course already exists; status set to approved.")

        # Ensure an instructor and teaching assignment
        instr, _ = Instructor.objects.get_or_create(
            instructor_id=40001,
            defaults={"name": "示例教师", "school": school},
        )
        ci, assigned = CourseInstructor.objects.get_or_create(
            id=50001,
            defaults={
                "course": course,
                "instructor": instr,
                "semester": "秋季",
                "year": 2025,
            },
        )
        if assigned:
            self.stdout.write(self.style.SUCCESS("Demo instructor and course assignment created."))
        else:
            # ensure linkage if existing id reused without relation
            if ci.course_id != course.course_id or ci.instructor_id != instr.instructor_id:
                ci.course = course
                ci.instructor = instr
                ci.save(update_fields=["course", "instructor"])
