from django.contrib import admin
from .models import Group, StudentProfile, TeacherProfile, Subject, Grade, Attendance, Homework, Schedule, Notification

admin.site.register(Group)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(Subject)
admin.site.register(Grade)
admin.site.register(Attendance)
admin.site.register(Homework)
admin.site.register(Schedule)
admin.site.register(Notification)
