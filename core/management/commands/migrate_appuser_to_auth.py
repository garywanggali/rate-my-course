from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import AppUser, Course, Rating, Comment, CourseTag, RatingReaction, Report, Favorite


class Command(BaseCommand):
    help = "Migrate legacy AppUser (user table) to auth_user and relink foreign keys"

    def handle(self, *args, **options):
        User = get_user_model()
        created = 0
        linked = 0

        self.stdout.write("Building user mapping...")
        id_map = {}
        for au in AppUser.objects.all():
            user = User.objects.filter(username=au.username).first()
            if not user:
                # create auth user with unusable password; keep email
                user = User.objects.create(username=au.username, email=au.email)
                user.set_unusable_password()
                user.save()
                created += 1
            id_map[au.user_id] = user.id

        self.stdout.write(f"Auth users created: {created}")

        def relink(model, field_name):
            nonlocal linked
            qs = model.objects.all()
            updates = 0
            for obj in qs.iterator():
                old_id = getattr(obj, field_name)
                new_id = id_map.get(old_id)
                if new_id and new_id != old_id:
                    setattr(obj, field_name, new_id)
                    obj.save(update_fields=[field_name])
                    updates += 1
            linked += updates
            self.stdout.write(f"Relinked {updates} rows in {model._meta.db_table}.{field_name}")

        self.stdout.write("Relinking foreign keys...")
        with transaction.atomic():
            # Course.created_by
            relink(Course, "created_by_id")
            # Rating.user_id
            relink(Rating, "user_id")
            # Comment.user_id
            relink(Comment, "user_id")
            # CourseTag.user_id
            relink(CourseTag, "user_id")
            # RatingReaction.user_id
            relink(RatingReaction, "user_id")
            # Report.reporter_id
            relink(Report, "reporter_id")
            # Favorite.user_id
            relink(Favorite, "user_id")

        self.stdout.write(self.style.SUCCESS(f"Done. Total relinked rows: {linked}"))
