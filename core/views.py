from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps
import json
import calendar
import datetime

from accounts.models import User
from .models import (
    Group, StudentProfile, TeacherProfile, Subject,
    Grade, Attendance, Homework, Schedule, Notification
)


# ─── Role decorators ────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, 'Доступ запрещён.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ─── Landing ─────────────────────────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher_dashboard')
        else:
            return redirect('student_dashboard')
    stats = {
        'students': StudentProfile.objects.count(),
        'teachers': TeacherProfile.objects.count(),
        'subjects': Subject.objects.count(),
        'groups': Group.objects.count(),
    }
    return render(request, 'landing.html', {'stats': stats})


# ─── Admin views ─────────────────────────────────────────────────────────────

@role_required('admin')
def admin_dashboard(request):
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_subjects = Subject.objects.count()
    total_groups = Group.objects.count()
    recent_grades = Grade.objects.select_related('student__user', 'subject').order_by('-date')[:10]
    recent_students = StudentProfile.objects.select_related('user', 'group').order_by('-user__date_joined')[:5]
    avg_grade = Grade.objects.aggregate(avg=Avg('value'))['avg'] or 0
    present_count = Attendance.objects.filter(status='present').count()
    total_att = Attendance.objects.count()
    att_percent = round(present_count / total_att * 100, 1) if total_att else 0
    grade_dist = {i: Grade.objects.filter(value=i).count() for i in range(1, 6)}
    groups_data = Group.objects.annotate(cnt=Count('studentprofile')).values('name', 'cnt')
    context = {
        'total_students': total_students, 'total_teachers': total_teachers,
        'total_subjects': total_subjects, 'total_groups': total_groups,
        'recent_grades': recent_grades, 'recent_students': recent_students,
        'avg_grade': round(avg_grade, 2), 'att_percent': att_percent,
        'grade_dist': json.dumps(grade_dist),
        'groups_data': json.dumps(list(groups_data)),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@role_required('admin')
def admin_students(request):
    q = request.GET.get('q', '')
    group_id = request.GET.get('group', '')
    students = StudentProfile.objects.select_related('user', 'group').order_by('user__last_name')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q) | Q(user__email__icontains=q)
        )
    if group_id:
        students = students.filter(group_id=group_id)
    paginator = Paginator(students, 15)
    page = paginator.get_page(request.GET.get('page'))
    groups = Group.objects.all()
    return render(request, 'admin_panel/students.html', {
        'page_obj': page, 'groups': groups, 'q': q, 'selected_group': group_id
    })


