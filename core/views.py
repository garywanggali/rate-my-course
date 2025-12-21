from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpRequest
from django.db.models import Avg, Count, Q
from .models import Course, Rating, School, Tag
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import Comment, Favorite, RatingReaction, CourseInstructor, Instructor, CourseTag, Report

from django.contrib.auth import get_user_model

def index(request: HttpRequest):
    ratings_qs = Rating.objects.filter(course__status="approved")
    agg = ratings_qs.values("course").annotate(avg_score=Avg("overall_score"), rating_count=Count("rating_id")).order_by("-avg_score")[:10]
    top_courses = []
    for row in agg:
        try:
            c = Course.objects.get(pk=row["course"])
            top_courses.append((c, row["avg_score"] or 0, row["rating_count"]))
        except Course.DoesNotExist:
            pass
    recent_ratings = ratings_qs.order_by("-created_at")[:5]
    return render(request, "index.html", {"top_courses": top_courses, "recent_ratings": recent_ratings})

def courses(request: HttpRequest):
    search = request.GET.get("search", "").strip()
    school_id = request.GET.get("school_id")
    school_type = request.GET.get("school_type", "")
    category_id = request.GET.get("category_id")
    tag = request.GET.get("tag", "")

    qs = Course.objects.all() if request.user.is_staff else Course.objects.filter(status="approved")
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(code__icontains=search)
            | Q(description__icontains=search)
            | Q(school__name__icontains=search)
        )
    if school_id:
        qs = qs.filter(school_id=school_id)
    if school_type:
        qs = qs.filter(school__school_type=school_type)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if tag:
        qs = qs.filter(coursetag__tag__name__icontains=tag)

    # annotate average and count via Rating relation
    # fallback: compute manually if annotation is complex on legacy tables
    courses_list = []
    for c in qs:
        ratings = Rating.objects.filter(course=c)
        if ratings.exists():
            avg_score = ratings.aggregate(a=Avg("overall_score"))["a"] or 0
            rating_count = ratings.count()
        else:
            avg_score = 0
            rating_count = 0
        setattr(c, "avg_score", avg_score)
        setattr(c, "rating_count", rating_count)
        courses_list.append(c)

    schools = School.objects.order_by("name")
    from .models import Category
    categories = Category.objects.order_by("name")
    tags = Tag.objects.all()[:20]

    return render(
        request,
        "courses.html",
        {
            "courses": courses_list,
            "schools": schools,
            "categories": categories,
            "tags": tags,
            "search": search,
            "school_id": int(school_id) if school_id else None,
            "school_type": school_type,
            "category_id": int(category_id) if category_id else None,
            "tag": tag,
        },
    )

def course_detail(request: HttpRequest, course_id: int):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "课程不存在")
        return redirect("courses")

    if course.status != "approved":
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.info(request, "该课程正在审核中，暂时无法查看。")
            return redirect("courses")

    ratings = Rating.objects.filter(course_id=course_id).order_by("-created_at")
    if ratings.exists():
        avg_overall = ratings.aggregate(a=Avg("overall_score"))["a"] or 0
        avg_difficulty = ratings.aggregate(a=Avg("difficulty"))["a"] or 0
        avg_usefulness = ratings.aggregate(a=Avg("usefulness"))["a"] or 0
        avg_workload = ratings.aggregate(a=Avg("workload"))["a"] or 0
    else:
        avg_overall = avg_difficulty = avg_usefulness = avg_workload = 0

    instructors = Instructor.objects.filter(courseinstructor__course_id=course_id)
    course_tags = Tag.objects.filter(coursetag__course_id=course_id)
    available_tags = Tag.objects.order_by("name")[:100]

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user_id=request.user.id, course_id=course_id).exists()

    return render(
        request,
        "course_detail.html",
        {
            "course": course,
            "ratings": ratings,
            "avg_overall": avg_overall,
            "avg_difficulty": avg_difficulty,
            "avg_usefulness": avg_usefulness,
            "avg_workload": avg_workload,
            "instructors": instructors,
            "course_tags": course_tags,
            "available_tags": available_tags,
            "is_favorite": is_favorite,
        },
    )

def register(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            messages.error(request, "用户名和密码为必填项")
            return redirect("register")
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "用户名已存在")
            return redirect("register")
        if email and User.objects.filter(email=email).exists():
            messages.error(request, "邮箱已注册")
            return redirect("register")
        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "注册成功，请登录")
        return redirect("login")
    return render(request, "register.html")

def login_view(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "index")
        messages.error(request, "用户名或密码错误")
    return render(request, "login.html")

