from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import School, Category, Course, Instructor, CourseInstructor, Rating, Comment, Tag, CourseTag, RatingReaction

class Command(BaseCommand):
    help = "Seed multiple demo courses, instructors, ratings, comments, and tags"

    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(username="admin").first()
        s1, _ = School.objects.get_or_create(
            school_id=10002,
            defaults={"name": "示例理工大学", "school_type": "university", "country": "中国", "city": "上海"},
        )
        c_comp = Category.objects.get_or_create(name="计算机")[0]
        c_hum = Category.objects.get_or_create(name="人文社科")[0]
        c_sci = Category.objects.get_or_create(name="理学")[0]

        u1, _ = User.objects.get_or_create(username="student1", defaults={"email": "student1@example.com"})
        u1.set_password("password123")
        u1.save()
        u2, _ = User.objects.get_or_create(username="student2", defaults={"email": "student2@example.com"})
        u2.set_password("password123")
        u2.save()
        u3, _ = User.objects.get_or_create(username="student3", defaults={"email": "student3@example.com"})
        u3.set_password("password123")
        u3.save()
        u4, _ = User.objects.get_or_create(username="student4", defaults={"email": "student4@example.com"})
        u4.set_password("password123")
        u4.save()
        u5, _ = User.objects.get_or_create(username="student5", defaults={"email": "student5@example.com"})
        u5.set_password("password123")
        u5.save()

        data = [
            {
                "course": {"course_id": 30002, "code": "CS102", "title": "数据结构基础", "category": c_comp, "school": s1},
                "instructors": [
                    {"instructor_id": 40011, "name": "张老师", "semester": "秋季", "year": 2025},
                    {"instructor_id": 40012, "name": "李老师", "semester": "春季", "year": 2026},
                ],
                "ratings": [
                    {"rating_id": 70011, "user": u1, "overall": 4, "diff": 3, "use": 4, "work": 3, "text": "讲解清晰，作业适中", "ins": 40011},
                    {"rating_id": 70012, "user": u2, "overall": 5, "diff": 2, "use": 5, "work": 2, "text": "非常实用，推荐", "ins": 40011},
                    {"rating_id": 70013, "user": admin or u1, "overall": 3, "diff": 4, "use": 3, "work": 4, "text": "难度偏高", "ins": 40012},
                ],
                "tags": ["算法", "链表", "树"],
            },
            {
                "course": {"course_id": 30003, "code": "HUM201", "title": "社会学导论", "category": c_hum, "school": s1},
                "instructors": [
                    {"instructor_id": 40021, "name": "王老师", "semester": "秋季", "year": 2025},
                    {"instructor_id": 40022, "name": "赵老师", "semester": "春季", "year": 2026},
                ],
                "ratings": [
                    {"rating_id": 70021, "user": u1, "overall": 4, "diff": 2, "use": 4, "work": 2, "text": "讨论课氛围好", "ins": 40021},
                    {"rating_id": 70022, "user": u2, "overall": 3, "diff": 2, "use": 3, "work": 1, "text": "作业少，轻松", "ins": 40022},
                ],
                "tags": ["讨论", "理论", "案例"],
            },
            {
                "course": {"course_id": 30004, "code": "SCI110", "title": "高等数学A", "category": c_sci, "school": s1},
                "instructors": [
                    {"instructor_id": 40031, "name": "钱老师", "semester": "秋季", "year": 2025},
                    {"instructor_id": 40032, "name": "孙老师", "semester": "春季", "year": 2026},
                ],
                "ratings": [
                    {"rating_id": 70031, "user": u1, "overall": 3, "diff": 5, "use": 4, "work": 5, "text": "难度大，作业多", "ins": 40031},
                    {"rating_id": 70032, "user": u2, "overall": 4, "diff": 4, "use": 4, "work": 4, "text": "讲义详尽", "ins": 40032},
                ],
                "tags": ["证明", "微积分", "作业多"],
            },
            {
                "course": {"course_id": 30005, "code": "CS210", "title": "数据库系统", "category": c_comp, "school": s1},
                "instructors": [
                    {"instructor_id": 40041, "name": "周老师", "semester": "秋季", "year": 2025},
                    {"instructor_id": 40042, "name": "吴老师", "semester": "春季", "year": 2026},
                ],
                "ratings": [
                    {"rating_id": 70041, "user": u1, "overall": 5, "diff": 3, "use": 5, "work": 3, "text": "项目实践多，受益匪浅", "ins": 40041},
                    {"rating_id": 70042, "user": u2, "overall": 4, "diff": 3, "use": 4, "work": 2, "text": "课程安排合理", "ins": 40042},
                ],
                "tags": ["SQL", "事务", "索引"],
            },
        ]

        ct_id = 90001
        next_tag_id = (Tag.objects.order_by('-tag_id').values_list('tag_id', flat=True).first() or 10000) + 1
        ci_id = 51000
        for entry in data:
            cdef = entry["course"]
            course, _ = Course.objects.get_or_create(
                course_id=cdef["course_id"],
                defaults={
                    "code": cdef.get("code"),
                    "title": cdef["title"],
                    "school": cdef["school"],
                    "category": cdef["category"],
                    "status": "approved",
                    "created_at": timezone.now(),
                },
            )
            for insdef in entry["instructors"]:
                ins, _ = Instructor.objects.get_or_create(
                    instructor_id=insdef["instructor_id"],
                    defaults={"name": insdef["name"], "school": cdef["school"]},
                )
                ci_id += 1
                CourseInstructor.objects.get_or_create(
                    id=ci_id,
                    defaults={
                        "course": course,
                        "instructor": ins,
                        "semester": insdef.get("semester"),
                        "year": insdef.get("year"),
                    },
                )

            for rdef in entry["ratings"]:
                ins = Instructor.objects.get(instructor_id=rdef["ins"]) if rdef.get("ins") else None
                Rating.objects.get_or_create(
                    rating_id=rdef["rating_id"],
                    defaults={
                        "user": rdef["user"],
                        "course": course,
                        "instructor": ins,
                        "overall_score": rdef["overall"],
                        "difficulty": rdef["diff"],
                        "usefulness": rdef["use"],
                        "workload": rdef["work"],
                        "comment_text": rdef["text"],
                        "anonymous_flag": False,
                        "created_at": timezone.now(),
                    },
                )

            for tname in entry["tags"]:
                try:
                    tag = Tag.objects.get(name=tname)
                except Tag.DoesNotExist:
                    tag = Tag(tag_id=next_tag_id, name=tname)
                    tag.save()
                    next_tag_id += 1
                ct_id += 1
                CourseTag.objects.get_or_create(
                    id=ct_id,
                    defaults={
                        "course": course,
                        "tag": tag,
                        "user": admin or u1,
                        "created_at": timezone.now(),
                    },
                )

        # attach some comments to ratings
        com_id = (Comment.objects.order_by('-comment_id').values_list('comment_id', flat=True).first() or 80000) + 1
        react_id = (RatingReaction.objects.order_by('-id').values_list('id', flat=True).first() or 90000) + 1
        r_all = Rating.objects.filter(rating_id__gte=70011, rating_id__lte=70042)
        from random import randint, choice
        commenters = [u1, u2, u3, u4, u5]
        for r in r_all:
            base_comments = [
                "老师讲义很详细，理解难点有帮助。",
                "课堂互动较多，收获不少。",
                "节奏稍快，建议提前预习。",
                "作业有点多，但能巩固知识。",
            ]
            # create 3-5 root comments
            for _ in range(randint(3, 5)):
                txt = choice(base_comments)
                c = Comment.objects.create(
                    comment_id=com_id,
                    rating=r,
                    user=choice(commenters),
                    parent_comment=None,
                    text=txt,
                    created_at=timezone.now(),
                )
                com_id += 1
                # replies 0-2
                for _r in range(randint(0, 2)):
                    Comment.objects.create(
                        comment_id=com_id,
                        rating=r,
                        user=choice(commenters),
                        parent_comment=c,
                        text=choice([
                            "赞同你的观点。",
                            "能否分享一下学习资料？",
                            "我上的是另一位老师，体验不同。",
                        ]),
                        created_at=timezone.now(),
                    )
                    com_id += 1
            # reactions: helpful / not_helpful
            for _ in range(randint(2, 7)):
                RatingReaction.objects.create(
                    id=react_id,
                    rating=r,
                    user=choice(commenters),
                    reaction_type="helpful",
                    created_at=timezone.now(),
                )
                react_id += 1
            for _ in range(randint(0, 3)):
                RatingReaction.objects.create(
                    id=react_id,
                    rating=r,
                    user=choice(commenters),
                    reaction_type="not_helpful",
                    created_at=timezone.now(),
                )
                react_id += 1
        self.stdout.write(self.style.SUCCESS("Seeded more demo courses, instructors, ratings, comments and tags."))
