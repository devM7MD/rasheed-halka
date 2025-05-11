from django.db import models
import os

def student_photo_path(instance, filename):
    """Define upload path for student photos"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Format filename as student_id.ext
    filename = f"{instance.id}.{ext}"
    return os.path.join('student_photos', filename)

def certificate_path(instance, filename):
    """Define upload path for student certificates"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Format filename as student_id_certificate_number.ext
    student_certificates = Certificate.objects.filter(student=instance.student).count()
    filename = f"{instance.student.id}_certificate_{student_certificates + 1}.{ext}"
    return os.path.join('certificates', filename)

class Student(models.Model):
    """Model to store student information"""
    
    GENDER_CHOICES = [
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    ]
    
    CATEGORY_CHOICES = [
        ('university', 'طالب جامعي'),
        ('school', 'طالب مدرسة'),
        ('graduate', 'خريج'),
    ]
    
    STUDY_LEVEL_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
    ]
    
    # Fixed information for all students in this halaqa
    branch = models.CharField(max_length=50, default='Ajman', verbose_name='الفرع')
    center = models.CharField(max_length=100, default='Abdullah bin Rashid Al Nuaimi - Male', verbose_name='المركز')
    center_type = models.CharField(max_length=50, default='Halaqa', verbose_name='نوع المركز')
    region = models.CharField(max_length=50, default='Al Rawdah', verbose_name='المنطقة')
    session_time = models.CharField(max_length=50, default='Evening', verbose_name='وقت الجلسة')
    teacher = models.CharField(max_length=100, default='Sheikh Rashid Al-Habshi', verbose_name='المعلم')
    
    # Variable information per student
    full_name = models.CharField(max_length=255, verbose_name='الاسم الكامل')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='الفئة')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='الجنس')
    nationality = models.CharField(max_length=100, verbose_name='الجنسية')
    date_of_birth = models.DateField(verbose_name='تاريخ الميلاد')
    registration_date = models.DateField(verbose_name='تاريخ التسجيل')
    study_level = models.IntegerField(choices=STUDY_LEVEL_CHOICES, verbose_name='المستوى الدراسي')
    phone_number = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    guardian_name = models.CharField(max_length=255, verbose_name='اسم ولي الأمر')
    guardian_phone = models.CharField(max_length=20, verbose_name='هاتف ولي الأمر')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='active', verbose_name='حالة الدفع')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='الحالة')
    photo = models.ImageField(upload_to=student_photo_path, blank=True, null=True, verbose_name='الصورة الشخصية')
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        ordering = ['full_name']
        verbose_name = 'طالب'
        verbose_name_plural = 'الطلاب'
        
    def is_active(self):
        return self.status == 'active'
    
    def get_certificates(self):
        return self.certificate_set.all()

class Certificate(models.Model):
    """Model to store student certificates"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='الطالب')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    file = models.FileField(upload_to=certificate_path, verbose_name='الملف')
    issue_date = models.DateField(verbose_name='تاريخ الإصدار')
    
    # Auto fields
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'شهادة'
        verbose_name_plural = 'الشهادات'