@role_required('admin')
def admin_teachers(request):
    q = request.GET.get('q', '')
    teachers = TeacherProfile.objects.select_related('user').order_by('user__last_name')
    if q:
        teachers = teachers.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
            Q(specialization__icontains=q)
        )
    paginator = Paginator(teachers, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/teachers.html', {'page_obj': page, 'q': q})


@role_required('admin')
def admin_subjects(request):
    q = request.GET.get('q', '')
    subjects = Subject.objects.select_related('teacher__user').prefetch_related('groups').order_by('title')
    if q:
        subjects = subjects.filter(Q(title__icontains=q))
    paginator = Paginator(subjects, 15)
    page = paginator.get_page(request.GET.get('page'))
    teachers = TeacherProfile.objects.select_related('user').all()
    groups = Group.objects.all()
    return render(request, 'admin_panel/subjects.html', {
        'page_obj': page, 'q': q, 'teachers': teachers, 'groups': groups
    })


@role_required('admin')
def admin_groups(request):
    groups = Group.objects.annotate(student_count=Count('studentprofile')).order_by('course', 'name')
    return render(request, 'admin_panel/groups.html', {'groups': groups})


@role_required('admin')
def admin_schedule(request):
    groups = Group.objects.all()
    selected_group_id = request.GET.get('group', '')
    schedule = Schedule.objects.select_related('group', 'subject', 'teacher__user').order_by('day', 'time_start')
    if selected_group_id:
        schedule = schedule.filter(group_id=selected_group_id)
    subjects = Subject.objects.all()
    teachers = TeacherProfile.objects.select_related('user').all()
    days = Schedule.DAY_CHOICES
    return render(request, 'admin_panel/schedule.html', {
        'schedule': schedule, 'groups': groups, 'subjects': subjects,
        'teachers': teachers, 'days': days, 'selected_group': selected_group_id
    })


@role_required('admin')
def admin_analytics(request):
    grade_dist = {str(i): Grade.objects.filter(value=i).count() for i in range(1, 6)}
    att_stats = {
        s: Attendance.objects.filter(status=s).count()
        for s in ['present', 'absent', 'late', 'excused']
    }
    top_students = StudentProfile.objects.annotate(
        avg=Avg('grades__value')
    ).filter(avg__isnull=False).order_by('-avg')[:10]
    groups_avg = Group.objects.annotate(
        avg=Avg('studentprofile__grades__value')
    ).filter(avg__isnull=False).values('name', 'avg').order_by('-avg')
    return render(request, 'admin_panel/analytics.html', {
        'grade_dist': json.dumps(grade_dist),
        'att_stats': json.dumps(att_stats),
        'top_students': top_students,
        'groups_avg': json.dumps(list(groups_avg)),
    })


@role_required('admin')
def admin_settings(request):
    return render(request, 'admin_panel/settings.html')


# ─── Admin CRUD APIs ──────────────────────────────────────────────────────────

@role_required('admin')
def add_student(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password', 'edunova123')
            group_id = request.POST.get('group')

            user = User.objects.create_user(
                username=username, first_name=first_name,
                last_name=last_name, email=email,
                password=password, role='student'
            )
            group = Group.objects.get(id=group_id) if group_id else None
            StudentProfile.objects.create(user=user, group=group)
            messages.success(request, f'Студент {first_name} {last_name} добавлен.')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return redirect('admin_students')


@role_required('admin')
def delete_student(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    name = student.user.get_full_name_or_username()
    student.user.delete()
    messages.success(request, f'Студент {name} удалён.')
    return redirect('admin_students')


@role_required('admin')
def edit_student(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        student.user.first_name = request.POST.get('first_name', student.user.first_name)
        student.user.last_name = request.POST.get('last_name', student.user.last_name)
        student.user.email = request.POST.get('email', student.user.email)
        student.user.save()
        group_id = request.POST.get('group')
        student.group = Group.objects.get(id=group_id) if group_id else None
        student.save()
        messages.success(request, 'Данные студента обновлены.')
    return redirect('admin_students')


@role_required('admin')
def add_teacher(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password', 'edunova123')
            specialization = request.POST.get('specialization', '')
            user = User.objects.create_user(
                username=username, first_name=first_name,
                last_name=last_name, email=email,
                password=password, role='teacher'
            )
            TeacherProfile.objects.create(user=user, specialization=specialization)
            messages.success(request, f'Преподаватель {first_name} {last_name} добавлен.')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return redirect('admin_teachers')


@role_required('admin')
def delete_teacher(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    name = teacher.user.get_full_name_or_username()
    teacher.user.delete()
    messages.success(request, f'Преподаватель {name} удалён.')
    return redirect('admin_teachers')


@role_required('admin')
def add_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        course = request.POST.get('course', 1)
        Group.objects.create(name=name, course=course)
        messages.success(request, f'Группа {name} добавлена.')
    return redirect('admin_groups')


@role_required('admin')
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    name = group.name
    group.delete()
    messages.success(request, f'Группа {name} удалена.')
    return redirect('admin_groups')


@role_required('admin')
def add_subject(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        teacher_id = request.POST.get('teacher')
        description = request.POST.get('description', '')
        teacher = TeacherProfile.objects.get(id=teacher_id) if teacher_id else None
        subject = Subject.objects.create(title=title, teacher=teacher, description=description)
        group_ids = request.POST.getlist('groups')
        if group_ids:
            subject.groups.set(Group.objects.filter(id__in=group_ids))
        messages.success(request, f'Предмет {title} добавлен.')
    return redirect('admin_subjects')


@role_required('admin')
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    title = subject.title
    subject.delete()
    messages.success(request, f'Предмет {title} удалён.')
    return redirect('admin_subjects')


@role_required('admin')
def add_schedule(request):
    if request.method == 'POST':
        try:
            group = get_object_or_404(Group, id=request.POST.get('group'))
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            teacher_id = request.POST.get('teacher')
            teacher = TeacherProfile.objects.get(id=teacher_id) if teacher_id else None
            Schedule.objects.create(
                group=group, subject=subject, teacher=teacher,
                day=request.POST.get('day'),
                time_start=request.POST.get('time_start'),
                time_end=request.POST.get('time_end'),
                room=request.POST.get('room', '')
            )
            messages.success(request, 'Расписание добавлено.')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return redirect('admin_schedule')


@role_required('admin')
def delete_schedule(request, pk):
    entry = get_object_or_404(Schedule, pk=pk)
    entry.delete()
    messages.success(request, 'Запись расписания удалена.')
    return redirect('admin_schedule')


# ─── Teacher views ────────────────────────────────────────────────────────────

def get_teacher_profile(user):
    try:
        return user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return None


@role_required('teacher')
def teacher_dashboard(request):
    teacher = get_teacher_profile(request.user)
    if not teacher:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('login')
    subjects = Subject.objects.filter(teacher=teacher)
    total_students = StudentProfile.objects.filter(group__subjects__teacher=teacher).distinct().count()
    recent_grades = Grade.objects.filter(teacher=teacher).select_related(
        'student__user', 'subject'
    ).order_by('-date')[:8]
    pending_hw = Homework.objects.filter(teacher=teacher, deadline__gte=timezone.now()).count()
    today = timezone.now().date()
    today_schedule = Schedule.objects.filter(
        teacher=teacher,
        day=today.strftime('%A').lower()
    ).select_related('group', 'subject').order_by('time_start')
    avg_grade = Grade.objects.filter(teacher=teacher).aggregate(avg=Avg('value'))['avg'] or 0
    context = {
        'teacher': teacher, 'subjects': subjects,
        'total_students': total_students, 'recent_grades': recent_grades,
        'pending_hw': pending_hw, 'today_schedule': today_schedule,
        'avg_grade': round(avg_grade, 2),
    }
    return render(request, 'teacher/dashboard.html', context)


@role_required('teacher')
def teacher_subjects(request):
    teacher = get_teacher_profile(request.user)
    subjects = Subject.objects.filter(teacher=teacher).prefetch_related('groups')
    return render(request, 'teacher/subjects.html', {'subjects': subjects, 'teacher': teacher})


@role_required('teacher')
def teacher_students(request):
    teacher = get_teacher_profile(request.user)
    subject_id = request.GET.get('subject', '')
    students = StudentProfile.objects.filter(
        group__subjects__teacher=teacher
    ).distinct().select_related('user', 'group')
    subjects = Subject.objects.filter(teacher=teacher)
    if subject_id:
        students = StudentProfile.objects.filter(
            group__subjects__id=subject_id
        ).distinct().select_related('user', 'group')
    q = request.GET.get('q', '')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
        )
    return render(request, 'teacher/students.html', {
        'students': students, 'subjects': subjects,
        'selected_subject': subject_id, 'q': q, 'teacher': teacher
    })


@role_required('teacher')
def teacher_grades(request):
    teacher = get_teacher_profile(request.user)
    subject_id = request.GET.get('subject', '')
    subjects = Subject.objects.filter(teacher=teacher)
    grades = Grade.objects.filter(teacher=teacher).select_related(
        'student__user', 'student__group', 'subject'
    ).order_by('-date')
    if subject_id:
        grades = grades.filter(subject_id=subject_id)
    students = StudentProfile.objects.filter(
        group__subjects__teacher=teacher
    ).distinct().select_related('user', 'group')
    paginator = Paginator(grades, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'teacher/grades.html', {
        'page_obj': page, 'subjects': subjects, 'students': students,
        'selected_subject': subject_id, 'teacher': teacher
    })


@role_required('teacher')
def add_grade(request):
    if request.method == 'POST':
        teacher = get_teacher_profile(request.user)
        try:
            student = get_object_or_404(StudentProfile, id=request.POST.get('student'))
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            value = int(request.POST.get('value', 5))
            comment = request.POST.get('comment', '')
            grade = Grade.objects.create(
                student=student, subject=subject,
                value=value, comment=comment, teacher=teacher
            )
            Notification.objects.create(
                user=student.user,
                title='Новая оценка',
                message=f'По предмету "{subject.title}" выставлена оценка {value}.',
                type='grade'
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': grade.id, 'value': value})
            messages.success(request, f'Оценка {value} выставлена.')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Ошибка: {e}')
    return redirect('teacher_grades')


@role_required('teacher')
def delete_grade(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    grade.delete()
    messages.success(request, 'Оценка удалена.')
    return redirect('teacher_grades')


@role_required('teacher')
def teacher_attendance(request):
    teacher = get_teacher_profile(request.user)
    subject_id = request.GET.get('subject', '')
    date_str = request.GET.get('date', str(timezone.now().date()))
    subjects = Subject.objects.filter(teacher=teacher)
    selected_subject = None
    students = []
    attendance_map = {}
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id)
        students = StudentProfile.objects.filter(
            group__subjects=selected_subject
        ).distinct().select_related('user')
        att_records = Attendance.objects.filter(subject=selected_subject, date=date_str)
        attendance_map = {a.student_id: a.status for a in att_records}
    return render(request, 'teacher/attendance.html', {
        'subjects': subjects, 'selected_subject': selected_subject,
        'students': students, 'attendance_map': attendance_map,
        'date': date_str, 'teacher': teacher
    })


@role_required('teacher')
def save_attendance(request):
    if request.method == 'POST':
        teacher = get_teacher_profile(request.user)
        subject_id = request.POST.get('subject')
        date_str = request.POST.get('date')
        subject = get_object_or_404(Subject, id=subject_id)
        students = StudentProfile.objects.filter(group__subjects=subject).distinct()
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
            Attendance.objects.update_or_create(
                student=student, subject=subject, date=date_str,
                defaults={'status': status}
            )
        messages.success(request, 'Посещаемость сохранена.')
    return redirect('teacher_attendance')


@role_required('teacher')
def teacher_homework(request):
    teacher = get_teacher_profile(request.user)
    subject_id = request.GET.get('subject', '')
    subjects = Subject.objects.filter(teacher=teacher)
    homework = Homework.objects.filter(teacher=teacher).select_related('subject').order_by('deadline')
    if subject_id:
        homework = homework.filter(subject_id=subject_id)
    return render(request, 'teacher/homework.html', {
        'homework': homework, 'subjects': subjects,
        'selected_subject': subject_id, 'teacher': teacher,
        'now': timezone.now()
    })


@role_required('teacher')
def add_homework(request):
    if request.method == 'POST':
        teacher = get_teacher_profile(request.user)
        try:
            subject = get_object_or_404(Subject, id=request.POST.get('subject'))
            hw = Homework.objects.create(
                subject=subject, teacher=teacher,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                deadline=request.POST.get('deadline')
            )
            for student in StudentProfile.objects.filter(group__subjects=subject).distinct():
                Notification.objects.create(
                    user=student.user,
                    title='Новое домашнее задание',
                    message=f'По предмету "{subject.title}": {hw.title}',
                    type='homework'
                )
            messages.success(request, 'Домашнее задание добавлено.')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return redirect('teacher_homework')


@role_required('teacher')
def delete_homework(request, pk):
    hw = get_object_or_404(Homework, pk=pk)
    hw.delete()
    messages.success(request, 'Задание удалено.')
    return redirect('teacher_homework')


@role_required('teacher')
def teacher_schedule(request):
    teacher = get_teacher_profile(request.user)
    schedule = Schedule.objects.filter(teacher=teacher).select_related(
        'group', 'subject'
    ).order_by('day', 'time_start')
    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    schedule_by_day = {}
    for day_key, day_label in Schedule.DAY_CHOICES:
        day_entries = [s for s in schedule if s.day == day_key]
        if day_entries:
            schedule_by_day[day_label] = day_entries
    return render(request, 'teacher/schedule.html', {
        'schedule_by_day': schedule_by_day, 'teacher': teacher
    })


@role_required('teacher')
def teacher_groups(request):
    teacher = get_teacher_profile(request.user)
    subjects = Subject.objects.filter(teacher=teacher).prefetch_related('groups')
    groups = Group.objects.filter(subjects__teacher=teacher).distinct().order_by('course', 'name')
    selected_group_id = request.GET.get('group', '')
    selected_group = None
    students = []
    subjects_for_group = []
    if selected_group_id:
        selected_group = get_object_or_404(Group, id=selected_group_id)
        students = StudentProfile.objects.filter(
            group=selected_group
        ).select_related('user').order_by('user__last_name')
        subjects_for_group = Subject.objects.filter(
            teacher=teacher, groups=selected_group
        )
    return render(request, 'teacher/groups.html', {
        'teacher': teacher,
        'groups': groups,
        'selected_group': selected_group,
        'students': students,
        'subjects_for_group': subjects_for_group,
        'today': str(timezone.now().date()),
    })


@role_required('teacher')
def teacher_group_mark(request):
    """AJAX endpoint: mark attendance + grade for a student in one call."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    teacher = get_teacher_profile(request.user)
    data = json.loads(request.body)
    action = data.get('action')

    if action == 'grade':
        student = get_object_or_404(StudentProfile, id=data['student_id'])
        subject = get_object_or_404(Subject, id=data['subject_id'], teacher=teacher)
        value = int(data.get('value', 5))
        comment = data.get('comment', '')
        grade = Grade.objects.create(
            student=student, subject=subject,
            value=value, comment=comment, teacher=teacher
        )
        Notification.objects.create(
            user=student.user,
            title='Новая оценка',
            message=f'По предмету «{subject.title}» выставлена оценка {value}.',
            type='grade'
        )
        avg = Grade.objects.filter(student=student, subject=subject).aggregate(a=Avg('value'))['a'] or 0
        return JsonResponse({'success': True, 'grade_id': grade.id, 'value': value, 'avg': round(avg, 1)})

    elif action == 'del_grade':
        grade = get_object_or_404(Grade, id=data['grade_id'])
        student = grade.student
        subject = grade.subject
        grade.delete()
        avg = Grade.objects.filter(student=student, subject=subject).aggregate(a=Avg('value'))['a'] or 0
        return JsonResponse({'success': True, 'avg': round(avg, 1)})

    elif action == 'attendance':
        student = get_object_or_404(StudentProfile, id=data['student_id'])
        subject = get_object_or_404(Subject, id=data['subject_id'], teacher=teacher)
        att_date = data.get('date', str(timezone.now().date()))
        status = data.get('status', 'present')
        if status == 'clear':
            Attendance.objects.filter(student=student, subject=subject, date=att_date).delete()
            return JsonResponse({'success': True, 'status': None})
        att, _ = Attendance.objects.update_or_create(
            student=student, subject=subject, date=att_date,
            defaults={'status': status}
        )
        return JsonResponse({'success': True, 'status': status})

    return JsonResponse({'error': 'Unknown action'}, status=400)


@role_required('teacher')
def teacher_subject_journal(request, subject_id):
    teacher = get_teacher_profile(request.user)
    subject = get_object_or_404(Subject, id=subject_id, teacher=teacher)
    groups = subject.groups.all().order_by('course', 'name')

    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    # Clamp to valid month
    if month < 1:  month = 12; year -= 1
    if month > 12: month = 1;  year += 1

    _, last_day = calendar.monthrange(year, month)
    month_start = datetime.date(year, month, 1)
    month_end   = datetime.date(year, month, last_day)
    dates = [datetime.date(year, month, d) for d in range(1, last_day + 1)
             if datetime.date(year, month, d) <= today]

    # Selected group
    group_id = request.GET.get('group', '')
    selected_group = None
    if group_id:
        selected_group = groups.filter(id=group_id).first()
    if not selected_group and groups.exists():
        selected_group = groups.first()

    students = []
    journal_data = {}

    if selected_group:
        students = list(StudentProfile.objects.filter(
            group=selected_group
        ).select_related('user').order_by('user__last_name', 'user__first_name'))

        grades = Grade.objects.filter(
            subject=subject,
            student__group=selected_group,
            date__gte=month_start,
            date__lte=month_end,
        ).order_by('date', 'id').select_related('student')

        att_records = Attendance.objects.filter(
            subject=subject,
            student__group=selected_group,
            date__gte=month_start,
            date__lte=month_end,
        ).select_related('student')

        for st in students:
            journal_data[st.id] = {}

        for g in grades:
            d = str(g.date)
            sid = g.student_id
            if sid not in journal_data:
                journal_data[sid] = {}
            if d not in journal_data[sid]:
                journal_data[sid][d] = {'grades': [], 'att': None}
            journal_data[sid][d]['grades'].append({'id': g.id, 'value': g.value})

        for a in att_records:
            d = str(a.date)
            sid = a.student_id
            if sid not in journal_data:
                journal_data[sid] = {}
            if d not in journal_data[sid]:
                journal_data[sid][d] = {'grades': [], 'att': None}
            journal_data[sid][d]['att'] = a.status

    # Prev / next month
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    month_names = ['','Январь','Февраль','Март','Апрель','Май','Июнь',
                   'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

    return render(request, 'teacher/journal.html', {
        'teacher': teacher,
        'subject': subject,
        'groups': groups,
        'selected_group': selected_group,
        'dates': dates,
        'students': students,
        'journal_data': json.dumps(journal_data),
        'today': str(today),
        'month': month,
        'year': year,
        'month_name': month_names[month],
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
    })


# ─── Student views ────────────────────────────────────────────────────────────

def get_student_profile(user):
    try:
        return user.student_profile
    except StudentProfile.DoesNotExist:
        return None


@role_required('student')
def student_dashboard(request):
    student = get_student_profile(request.user)
    if not student:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('login')
    recent_grades = Grade.objects.filter(student=student).select_related(
        'subject', 'teacher__user'
    ).order_by('-date')[:6]
    avg_grade = student.average_grade()
    att_percent = student.attendance_percent()
    upcoming_hw = Homework.objects.filter(
        subject__groups=student.group,
        deadline__gte=timezone.now()
    ).order_by('deadline')[:5] if student.group else []
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    today = timezone.now().date()
    today_schedule = []
    if student.group:
        today_schedule = Schedule.objects.filter(
            group=student.group,
            day=today.strftime('%A').lower()
        ).select_related('subject', 'teacher__user').order_by('time_start')
    grade_by_subject = {}
    if student.group:
        for subj in student.group.subjects.all():
            subj_grades = Grade.objects.filter(student=student, subject=subj)
            if subj_grades.exists():
                grade_by_subject[subj.title] = round(
                    subj_grades.aggregate(avg=Avg('value'))['avg'] or 0, 1
                )
    context = {
        'student': student, 'recent_grades': recent_grades,
        'avg_grade': avg_grade, 'att_percent': att_percent,
        'upcoming_hw': upcoming_hw, 'notifications': notifications,
        'unread_count': unread_count, 'today_schedule': today_schedule,
        'grade_by_subject': json.dumps(grade_by_subject),
    }
    return render(request, 'student/dashboard.html', context)


@role_required('student')
def student_grades(request):
    student = get_student_profile(request.user)
    subject_id = request.GET.get('subject', '')
    grades = Grade.objects.filter(student=student).select_related(
        'subject', 'teacher__user'
    ).order_by('-date')
    subjects = []
    if student.group:
        subjects = student.group.subjects.all()
    if subject_id:
        grades = grades.filter(subject_id=subject_id)
    avg = grades.aggregate(avg=Avg('value'))['avg'] or 0
    grade_by_subject = {}
    for subj in subjects:
        subj_grades = Grade.objects.filter(student=student, subject=subj)
        if subj_grades.exists():
            grade_by_subject[subj.title] = round(
                subj_grades.aggregate(avg=Avg('value'))['avg'] or 0, 1
            )
    paginator = Paginator(grades, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'student/grades.html', {
        'page_obj': page, 'subjects': subjects,
        'selected_subject': subject_id, 'avg': round(avg, 2),
        'grade_by_subject': json.dumps(grade_by_subject), 'student': student
    })


@role_required('student')
def student_attendance(request):
    student = get_student_profile(request.user)
    subject_id = request.GET.get('subject', '')
    att = Attendance.objects.filter(student=student).select_related('subject').order_by('-date')
    subjects = []
    if student.group:
        subjects = student.group.subjects.all()
    if subject_id:
        att = att.filter(subject_id=subject_id)
    total = att.count()
    present = att.filter(status='present').count()
    percent = round(present / total * 100, 1) if total else 0
    paginator = Paginator(att, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'student/attendance.html', {
        'page_obj': page, 'subjects': subjects,
        'selected_subject': subject_id, 'total': total,
        'present': present, 'percent': percent, 'student': student
    })


@role_required('student')
def student_homework(request):
    student = get_student_profile(request.user)
    subject_id = request.GET.get('subject', '')
    now = timezone.now()
    subjects = []
    homework = []
    if student.group:
        subjects = student.group.subjects.all()
        homework = Homework.objects.filter(
            subject__groups=student.group
        ).select_related('subject').order_by('deadline')
        if subject_id:
            homework = homework.filter(subject_id=subject_id)
    return render(request, 'student/homework.html', {
        'homework': homework, 'subjects': subjects,
        'selected_subject': subject_id, 'now': now, 'student': student
    })


@role_required('student')
def student_schedule(request):
    student = get_student_profile(request.user)
    schedule = []
    schedule_by_day = {}
    if student and student.group:
        schedule = Schedule.objects.filter(
            group=student.group
        ).select_related('subject', 'teacher__user').order_by('day', 'time_start')
        for day_key, day_label in Schedule.DAY_CHOICES:
            day_entries = [s for s in schedule if s.day == day_key]
            schedule_by_day[day_label] = day_entries
    return render(request, 'student/schedule.html', {
        'schedule_by_day': schedule_by_day, 'student': student
    })


@role_required('student')
def student_notifications(request):
    student = get_student_profile(request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
        messages.success(request, 'Все уведомления отмечены как прочитанные.')
        return redirect('student_notifications')
    paginator = Paginator(notifications, 20)
    page = paginator.get_page(request.GET.get('page'))
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, 'student/notifications.html', {
        'page_obj': page, 'unread_count': unread_count, 'student': student
    })


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'success': True})


# ─── Error handlers ───────────────────────────────────────────────────────────

def error_404(request, exception):
    return render(request, '404.html', status=404)
