from django.db import models
from django.utils import timezone
from students.models import Student
from attendance.models import Attendance

class MemorizationPlan(models.Model):
    """
    Model to store weekly memorization plans
    """
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    week_start = models.DateField()  # Monday
    week_end = models.DateField()    # Thursday
    
    # Current progress
    current_surah = models.IntegerField()
    current_ayah = models.IntegerField()
    
    # Memorization target
    target_ayahs_per_day = models.IntegerField(default=5)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-week_start', 'student__full_name']
        verbose_name = 'Memorization Plan'
        verbose_name_plural = 'Memorization Plans'
    
    def __str__(self):
        return f"{self.student.full_name} - Week of {self.week_start.strftime('%Y-%m-%d')}"
    
    def get_daily_tasks(self):
        """
        Get all daily tasks associated with this plan
        """
        return self.dailytask_set.all().order_by(
            'date', 
            models.Case(
                models.When(task_type='new', then=models.Value(1)),
                models.When(task_type='review', then=models.Value(2)),
                default=models.Value(3),
                output_field=models.IntegerField(),
            )
        )
    
    def generate_daily_tasks(self):
        """
        Generate daily tasks based on the memorization plan
        """
        # Delete any existing tasks for this plan
        self.dailytask_set.all().delete()
        
        # Get surah and ayah information (this would ideally come from a Quran API or database)
        # For simplicity, we'll just use static values
        surah_lengths = {
            1: 7,    # الفاتحة
            2: 286,  # البقرة
            3: 200,  # آل عمران
            4: 176,  # النساء
            5: 120,  # المائدة
            6: 165,  # الأنعام
            7: 206,  # الأعراف
            8: 75,   # الأنفال
            9: 129,  # التوبة
            10: 109, # يونس
            11: 123, # هود
            12: 111, # يوسف
            13: 43,  # الرعد
            14: 52,  # إبراهيم
            15: 99,  # الحجر
            16: 128, # النحل
            17: 111, # الإسراء
            18: 110, # الكهف
            19: 98,  # مريم
            20: 135, # طه
            21: 112, # الأنبياء
            22: 78,  # الحج
            23: 118, # المؤمنون
            24: 64,  # النور
            25: 77,  # الفرقان
            26: 227, # الشعراء
            27: 93,  # النمل
            28: 88,  # القصص
            29: 69,  # العنكبوت
            30: 60,  # الروم
            31: 34,  # لقمان
            32: 30,  # السجدة
            33: 73,  # الأحزاب
            34: 54,  # سبأ
            35: 45,  # فاطر
            36: 83,  # يس
            37: 182, # الصافات
            38: 88,  # ص
            39: 75,  # الزمر
            40: 85,  # غافر
            41: 54,  # فصلت
            42: 53,  # الشورى
            43: 89,  # الزخرف
            44: 59,  # الدخان
            45: 37,  # الجاثية
            46: 35,  # الأحقاف
            47: 38,  # محمد
            48: 29,  # الفتح
            49: 18,  # الحجرات
            50: 45,  # ق
            51: 60,  # الذاريات
            52: 49,  # الطور
            53: 62,  # النجم
            54: 55,  # القمر
            55: 78,  # الرحمن
            56: 96,  # الواقعة
            57: 29,  # الحديد
            58: 22,  # المجادلة
            59: 24,  # الحشر
            60: 13,  # الممتحنة
            61: 14,  # الصف
            62: 11,  # الجمعة
            63: 11,  # المنافقون
            64: 18,  # التغابن
            65: 12,  # الطلاق
            66: 12,  # التحريم
            67: 30,  # الملك
            68: 52,  # القلم
            69: 52,  # الحاقة
            70: 44,  # المعارج
            71: 28,  # نوح
            72: 28,  # الجن
            73: 20,  # المزمل
            74: 56,  # المدثر
            75: 40,  # القيامة
            76: 31,  # الإنسان
            77: 50,  # المرسلات
            78: 40,  # النبأ
            79: 46,  # النازعات
            80: 42,  # عبس
            81: 29,  # التكوير
            82: 19,  # الانفطار
            83: 36,  # المطففين
            84: 25,  # الانشقاق
            85: 22,  # البروج
            86: 17,  # الطارق
            87: 19,  # الأعلى
            88: 26,  # الغاشية
            89: 30,  # الفجر
            90: 20,  # البلد
            91: 15,  # الشمس
            92: 21,  # الليل
            93: 11,  # الضحى
            94: 8,   # الشرح
            95: 8,   # التين
            96: 19,  # العلق
            97: 5,   # القدر
            98: 8,   # البينة
            99: 8,   # الزلزلة
            100: 11, # العاديات
            101: 11, # القارعة
            102: 8,  # التكاثر
            103: 3,  # العصر
            104: 9,  # الهمزة
            105: 5,  # الفيل
            106: 4,  # قريش
            107: 7,  # الماعون
            108: 3,  # الكوثر
            109: 6,  # الكافرون
            110: 3,  # النصر
            111: 5,  # المسد
            112: 4,  # الإخلاص
            113: 5,  # الفلق
            114: 6   # الناس
        }
        
        current_surah = self.current_surah
        current_ayah = self.current_ayah
        
        # Create tasks for Monday to Thursday
        for i in range(4):
            task_date = self.week_start + timezone.timedelta(days=i)
            
            # For future plans, we don't need to check attendance
            # We'll just create the tasks and let them be managed later
            
            # Calculate end ayah
            end_ayah = current_ayah + self.target_ayahs_per_day - 1
            
            # Check if we need to move to the next surah
            if current_surah in surah_lengths and end_ayah > surah_lengths[current_surah]:
                # Calculate remaining ayahs in current surah
                remaining_ayahs = surah_lengths[current_surah] - current_ayah + 1
                
                # Create task for current surah's remaining ayahs
                DailyTask.objects.create(
                    plan=self,
                    date=task_date,
                    task_type='new',
                    surah_start=current_surah,
                    ayah_start=current_ayah,
                    ayah_end=surah_lengths[current_surah],
                    status='pending'
                )
                
                # Move to next surah
                current_surah += 1
                current_ayah = 1
                
                # Create task for beginning of next surah if we have ayahs left to assign
                remaining_target = self.target_ayahs_per_day - remaining_ayahs
                if remaining_target > 0:
                    end_ayah = min(remaining_target, surah_lengths.get(current_surah, 999))
                    
                    DailyTask.objects.create(
                        plan=self,
                        date=task_date,
                        task_type='new',
                        surah_start=current_surah,
                        ayah_start=1,
                        ayah_end=end_ayah,
                        status='pending'
                    )
                    
                    current_ayah = end_ayah + 1
            else:
                # Create task within the same surah
                DailyTask.objects.create(
                    plan=self,
                    date=task_date,
                    task_type='new',
                    surah_start=current_surah,
                    ayah_start=current_ayah,
                    ayah_end=end_ayah,
                    status='pending'
                )
                
                current_ayah = end_ayah + 1
            
            # Also create a review task for previously memorized content
            # Check if the student has memorized enough content to review
            has_previous_memorization = False
            if self.current_surah > 1:
                has_previous_memorization = True
            elif self.current_surah == 1 and self.current_ayah > 10:
                has_previous_memorization = True
            
            if has_previous_memorization:
                # For simplicity, we'll just review the last 10 ayahs
                review_start = current_ayah - 10
                review_surah = current_surah
                
                if review_start < 1:
                    # Need to go back to previous surah
                    review_surah -= 1
                    if review_surah in surah_lengths:
                        review_start = surah_lengths[review_surah] - (10 - current_ayah)
                        if review_start < 1:
                            review_start = 1
                else:
                    review_start = max(1, review_start)
                
                DailyTask.objects.create(
                    plan=self,
                    date=task_date,
                    task_type='review',
                    surah_start=review_surah,
                    ayah_start=review_start,
                    ayah_end=current_ayah - 1 if review_surah == current_surah else surah_lengths.get(review_surah, 999),
                    status='pending'
                )

