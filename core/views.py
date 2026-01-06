from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpRequest
from django.db.models import Avg, Count, Q
from .models import Course, Rating, School, Tag
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from .models import Comment, Favorite, RatingReaction, CourseInstructor, Instructor, CourseTag, Report, UserDisclaimer

from django.contrib.auth import get_user_model
import random

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
    return render(request, "index.html", {"top_courses": top_courses})

def rankings(request: HttpRequest):
    school_id = request.GET.get("school_id")
    category_id = request.GET.get("category_id")

    # base course set
    course_qs = Course.objects.filter(status="approved")
    if school_id:
        course_qs = course_qs.filter(school_id=school_id)
    if category_id:
        course_qs = course_qs.filter(category_id=category_id)

    # course dimension rankings
    course_stats = []
    for c in course_qs:
        rs = Rating.objects.filter(course=c)
        if rs.exists():
            course_stats.append({
                "course": c,
                "avg_overall": rs.aggregate(a=Avg("overall_score"))['a'] or 0,
                "avg_difficulty": rs.aggregate(a=Avg("difficulty"))['a'] or 0,
                "avg_usefulness": rs.aggregate(a=Avg("usefulness"))['a'] or 0,
                "avg_workload": rs.aggregate(a=Avg("workload"))['a'] or 0,
                "rating_count": rs.count(),
            })

    top_overall = sorted(course_stats, key=lambda x: (-(x["avg_overall"] or 0), -x["rating_count"]),)[:10]
    top_easiest = sorted(course_stats, key=lambda x: (x["avg_difficulty"] or 0, -x["rating_count"]),)[:10]
    top_useful = sorted(course_stats, key=lambda x: (-(x["avg_usefulness"] or 0), -x["rating_count"]),)[:10]
    top_low_workload = sorted(course_stats, key=lambda x: (x["avg_workload"] or 0, -x["rating_count"]),)[:10]

    # instructor popularity (avg overall and count)
    instr_qs = Instructor.objects.filter(courseinstructor__course__in=course_qs).distinct()
    instructor_stats = []
    for ins in instr_qs:
        rqs = Rating.objects.filter(instructor=ins, course__in=course_qs)
        if rqs.exists():
            instructor_stats.append({
                "instructor": ins,
                "avg_overall": rqs.aggregate(a=Avg("overall_score"))['a'] or 0,
                "rating_count": rqs.count(),
            })
    top_instructors = sorted(instructor_stats, key=lambda x: (-(x["avg_overall"] or 0), -x["rating_count"]),)[:10]

    # user helpfulness rankings based on reactions to their ratings
    from django.contrib.auth import get_user_model
    User = get_user_model()
    author_ids = list(Rating.objects.filter(course__in=course_qs).values_list("user_id", flat=True).distinct())
    authors = User.objects.filter(id__in=author_ids)
    user_stats = []
    for u in authors:
        helpful = RatingReaction.objects.filter(reaction_type="helpful", rating__user_id=u.id, rating__course__in=course_qs).count()
        not_helpful = RatingReaction.objects.filter(reaction_type="not_helpful", rating__user_id=u.id, rating__course__in=course_qs).count()
        user_stats.append({
            "user": u,
            "helpful": helpful,
            "not_helpful": not_helpful,
            "net": helpful - not_helpful,
        })
    top_helpful_users = sorted(user_stats, key=lambda x: (-(x["helpful"] or 0), -x["net"]),)[:10]
    top_net_helpful_users = sorted(user_stats, key=lambda x: (-(x["net"] or 0), -x["helpful"]),)[:10]

    schools = School.objects.order_by("name")
    from .models import Category
    categories = Category.objects.order_by("name")

    return render(
        request,
        "rankings.html",
        {
            "schools": schools,
            "categories": categories,
            "school_id": int(school_id) if school_id else None,
            "category_id": int(category_id) if category_id else None,
            "top_overall": top_overall,
            "top_easiest": top_easiest,
            "top_useful": top_useful,
            "top_low_workload": top_low_workload,
            "top_instructors": top_instructors,
            "top_helpful_users": top_helpful_users,
            "top_net_helpful_users": top_net_helpful_users,
        },
    )

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

