from django.core.management.base import BaseCommand
from core.models import Category

DEFAULT_CATEGORIES = [
    "计算机",
    "人文社科",
    "理学",
    "工学",
    "经济管理",
    "艺术设计",
    "医学",
    "教育",
    "语言文学",
    "法学",
]

class Command(BaseCommand):
    help = "Seed default course categories"

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_CATEGORIES:
            obj, was_created = Category.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded categories. Newly created: {created}"))
