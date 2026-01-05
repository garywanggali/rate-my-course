from django.db import models
from django.conf import settings


"""All user references now point to Django auth user."""


class School(models.Model):
    school_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    SCHOOL_TYPE_CHOICES = (
        ("university", "university"),
        ("highschool", "highschool"),
    )
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPE_CHOICES, default="university")
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "school"
        managed = True

    def __str__(self):
        return self.name


class Course(models.Model):
    course_id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, db_column='category_id', to_field='category_id')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, db_column="school_id", to_field="school_id")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_column="created_by")
    STATUS_CHOICES = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "course"
        managed = True

    def __str__(self):
        return f"{self.title}" if not self.code else f"{self.title} ({self.code})"


class Instructor(models.Model):
    instructor_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    profile = models.TextField(null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, db_column="school_id", to_field="school_id")

    class Meta:
        db_table = "instructor"
        managed = True

    def __str__(self):
        return self.name


class Category(models.Model):
    category_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "category"
        managed = True

    def __str__(self):
        return self.name


class CourseInstructor(models.Model):
    id = models.IntegerField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", to_field="course_id")
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, db_column="instructor_id", to_field="instructor_id")
    semester = models.CharField(max_length=50, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "course_instructor"
        managed = True


class Rating(models.Model):
    rating_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", to_field="course_id")
    instructor = models.ForeignKey('Instructor', on_delete=models.SET_NULL, null=True, db_column='instructor_id', to_field='instructor_id')
    overall_score = models.IntegerField()
    difficulty = models.IntegerField()
    usefulness = models.IntegerField()
    workload = models.IntegerField()
    comment_text = models.TextField(null=True, blank=True)
    anonymous_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rating"
        managed = True


class Comment(models.Model):
    comment_id = models.IntegerField(primary_key=True)
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE, db_column="rating_id", to_field="rating_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    parent_comment = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, db_column="parent_comment_id", to_field="comment_id")
    text = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "comment"
        managed = True


class Tag(models.Model):
    tag_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "tag"
        managed = True

    def __str__(self):
        return self.name


class CourseTag(models.Model):
    id = models.IntegerField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", to_field="course_id")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_column="tag_id", to_field="tag_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "course_tag"
        managed = True


class RatingReaction(models.Model):
    id = models.IntegerField(primary_key=True)
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE, db_column="rating_id", to_field="rating_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    reaction_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rating_reaction"
        managed = True


class Report(models.Model):
    report_id = models.IntegerField(primary_key=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="reporter_id")
    reported_entity_type = models.CharField(max_length=20)
    entity_id = models.IntegerField()
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "report"
        managed = True


class Favorite(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", to_field="course_id")
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "favorite"
        managed = True


class UserDisclaimer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    accepted_at = models.DateTimeField()

    class Meta:
        db_table = "user_disclaimer"
        managed = True
