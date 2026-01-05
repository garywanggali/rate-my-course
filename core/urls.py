from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("courses/", views.courses, name="courses"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("course/<int:course_id>/random_comment/", views.random_course_comment, name="random_course_comment"),
    path("rankings/", views.rankings, name="rankings"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("disclaimer/", views.disclaimer, name="disclaimer"),
    path("course/<int:course_id>/rate/", views.rate_course, name="rate_course"),
    path("rating/<int:rating_id>/comment/", views.add_comment, name="add_comment"),
    path("rating/<int:rating_id>/reaction/", views.add_reaction, name="add_reaction"),
    path("course/<int:course_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("report/", views.report, name="report"),
    path("admin/pending-courses/", views.pending_courses, name="pending_courses"),
    path("admin/course/<int:course_id>/approve/", views.approve_course, name="approve_course"),
    path("admin/course/<int:course_id>/reject/", views.reject_course, name="reject_course"),
]