class DailyTask(models.Model):
    """
    Model to store daily memorization tasks
    """
    
    TASK_TYPE_CHOICES = [
        ('new', 'New Memorization'),
        ('review', 'Review'),
        ('tajweed', 'Tajweed Rules'),
        ('fiqh', 'Fiqh of Worship'),
        ('jibal', 'Ya Jibal Oobi'),
        ('custom', 'Custom Lesson'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    plan = models.ForeignKey(MemorizationPlan, on_delete=models.CASCADE)
    date = models.DateField()
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES)
    
    # For Quran memorization tasks
    surah_start = models.IntegerField(null=True, blank=True)
    ayah_start = models.IntegerField(null=True, blank=True)
    ayah_end = models.IntegerField(null=True, blank=True)
    
    # For non-Quran tasks
    description = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True, null=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'plan__student__full_name']
        verbose_name = 'Daily Task'
        verbose_name_plural = 'Daily Tasks'
    
    def __str__(self):
        if self.task_type in ['new', 'review']:
            return f"{self.plan.student.full_name} - {self.get_task_type_display()} - Surah {self.surah_start}:{self.ayah_start}-{self.ayah_end} ({self.date.strftime('%Y-%m-%d')})"
        else:
            return f"{self.plan.student.full_name} - {self.get_task_type_display()} - {self.date.strftime('%Y-%m-%d')}"
    
    def get_student(self):
        return self.plan.student
    
    @property
    def student(self):
        return self.plan.student
