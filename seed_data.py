"""
Seed script — run with: python manage.py shell < seed_data.py
OR: python seed_data.py (from project root with DJANGO_SETTINGS_MODULE set)
"""
import os, django, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova.settings')
django.setup()

from django.utils import timezone
from datetime import date, timedelta, time
from accounts.models import User
from core.models import (
    Group, StudentProfile, TeacherProfile,
    Subject, Grade, Attendance, Homework, Schedule, Notification
)

print("Seeding database...")

# ── Superuser / Admin ─────────────────────────────────
admin, _ = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@edunova.kz', 'first_name': 'Администратор', 'last_name': 'Системы',
    'role': 'admin', 'is_staff': True, 'is_superuser': True
})
admin.set_password('admin123')
admin.save()
print("  Admin: admin / admin123")

# ── Groups ────────────────────────────────────────────
g1, _ = Group.objects.get_or_create(name='ИТ-21', defaults={'course': 2})
g2, _ = Group.objects.get_or_create(name='ЭК-22', defaults={'course': 1})
g3, _ = Group.objects.get_or_create(name='МТ-20', defaults={'course': 3})
groups = [g1, g2, g3]
print("  Groups: ИТ-21, ЭК-22, МТ-20")

# ── Teachers ──────────────────────────────────────────
teachers_data = [
    ('teacher1', 'Алибек', 'Жумабеков', 'teacher1@edunova.kz', 'Математика и информатика'),
    ('teacher2', 'Гүлнар', 'Сейткалиева', 'teacher2@edunova.kz', 'Экономика и менеджмент'),
    ('teacher3', 'Сергей', 'Петров', 'teacher3@edunova.kz', 'Физика и математика'),
]
teacher_profiles = []
for uname, first, last, email, spec in teachers_data:
    u, _ = User.objects.get_or_create(username=uname, defaults={
        'email': email, 'first_name': first, 'last_name': last, 'role': 'teacher'
    })
    u.set_password('teacher123')
    u.save()
    tp, _ = TeacherProfile.objects.get_or_create(user=u, defaults={'specialization': spec})
    teacher_profiles.append(tp)
print(f"  Teachers: {', '.join(t[0] for t in teachers_data)} / teacher123")

# ── Subjects ──────────────────────────────────────────
subjects_data = [
    ('Математика', teacher_profiles[0], [g1, g3]),
    ('Информатика', teacher_profiles[0], [g1, g2]),
    ('Экономика', teacher_profiles[1], [g2, g3]),
    ('Физика', teacher_profiles[2], [g1, g3]),
    ('Менеджмент', teacher_profiles[1], [g2]),
    ('Алгоритмы и структуры данных', teacher_profiles[0], [g1]),
]
subject_objs = []
for title, teacher, grps in subjects_data:
    s, _ = Subject.objects.get_or_create(title=title, defaults={'teacher': teacher})
    s.teacher = teacher
    s.groups.set(grps)
    s.save()
    subject_objs.append(s)
print(f"  Subjects: {len(subject_objs)} created")

# ── Students ──────────────────────────────────────────
students_data = [
    ('student1', 'Айгерим', 'Касымова', 'student1@edunova.kz', g1),
    ('student2', 'Данияр', 'Нұрланов', 'student2@edunova.kz', g1),
    ('student3', 'Медина', 'Алиева',   'student3@edunova.kz', g1),
    ('student4', 'Арман',  'Бекенов',  'student4@edunova.kz', g2),
    ('student5', 'Зарина', 'Омарова',  'student5@edunova.kz', g2),
    ('student6', 'Руслан', 'Ибраев',   'student6@edunova.kz', g3),
    ('student7', 'Камила', 'Тоқанова', 'student7@edunova.kz', g3),
]
student_profiles = []
for uname, first, last, email, group in students_data:
    u, _ = User.objects.get_or_create(username=uname, defaults={
        'email': email, 'first_name': first, 'last_name': last, 'role': 'student'
    })
    u.set_password('student123')
    u.save()
    sp, _ = StudentProfile.objects.get_or_create(user=u, defaults={'group': group})
    sp.group = group
    sp.save()
    student_profiles.append(sp)
print(f"  Students: {', '.join(s[0] for s in students_data)} / student123")

