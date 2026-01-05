from django.contrib import admin
from .models import School, Course, Instructor, Rating, Comment, Tag, CourseTag, RatingReaction, Report, Favorite, Category, CourseInstructor


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("school_id", "name", "school_type", "country", "city")
    search_fields = ("name", "country", "city")
    list_filter = ("school_type",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name")
    search_fields = ("name",)


class CourseInstructorInline(admin.TabularInline):
    model = CourseInstructor
    extra = 1
    fields = ("instructor", "semester", "year")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_id", "title", "code", "school", "category", "status")
    search_fields = ("title", "code")
    list_filter = ("status", "school__school_type", "category")
    inlines = [CourseInstructorInline]

    def get_changeform_initial_data(self, request):
        return {"status": "approved"}


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("instructor_id", "name", "school")
    search_fields = ("name",)
    list_filter = ("school",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("tag_id", "name")
    search_fields = ("name",)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("rating_id", "course", "instructor", "user", "overall_score", "difficulty", "usefulness", "workload", "created_at")
    list_filter = ("overall_score", "difficulty", "usefulness", "workload")
    search_fields = ("course__title", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("comment_id", "rating", "user", "parent_comment", "created_at")
    search_fields = ("rating__course__title", "user__username", "text")


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "tag", "user", "created_at")
    search_fields = ("course__title", "tag__name", "user__username")


@admin.register(RatingReaction)
class RatingReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "rating", "user", "reaction_type", "created_at")
    list_filter = ("reaction_type",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("report_id", "reported_entity_type", "entity_id", "reporter", "status", "created_at")
    list_filter = ("reported_entity_type", "status")
    search_fields = ("reporter__username",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "user", "created_at")
    search_fields = ("course__title", "user__username")
