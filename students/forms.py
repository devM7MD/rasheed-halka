from django import forms
from .models import Student, Certificate
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class StudentForm(forms.ModelForm):
    """Form for adding/editing students"""
    
    # Use a simpler list of common countries for nationality dropdown
    NATIONALITY_CHOICES = [
        ('UAE', 'الإمارات العربية المتحدة'),
        ('Saudi Arabia', 'المملكة العربية السعودية'),
        ('Egypt', 'مصر'),
        ('Jordan', 'الأردن'),
        ('Syria', 'سوريا'),
        ('Palestine', 'فلسطين'),
        ('Lebanon', 'لبنان'),
        ('Iraq', 'العراق'),
        ('Yemen', 'اليمن'),
        ('Oman', 'عمان'),
        ('Kuwait', 'الكويت'),
        ('Bahrain', 'البحرين'),
        ('Qatar', 'قطر'),
        ('Morocco', 'المغرب'),
        ('Algeria', 'الجزائر'),
        ('Tunisia', 'تونس'),
        ('Libya', 'ليبيا'),
        ('Sudan', 'السودان'),
        ('Somalia', 'الصومال'),
        ('Pakistan', 'باكستان'),
        ('India', 'الهند'),
        ('Bangladesh', 'بنغلاديش'),
        ('Philippines', 'الفلبين'),
        ('Other', 'أخرى')
    ]
    
    nationality = forms.ChoiceField(
        choices=NATIONALITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('الجنسية'),
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('تاريخ الميلاد'),
    )
    
    registration_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('تاريخ التسجيل'),
    )
    
    class Meta:
        model = Student
        fields = [
            'full_name', 'category', 'gender', 'nationality', 
            'date_of_birth', 'registration_date', 'study_level',
            'phone_number', 'guardian_name', 'guardian_phone',
            'payment_status', 'status', 'photo'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'study_level': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+971 XX XXX XXXX'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+971 XX XXX XXXX'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        if not phone.startswith('+'):
            raise ValidationError(_('يجب أن يبدأ رقم الهاتف برمز البلد (مثل: +971)'))
        return phone
    
    def clean_guardian_phone(self):
        """Validate guardian phone number format"""
        phone = self.cleaned_data.get('guardian_phone')
        if not phone.startswith('+'):
            raise ValidationError(_('يجب أن يبدأ رقم الهاتف برمز البلد (مثل: +971)'))
        return phone

class CertificateForm(forms.ModelForm):
    """Form for adding/editing certificates"""
    
    issue_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('تاريخ الإصدار'),
    )
    
    class Meta:
        model = Certificate
        fields = ['title', 'description', 'file', 'issue_date']
        labels = {
            'title': _('عنوان الشهادة'),
            'description': _('الوصف'),
            'file': _('ملف الشهادة'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        } 