# ── Grades ────────────────────────────────────────────
import random
random.seed(42)
Grade.objects.all().delete()
for sp in student_profiles:
    group_subjects = Subject.objects.filter(groups=sp.group)
    for subj in group_subjects:
        for _ in range(random.randint(3, 8)):
            grade_val = random.choices([5, 4, 3, 2], weights=[35, 40, 20, 5])[0]
            days_ago = random.randint(0, 90)
            Grade.objects.create(
                student=sp, subject=subj, value=grade_val,
                teacher=subj.teacher,
                comment=random.choice(['', 'Хорошая работа', 'Нужно больше стараться', ''])
            )
print("  Grades: generated")

# ── Attendance ────────────────────────────────────────
Attendance.objects.all().delete()
today = date.today()
for sp in student_profiles:
    group_subjects = Subject.objects.filter(groups=sp.group)
    for subj in group_subjects:
        for i in range(20):
            att_date = today - timedelta(days=i * 3)
            status = random.choices(
                ['present', 'absent', 'late', 'excused'],
                weights=[75, 15, 7, 3]
            )[0]
            try:
                Attendance.objects.get_or_create(
                    student=sp, subject=subj, date=att_date,
                    defaults={'status': status}
                )
            except Exception:
                pass
print("  Attendance: generated")

# ── Homework ──────────────────────────────────────────
Homework.objects.all().delete()
hw_data = [
    (subject_objs[0], teacher_profiles[0], 'Задание 1: Интегралы', 'Решить задачи 1-15 из раздела интегралы', 3),
    (subject_objs[1], teacher_profiles[0], 'Лабораторная №3', 'Разработать алгоритм сортировки на Python', 5),
    (subject_objs[2], teacher_profiles[1], 'Реферат: Инфляция', 'Написать реферат об инфляции (2000 слов)', 7),
    (subject_objs[3], teacher_profiles[2], 'Задачи по механике', 'Решить задачи 1-10 из раздела механика', 2),
    (subject_objs[4], teacher_profiles[1], 'Кейс-анализ', 'Провести анализ кейса компании Apple', 10),
]
for subj, teacher, title, desc, days_fwd in hw_data:
    Homework.objects.create(
        subject=subj, teacher=teacher, title=title, description=desc,
        deadline=timezone.now() + timedelta(days=days_fwd)
    )
print("  Homework: generated")

# ── Schedule ──────────────────────────────────────────
Schedule.objects.all().delete()
schedule_data = [
    (g1, subject_objs[0], teacher_profiles[0], 'monday',    time(8, 30),  time(10,  5), '201'),
    (g1, subject_objs[1], teacher_profiles[0], 'monday',    time(10, 15), time(11, 50), 'Компьютерный класс'),
    (g1, subject_objs[3], teacher_profiles[2], 'wednesday', time(8, 30),  time(10,  5), '305'),
    (g1, subject_objs[5], teacher_profiles[0], 'friday',    time(10, 15), time(11, 50), 'Компьютерный класс'),
    (g2, subject_objs[1], teacher_profiles[0], 'tuesday',   time(8, 30),  time(10,  5), 'Компьютерный класс'),
    (g2, subject_objs[2], teacher_profiles[1], 'tuesday',   time(10, 15), time(11, 50), '102'),
    (g2, subject_objs[4], teacher_profiles[1], 'thursday',  time(8, 30),  time(10,  5), '103'),
    (g3, subject_objs[0], teacher_profiles[0], 'monday',    time(12, 0),  time(13, 35), '201'),
    (g3, subject_objs[2], teacher_profiles[1], 'wednesday', time(10, 15), time(11, 50), '102'),
    (g3, subject_objs[3], teacher_profiles[2], 'friday',    time(8, 30),  time(10,  5), '305'),
]
for group, subj, teacher, day, ts, te, room in schedule_data:
    Schedule.objects.create(
        group=group, subject=subj, teacher=teacher,
        day=day, time_start=ts, time_end=te, room=room
    )
print("  Schedule: generated")

# ── Notifications ─────────────────────────────────────
Notification.objects.all().delete()
for sp in student_profiles[:4]:
    Notification.objects.create(
        user=sp.user, title='Добро пожаловать в EduNova!',
        message='Система успешно запущена. Ознакомьтесь с расписанием и заданиями.',
        type='system'
    )
    Notification.objects.create(
        user=sp.user, title='Новое домашнее задание',
        message='По предмету «Математика» добавлено новое задание.',
        type='homework'
    )
print("  Notifications: generated")

print("\n✅ Seed complete!")
print("\nАккаунты для входа:")
print("  admin    / admin123    — Администратор")
print("  teacher1 / teacher123  — Преподаватель")
print("  student1 / student123  — Студент")
