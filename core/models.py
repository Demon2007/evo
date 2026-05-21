from django.db import models
from django.conf import settings


class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название группы')
    course = models.PositiveIntegerField(verbose_name='Курс')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.course} курс)"

    def student_count(self):
        return self.studentprofile_set.count()

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['course', 'name']


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_profile', verbose_name='Пользователь'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Группа'
    )
    phone = models.CharField(max_length=20, blank=True)
    enrollment_year = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name_or_username()} - {self.group}"

    def average_grade(self):
        grades = Grade.objects.filter(student=self)
        if grades.exists():
            return round(sum(g.value for g in grades) / grades.count(), 2)
        return 0

    def attendance_percent(self):
        total = Attendance.objects.filter(student=self).count()
        if total == 0:
            return 0
        present = Attendance.objects.filter(student=self, status='present').count()
        return round(present / total * 100, 1)

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='teacher_profile', verbose_name='Пользователь'
    )
    specialization = models.CharField(max_length=200, blank=True, verbose_name='Специализация')

    def __str__(self):
        return f"{self.user.get_full_name_or_username()} - {self.specialization}"

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'


class Subject(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название предмета')
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subjects', verbose_name='Преподаватель'
    )
    groups = models.ManyToManyField(Group, blank=True, related_name='subjects', verbose_name='Группы')
    description = models.TextField(blank=True, verbose_name='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['title']


class Grade(models.Model):
    GRADE_CHOICES = [(i, str(i)) for i in range(1, 6)]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    value = models.PositiveIntegerField(choices=GRADE_CHOICES, verbose_name='Оценка')
    date = models.DateField(auto_now_add=True)
    comment = models.CharField(max_length=300, blank=True)
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='given_grades'
    )

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.value}"

    def get_grade_label(self):
        labels = {5: 'Отлично', 4: 'Хорошо', 3: 'Удовлетворительно', 2: 'Неудовлетворительно', 1: 'Очень плохо'}
        return labels.get(self.value, str(self.value))

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-date']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'По уважительной причине'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.date}): {self.status}"

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        ordering = ['-date']
        unique_together = ['student', 'subject', 'date']


class Homework(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homeworks')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    deadline = models.DateTimeField(verbose_name='Срок сдачи')
    created_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.subject}: {self.title}"

    def is_overdue(self):
        from django.utils import timezone
        return self.deadline < timezone.now()

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['deadline']


class Schedule(models.Model):
    DAY_CHOICES = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedule')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedule')
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True
    )
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    time_start = models.TimeField()
    time_end = models.TimeField()
    room = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.group} - {self.subject} ({self.day} {self.time_start})"

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day', 'time_start']


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Информация'),
        ('grade', 'Оценка'),
        ('homework', 'Домашнее задание'),
        ('attendance', 'Посещаемость'),
        ('system', 'Система'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.title}"

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