def logout_view(request: HttpRequest):
    logout(request)
    return redirect("index")
@login_required
def rate_course(request: HttpRequest, course_id: int):
    try:
        Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "课程不存在")
        return redirect("courses")

    existing = Rating.objects.filter(user_id=request.user.id, course_id=course_id).first()
    if existing:
        messages.info(request, "您已评价过该课程，可修改评价。")
        return redirect("course_detail", course_id=course_id)

    r = Rating(
        user_id=request.user.id,
        course_id=course_id,
        overall_score=int(request.POST.get("overall_score", 0) or 0),
        difficulty=int(request.POST.get("difficulty", 0) or 0),
        usefulness=int(request.POST.get("usefulness", 0) or 0),
        workload=int(request.POST.get("workload", 0) or 0),
        comment_text=request.POST.get("comment_text", ""),
        anonymous_flag=request.POST.get("anonymous_flag") == "on",
        created_at=timezone.now(),
    )
    r.save()

    tag_names = request.POST.getlist("tags")
    for t in tag_names:
        name = (t or "").strip()
        if not name:
            continue
        tag_obj, _ = Tag.objects.get_or_create(name=name)
        CourseTag.objects.create(course_id=course_id, tag_id=tag_obj.tag_id, user_id=request.user.id, created_at=timezone.now())

    messages.success(request, "评价提交成功！")
    return redirect("course_detail", course_id=course_id)

@login_required
def add_comment(request: HttpRequest, rating_id: int):
    try:
        rating = Rating.objects.get(pk=rating_id)
    except Rating.DoesNotExist:
        messages.error(request, "评价不存在")
        return redirect("index")

    parent_id = request.POST.get("parent_comment_id")
    Comment.objects.create(
        rating_id=rating_id,
        user_id=request.user.id,
        parent_comment_id=int(parent_id) if parent_id else None,
        text=request.POST.get("text", ""),
        created_at=timezone.now(),
    )
    return redirect("course_detail", course_id=rating.course_id)

@login_required
def add_reaction(request: HttpRequest, rating_id: int):
    reaction_type = request.POST.get("reaction_type")
    existing = RatingReaction.objects.filter(user_id=request.user.id, rating_id=rating_id).first()
    if existing:
        existing.reaction_type = reaction_type
        existing.save()
    else:
        RatingReaction.objects.create(user_id=request.user.id, rating_id=rating_id, reaction_type=reaction_type, created_at=timezone.now())
    return redirect(request.META.get("HTTP_REFERER") or "index")

@login_required
def toggle_favorite(request: HttpRequest, course_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "请先登录"}, status=401)
    fav = Favorite.objects.filter(user_id=request.user.id, course_id=course_id).first()
    if fav:
        fav.delete()
        action = "removed"
    else:
        Favorite.objects.create(user_id=request.user.id, course_id=course_id, created_at=timezone.now())
        action = "added"
    return JsonResponse({"status": "success", "action": action})

@login_required
def report(request: HttpRequest):
    entity_type = request.POST.get("entity_type")
    entity_id = int(request.POST.get("entity_id") or 0)
    reason = request.POST.get("reason", "")
    Report.objects.create(
        reporter_id=request.user.id,
        reported_entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        status="pending",
        created_at=timezone.now(),
    )
    messages.success(request, "举报已提交，感谢你的反馈。")
    return redirect(request.META.get("HTTP_REFERER") or "index")

def admin_required(view_func):
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "需要管理员权限")
            return redirect("index")
        return view_func(request, *args, **kwargs)
    return _wrapped

@admin_required
def pending_courses(request: HttpRequest):
    pending = Course.objects.filter(status="pending").order_by("-created_at")
    for c in pending:
        if c.created_by_id:
            try:
                c.creator = get_user_model().objects.get(id=c.created_by_id)
            except get_user_model().DoesNotExist:
                c.creator = None
        else:
            c.creator = None
    return render(request, "admin/pending_courses.html", {"courses": pending})

@admin_required
def approve_course(request: HttpRequest, course_id: int):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "课程不存在")
        return redirect("pending_courses")
    course.status = "approved"
    course.save()
    messages.success(request, f"课程 \"{course.title}\" 已审核通过。")
    return redirect("pending_courses")

@admin_required
def reject_course(request: HttpRequest, course_id: int):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "课程不存在")
        return redirect("pending_courses")
    course.status = "rejected"
    course.save()
    messages.success(request, f"课程 \"{course.title}\" 已拒绝。")
    return redirect("pending_courses")
