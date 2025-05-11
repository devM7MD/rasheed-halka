from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Add a number of days to a date"""
    if value is None:
        return value
    return value + timedelta(days=int(days))

@register.filter
def get_range(value):
    """Create a range of numbers from 0 to value-1"""
    return range(int(value))

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    return int(value) - int(arg)

@register.filter
def div(value, arg):
    """Divide the value by the arg"""
    return int(value) / int(arg)

@register.filter
def mul(value, arg):
    """Multiply the value by the arg"""
    return int(value) * int(arg)

@register.filter
def count_tasks_by_type(tasks, task_type):
    """Count the number of tasks with the specified type"""
    count = 0
    for task in tasks:
        if task.task_type == task_type:
            count += 1
    return count

@register.filter
def surah_name(surah_number):
    """Convert surah number to its Arabic name"""
    surah_names = {
        1: "الفاتحة",
        2: "البقرة",
        3: "آل عمران",
        4: "النساء",
        5: "المائدة",
        6: "الأنعام",
        7: "الأعراف",
        8: "الأنفال",
        9: "التوبة",
        10: "يونس",
        11: "هود",
        12: "يوسف",
        13: "الرعد",
        14: "إبراهيم",
        15: "الحجر",
        16: "النحل",
        17: "الإسراء",
        18: "الكهف",
        19: "مريم",
        20: "طه",
        21: "الأنبياء",
        22: "الحج",
        23: "المؤمنون",
        24: "النور",
        25: "الفرقان",
        26: "الشعراء",
        27: "النمل",
        28: "القصص",
        29: "العنكبوت",
        30: "الروم",
        31: "لقمان",
        32: "السجدة",
        33: "الأحزاب",
        34: "سبأ",
        35: "فاطر",
        36: "يس",
        37: "الصافات",
        38: "ص",
        39: "الزمر",
        40: "غافر",
        41: "فصلت",
        42: "الشورى",
        43: "الزخرف",
        44: "الدخان",
        45: "الجاثية",
        46: "الأحقاف",
        47: "محمد",
        48: "الفتح",
        49: "الحجرات",
        50: "ق",
        51: "الذاريات",
        52: "الطور",
        53: "النجم",
        54: "القمر",
        55: "الرحمن",
        56: "الواقعة",
        57: "الحديد",
        58: "المجادلة",
        59: "الحشر",
        60: "الممتحنة",
        61: "الصف",
        62: "الجمعة",
        63: "المنافقون",
        64: "التغابن",
        65: "الطلاق",
        66: "التحريم",
        67: "الملك",
        68: "القلم",
        69: "الحاقة",
        70: "المعارج",
        71: "نوح",
        72: "الجن",
        73: "المزمل",
        74: "المدثر",
        75: "القيامة",
        76: "الإنسان",
        77: "المرسلات",
        78: "النبأ",
        79: "النازعات",
        80: "عبس",
        81: "التكوير",
        82: "الانفطار",
        83: "المطففين",
        84: "الانشقاق",
        85: "البروج",
        86: "الطارق",
        87: "الأعلى",
        88: "الغاشية",
        89: "الفجر",
        90: "البلد",
        91: "الشمس",
        92: "الليل",
        93: "الضحى",
        94: "الشرح",
        95: "التين",
        96: "العلق",
        97: "القدر",
        98: "البينة",
        99: "الزلزلة",
        100: "العاديات",
        101: "القارعة",
        102: "التكاثر",
        103: "العصر",
        104: "الهمزة",
        105: "الفيل",
        106: "قريش",
        107: "الماعون",
        108: "الكوثر",
        109: "الكافرون",
        110: "النصر",
        111: "المسد",
        112: "الإخلاص",
        113: "الفلق",
        114: "الناس"
    }
    try:
        surah_num = int(surah_number)
        return surah_names.get(surah_num, f"سورة {surah_num}")
    except (ValueError, TypeError):
        return surah_number 