def random_course_comment(request: HttpRequest, course_id: int):
    try:
        Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return JsonResponse({"text": None}, status=404)
    exclude_kind = request.GET.get("exclude_kind")
    exclude_id_raw = request.GET.get("exclude_id")
    try:
        exclude_id = int(exclude_id_raw) if exclude_id_raw is not None else None
    except Exception:
        exclude_id = None

    ratings_qs = Rating.objects.filter(course_id=course_id).exclude(comment_text__isnull=True).exclude(comment_text__exact="")
    comments_qs = Comment.objects.filter(rating__course_id=course_id).exclude(text__isnull=True).exclude(text__exact="")

    if exclude_kind == "rating" and exclude_id:
        ratings_qs = ratings_qs.exclude(rating_id=exclude_id)
    if exclude_kind == "comment" and exclude_id:
        comments_qs = comments_qs.exclude(comment_id=exclude_id)
    count_r = ratings_qs.count()
    count_c = comments_qs.count()
    if count_r + count_c == 0:
        return JsonResponse({"text": None})
    pick = random.randint(1, count_r + count_c)
    if pick <= count_r:
        r = ratings_qs.order_by("?").first()
        username = None
        try:
            username = ("匿名" if getattr(r, "anonymous_flag", False) else r.user.username)
        except Exception:
            username = None
        return JsonResponse({
            "text": r.comment_text,
            "user": username,
            "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
            "kind": "rating",
            "id": r.rating_id,
        })
    else:
        c = comments_qs.order_by("?").first()
        username = None
        try:
            username = c.user.username
        except Exception:
            username = None
        return JsonResponse({
            "text": c.text,
            "user": username,
            "created_at": c.created_at.isoformat() if getattr(c, "created_at", None) else None,
            "kind": "comment",
            "id": c.comment_id,
        })

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
    rating_ids = [r.rating_id for r in ratings]
    comment_qs = Comment.objects.filter(rating_id__in=rating_ids).order_by("created_at")
    nodes = {}
    roots_by_rating = {}
    for c in comment_qs:
        setattr(c, "children", [])
        nodes[c.comment_id] = c
        roots_by_rating.setdefault(c.rating_id, [])
    for c in comment_qs:
        if c.parent_comment_id:
            parent = nodes.get(c.parent_comment_id)
            if parent is not None:
                parent.children.append(c)
            else:
                roots_by_rating.setdefault(c.rating_id, []).append(c)
        else:
            roots_by_rating.setdefault(c.rating_id, []).append(c)
    for r in ratings:
        setattr(r, "comments", roots_by_rating.get(r.rating_id, []))
    if ratings.exists():
        avg_overall = ratings.aggregate(a=Avg("overall_score"))["a"] or 0
        avg_difficulty = ratings.aggregate(a=Avg("difficulty"))["a"] or 0
        avg_usefulness = ratings.aggregate(a=Avg("usefulness"))["a"] or 0
        avg_workload = ratings.aggregate(a=Avg("workload"))["a"] or 0
    else:
        avg_overall = avg_difficulty = avg_usefulness = avg_workload = 0

    instructors = list(Instructor.objects.filter(courseinstructor__course_id=course_id))
    course_tags = Tag.objects.filter(coursetag__course_id=course_id)
    available_tags = Tag.objects.order_by("name")[:100]

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user_id=request.user.id, course_id=course_id).exists()

    # per-instructor aggregates
    instructor_stats = []
    for ins in instructors:
        rqs = Rating.objects.filter(course_id=course_id, instructor_id=ins.instructor_id)
        if rqs.exists():
            avg_ins = rqs.aggregate(a=Avg("overall_score"))['a'] or 0
            cnt_ins = rqs.count()
        else:
            avg_ins = 0
            cnt_ins = 0
        instructor_stats.append({
            'instructor': ins,
            'avg_overall': avg_ins,
            'rating_count': cnt_ins,
        })

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
            "instructor_stats": instructor_stats,
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
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next") or "index"
            if not UserDisclaimer.objects.filter(user_id=user.id).exists():
                return redirect(f"{reverse('disclaimer')}?next={next_url}")
            return redirect(next_url)
        messages.success(request, "注册成功")
        return redirect("index")
    return render(request, "register.html")

def login_view(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if not UserDisclaimer.objects.filter(user_id=user.id).exists():
                go = next_url or "index"
                return redirect(f"{reverse('disclaimer')}?next={go}")
            return redirect(next_url or "index")
        messages.error(request, "用户名或密码错误")
    return render(request, "login.html")

def logout_view(request: HttpRequest):
    logout(request)
    return redirect("index")

@login_required
def disclaimer(request: HttpRequest):
    next_url = request.GET.get("next") or "index"
    if UserDisclaimer.objects.filter(user_id=request.user.id).exists():
        return redirect(next_url)
    if request.method == "POST":
        if request.POST.get("accept") == "yes":
            UserDisclaimer.objects.create(user_id=request.user.id, accepted_at=timezone.now())
            return redirect(next_url)
        messages.error(request, "请阅读并接受免责声明以继续使用平台")
    return render(request, "disclaimer.html", {"next": next_url})
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

    # optional instructor selection, only allow instructors assigned to this course
    sel_ins_id = request.POST.get("instructor_id")
    if sel_ins_id:
        try:
            ci_exists = CourseInstructor.objects.filter(course_id=course_id, instructor_id=int(sel_ins_id)).exists()
            if not ci_exists:
                sel_ins_id = None
        except Exception:
            sel_ins_id = None

    r = Rating(
        user_id=request.user.id,
        course_id=course_id,
        instructor_id=int(sel_ins_id) if sel_ins_id else None,
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
