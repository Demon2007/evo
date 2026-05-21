from django.urls import path
from . import views

urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/students/', views.admin_students, name='admin_students'),
    path('admin-panel/students/add/', views.add_student, name='add_student'),
    path('admin-panel/students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('admin-panel/students/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('admin-panel/teachers/', views.admin_teachers, name='admin_teachers'),
    path('admin-panel/teachers/add/', views.add_teacher, name='add_teacher'),
    path('admin-panel/teachers/delete/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('admin-panel/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin-panel/subjects/add/', views.add_subject, name='add_subject'),
    path('admin-panel/subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),
    path('admin-panel/groups/', views.admin_groups, name='admin_groups'),
    path('admin-panel/groups/add/', views.add_group, name='add_group'),
    path('admin-panel/groups/delete/<int:pk>/', views.delete_group, name='delete_group'),
    path('admin-panel/schedule/', views.admin_schedule, name='admin_schedule'),
    path('admin-panel/schedule/add/', views.add_schedule, name='add_schedule'),
    path('admin-panel/schedule/delete/<int:pk>/', views.delete_schedule, name='delete_schedule'),
    path('admin-panel/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),

    # Teacher
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/grades/', views.teacher_grades, name='teacher_grades'),
    path('teacher/grades/add/', views.add_grade, name='add_grade'),
    path('teacher/grades/delete/<int:pk>/', views.delete_grade, name='delete_grade'),
    path('teacher/attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('teacher/attendance/save/', views.save_attendance, name='save_attendance'),
    path('teacher/homework/', views.teacher_homework, name='teacher_homework'),
    path('teacher/homework/add/', views.add_homework, name='add_homework'),
    path('teacher/homework/delete/<int:pk>/', views.delete_homework, name='delete_homework'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/groups/mark/', views.teacher_group_mark, name='teacher_group_mark'),
    path('teacher/subjects/<int:subject_id>/journal/', views.teacher_subject_journal, name='teacher_subject_journal'),

    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/homework/', views.student_homework, name='student_homework'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),
    path('notifications/read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
]
