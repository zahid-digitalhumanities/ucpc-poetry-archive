# models/search_model.py
import re
import json
import numpy as np
from rapidfuzz import fuzz

from models.base import get_db_connection
from modules.embeddings import generate_embedding

# =========================================================
# ROMAN ENGINE
# =========================================================
try:
    from modules.roman_engine.matcher import process_query
except ImportError:
    def process_query(x):
        return x

# =========================================================
# ROMAN → URDU DICTIONARY (keep your full dictionary)
# =========================================================
ROMAN_DICT = {
    "mohabbat": "محبت",
    "ishq": "عشق",
    "pyar": "پیار",
    "dard": "درد",
    "zindagi": "زندگی",
    "raat": "رات",
    "tanhaai": "تنہائی",
    "yaad": "یاد",
    "dil": "دل",
    "aankh": "آنکھ",
    "lab": "لب",
    "chehra": "چہرہ",
    "husn": "حسن",
    "khuda": "خدا",
    "safar": "سفر",
    "manzil": "منزل",
    "dunya": "دنیا",
    "gham": "غم",
    "aansu": "آنسو",
    "jaan": "جان",
 "ishq": "عشق",
    "pyar": "پیار",
    "dard": "درد",
    "zindagi": "زندگی",
    "raat": "رات",
    "tanhaai": "تنہائی",
    "yaad": "یاد",
    "dil": "دل",
    "aankh": "آنکھ",
    "lab": "لب",
    "chehra": "چہرہ",
    "husan": "حسن",
    "khuda": "خدا",
    "safar": "سفر",
    "manzil": "منزل",
    "dunya": "دنیا",
    "gham": "غم",
    "aansu": "آنسو",
    "jaan": "جان",
    "night": "رات",
    "love": "محبت",
    "lonely": "تنہائی",
    "sad": "غم",
    "heart": "دل",
    "life": "زندگی",
    "death": "موت",
    "moon": "چاند",
    "flower": "پھول",
    "pain": "درد",
    "hope": "امید",
    "waiting": "انتظار",

    # Numbers 1–20
    "ek": "ایک",
    "do": "دو",
    "teen": "تین",
    "chaar": "چار",
    "paanch": "پانچ",
    "chhe": "چھے",
    "saat": "سات",
    "aath": "آٹھ",
    "nau": "نو",
    "das": "دس",
    "gyaarah": "گیارہ",
    "baarah": "بارہ",
    "terah": "تیرہ",
    "chaudah": "چودہ",
    "pandrah": "پندرہ",
    "solah": "سولہ",
    "satrah": "سترہ",
    "athaarah": "اٹھارہ",
    "unnis": "انیس",
    "bees": "بیس",

    # Days
    "itwaar": "اتوار",
    "peer": "پیر",
    "mangal": "منگل",
    "budh": "بدھ",
    "jumerat": "جمعرات",
    "jummah": "جمعہ",
    "hafta": "ہفتہ",

    # Months
    "muharram": "محرم",
    "safar_month": "صفر",
    "rabiul_awwal": "ربیع الاول",
    "rabiul_saani": "ربیع الثانی",
    "jamadiul_awwal": "جمادی الاول",
    "jamadiul_saani": "جمادی الثانی",
    "rajab": "رجب",
    "shabaan": "شعبان",
    "ramadan": "رمضان",
    "shawwal": "شوال",
    "zilqadah": "ذوالقعدہ",
    "zilhijjah": "ذوالحجہ",
    "janvari": "جنوری",
    "farvari": "فروری",
    "march": "مارچ",
    "april": "اپریل",
    "may": "مئی",
    "june": "جون",
    "july": "جولائی",
    "august": "اگست",
    "september": "ستمبر",
    "october": "اکتوبر",
    "november": "نومبر",
    "december": "دسمبر",

    # Colors
    "laal": "لال",
    "neela": "نیلا",
    "hara": "ہرا",
    "peela": "پیلا",
    "safed": "سفید",
    "kala": "کالا",
    "bhoora": "بھورا",
    "narangi": "نارنجی",
    "gulabi": "گلابی",
    "jamuni": "جامنی",
    "khaki": "خاکی",
    "chandi": "چاندی",
    "sona": "سونا",
    "aasmani": "آسمانی",
    "firozi": "فیروزی",

    # Family
    "maan": "ماں",
    "baap": "باپ",
    "bhai": "بھائی",
    "behan": "بہن",
    "beta": "بیٹا",
    "beti": "بیٹی",
    "khawand": "خاوند",
    "biwi": "بیوی",
    "dada": "دادا",
    "dadi": "دادی",
    "nana": "نانا",
    "nani": "نانی",
    "chaacha": "چچا",
    "chaachi": "چچی",
    "mamoon": "ماموں",
    "mami": "مامی",
    "khaloo": "خالو",
    "khala": "خالہ",
    "bhatija": "بھتیجا",
    "bhatiji": "بھتیجی",

    # Body parts
    "sar": "سر",
    "baal": "بال",
    "maatha": "ماتھا",
    "bhaun": "بھوں",
    "palken": "پلکیں",
    "naak": "ناک",
    "kaan": "کان",
    "gal": "گال",
    "moo": "منہ",
    "daant": "دانٹ",
    "zaban": "زبان",
    "gardan": "گردن",
    "kandha": "کندھا",
    "baazu": "بازو",
    "haath": "ہاتھ",
    "ungli": "انگلی",
    "khushoona": "خشونہ",
    "seenah": "سینہ",
    "peeth": "پیٹھ",
    "pait": "پیٹ",
    "tang": "ٹانگ",
    "ghutna": "گھٹنا",
    "pair": "پیر",
    "jism": "جسم",
    "khoon": "خون",

    # Nature
    "suraj": "سورج",
    "chand": "چاند",
    "sitara": "ستارہ",
    "aasmaan": "آسمان",
    "zameen": "زمین",
    "hawa": "ہوا",
    "paani": "پانی",
    "aag": "آگ",
    "barf": "برف",
    "badal": "بادل",
    "barsaat": "بارش",
    "bijli": "بجلی",
    "dhoop": "دھوپ",
    "chaon": "چھاؤں",
    "kohar": "کوہر",
    "dhund": "دھند",
    "jharna": "جھرنا",
    "nadi": "ندی",
    "samandar": "سمندر",
    "pahaar": "پہاڑ",
    "jangal": "جنگل",
    "raasta": "راستہ",
    "bagh": "باغ",
    "phool": "پھول",
    "pattha": "پتھر",
    "mitti": "مٹی",
    "ghaas": "گھاس",
    "darakht": "درخت",
    "patta": "پتہ",
    "bij": "بیج",

    # Emotions
    "khushi": "خوشی",
    "udasi": "اداسی",
    "ghussa": "غصہ",
    "pyaar": "پیار",
    "nफरत": "نفرت",
    "irshaad": "ارشاد",
    "jazbaat": "جذبات",
    "josh": "جوش",
    "sukoon": "سکون",
    "bebasi": "بے بسی",
    "majboori": "مجبوری",
    "umeed": "امید",
    "na_umeedi": "ناامیدی",
    "tashweesh": "تشویش",
    "fear": "خوف",
    "andshesha": "اندیشہ",
    "hairat": "حیرت",
    "sharm": "شرم",
    "ghuroor": "غرور",
    "hassad": "حسد",
    "rahmat": "رحمت",
    "shafqat": "شفقت",
    "wafa": "وفا",
    "bewafai": "بے وفائی",
    "judai": "جدائی",
    "wasl": "وصل",
    "hijr": "ہجر",
    "khamoshi": "خاموشی",
    "shiddat": "شدت",

    # Verbs
    "karna": "کرنا",
    "hona": "ہونا",
    "jana": "جانا",
    "aana": "آنا",
    "dena": "دینا",
    "lena": "لینا",
    "bolna": "بولنا",
    "sona": "سونا",
    "jagna": "جگنا",
    "khana": "کھانا",
    "peena": "پینا",
    "rona": "رونا",
    "hansna": "ہنسنا",
    "parhna": "پڑھنا",
    "likhna": "لکھنا",
    "chalna": "چلنا",
    "daurna": "دوڑنا",
    "baithna": "بیٹھنا",
    "uthna": "اٹھنا",
    "dekna": "دیکھنا",
    "sunna": "سننا",
    "sochna": "سوچنا",
    "samajhna": "سمجھنا",
    "poochna": "پوچھنا",
    "batana": "بتانا",
    "milna": "ملنا",
    "khelna": "کھیلنا",
    "nahaana": "نہانا",
    "kapre_pehenna": "کپڑے پہننا",
    "nikaalna": "نکالنا",
    "daalna": "ڈالنا",
    "todna": "توڑنا",
    "jodna": "جوڑنا",
    "khareedna": "خریدنا",
    "bechna": "بیچنا",
    "jeetna": "جیتنا",
    "haarna": "ہارنا",
    "banna": "بنا",
    "bighadna": "بگڑنا",
    "rukna": "رکنا",
    "chalna_phirna": "چلنا پھرنا",
    "ghumna": "گھومنا",
    "thakna": "تھکنا",
    "aaraam_karna": "آرام کرنا",
    "ro_kar_karna": "رو کر کرنا",
    "hans_kar_karna": "ہنس کر کرنا",
    "manna": "ماننا",
    "inkaar_karna": "انکار کرنا",
    "wada_karna": "وعدہ کرنا",
    "nibhana": "نبانا",

    # Adjectives
    "acha": "اچھا",
    "bura": "برا",
    "khoobsurat": "خوبصورت",
    "baddar": "بدصورت",
    "naya": "نیا",
    "purana": "پرانا",
    "garam": "گرم",
    "thanda": "ٹھنڈا",
    "meetha": "میٹھا",
    "khatta": "کھٹا",
    "namkeen": "نمکین",
    "taza": "تازہ",
    "purzoor": "پرزور",
    "kamzor": "کمزور",
    "amir": "امیر",
    "ghareeb": "غریب",
    "khush": "خوش",
    "udaas": "اداس",
    "poraana": "پُرانا",
    "jadeed": "جدید",
    "buland": "بلند",
    "pust": "پست",
    "roshan": "روشن",
    "andhera": "اندھیرا",
    "tez": "تیز",
    "ahista": "آہستہ",
    "saf": "صاف",
    "ganda": "گندا",
    "sona": "سونا",
    "chandi_jaisa": "چاندی جیسا",
    "pukhta": "پختہ",
    "kacha": "کچا",
    "sakht": "سخت",
    "naram": "نرم",
    "bhaari": "بھاری",
    "halka": "ہلکا",
    "lambi": "لمبی",
    "chhoti": "چھوٹی",
    "mota": "موٹا",
    "patla": "پتلا",
    "rangeen": "رنگین",
    "be_rang": "بے رنگ",
    "mahanga": "مہنگا",
    "sasta": "سستا",
    "dumdaar": "دمدار",
    "bewaqoof": "بیوقوف",
    "hoshyaar": "ہوشیار",
    "tajurba_kaar": "تجربہ کار",
    "na_tajurba_kaar": "نا تجربہ کار",

    # Food
    "roti": "روٹی",
    "chawal": "چاول",
    "daal": "دال",
    "sabzi": "سبزی",
    "ghosht": "گوشت",
    "murghi": "مرغی",
    "machli": "مچھلی",
    "anda": "انڈہ",
    "doodh": "دودھ",
    "dahi": "دہی",
    "panir": "پنیر",
    "makhan": "مکھن",
    "shakar": "شکر",
    "namak": "نمک",
    "mirch": "مرچ",
    "haldi": "ہلدی",
    "zeera": "زیرہ",
    "chatni": "چٹنی",
    "achar": "اچار",
    "samosa": "سموسہ",
    "pakora": "پکوڑا",
    "biryani": "بریانی",
    "qorma": "قورمہ",
    "kebab": "کباب",
    "nihari": "نہاری",
    "haleem": "حلیم",
    "paye": "پائے",
    "kheer": "کھیر",
    "falooda": "فلودہ",
    "jalebi": "جلیبی",

    # Household
    "darwaza": "دروازہ",
    "kirkhi": "کھڑکی",
    "kamra": "کمرہ",
    "bistar": "بستر",
    "takya": "تکیہ",
    "chaadar": "چادر",
    "kursi": "کرسی",
    "mez": "میز",
    "almari": "الماری",
    "sofa": "سوفہ",
    "farsh": "فرش",
    "dari": "داری",
    "pankha": "پنکھا",
    "bulb": "بلب",
    "barat_numa": "برات نما",
    "batari": "بٹری",
    "chulha": "چولہا",
    "tawa": "توہ",
    "deg": "دیگ",
    "karahi": "کراہی",
    "chammach": "چمچ",
    "kaanta": "کانٹا",
    "chaku": "چاقو",
    "glass": "گلاس",
    "pyala": "پیالہ",
    "surahi": "سوراہی",
    "dastarkhwan": "دسترخوان",
    "kalaam": "قلم",
    "kaghaz": "کاغذ",
    "kitab": "کتاب",

    # Clothing
    "kapray": "کپڑے",
    "qameez": "قمیض",
    "pajama": "پاجامہ",
    "shalwar": "شلوار",
    "dupatta": "دوپٹہ",
    "burqa": "برقع",
    "topi": "ٹوپی",
    "jaacket": "جیکٹ",
    "coat": "کوٹ",
    "sweater": "سویٹر",
    "joota": "جوتا",
    "mojari": "موجاری",
    "chappal": "چپل",
    "shoes": "شوز",
    "lungi": "لنگی",
    "tie": "ٹائی",
    "belt": "بیلٹ",
    "ring": "انگوٹھی",
    "choori": "چوڑی",
    "hath_kari": "ہاتھ کاری",

    # Time
    "subah": "صبح",
    "shaam": "شام",
    "din": "دن",
    "ghadi": "گھڑی",
    "pal": "پل",
    "lamha": "لمحہ",
    "saal": "سال",
    "mahina": "مہینہ",
    "hafta_block": "ہفتہ",
    "ghanta": "گھنٹہ",
    "minute": "منٹ",
    "second": "سیکنڈ",
    "aaj": "آج",
    "kal": "کل",
    "parson": "پرسوں",
    "teesra_din": "تیسرا دن",
    "hafta_baar": "ہفتہ بھر",
    "mahina_baar": "مہینہ بھر",
    "saal_baar": "سال بھر",
    "hamesha": "ہمیشہ",

    # Directions
    "shumal": "شمال",
    "janob": "جنوب",
    "mashriq": "مشرق",
    "maghrib": "مغرب",
    "utra": "اتر",
    "dakhan": "دکھن",
    "dayen": "دائیں",
    "bayein": "بائیں",
    "seedha": "سیدھا",
    "peechay": "پیچھے",
    "aage": "آگے",

    # Pronouns
    "main": "میں",
    "tum": "تم",
    "tuu": "تو",
    "aap": "آپ",
    "hum": "ہم",
    "woh": "وہ",
    "yeh": "یہ",
    "apna": "اپنا",
    "khud": "خود",
    "kisi": "کسی",
    "kuch": "کچھ",
    "sab": "سب",

    # Prepositions
    "ko": "کو",
    "se": "سے",
    "par": "پر",
    "tak": "تک",
    "liye": "لیے",
    "baad": "بعد",
    "pehle": "پہلے",
    "andar": "اندر",
    "bahar": "باہر",
    "paas": "پاس",
    "door": "دور",
    "aur": "اور",
    "ya": "یا",
    "lekin": "لیکن",
    "kyunke": "کیونکہ",
    "agar": "اگر",
    "toh": "تو",
    "warna": "ورنہ",

    # Common nouns
    "insaan": "انسان",
    "aurat": "عورت",
    "mard": "مرد",
    "bacha": "بچہ",
    "larki": "لڑکی",
    "larka": "لڑکا",
    "dost": "دوست",
    "duShman": "دشمن",
    "ustaad": "استاد",
    "shagird": "شاگرد",
    "doctor": "ڈاکٹر",
    "engineer": "انجینئر",
    "kaam": "کام",
    "office": "دفتر",
    "school": "اسکول",
    "college": "کالج",
    "university": "یونیورسٹی",
    "masjid": "مسجد",
    "mandir": "مندر",
    "girja": "گرجا",
    "bazar": "بازار",
    "gali": "گلی",
    "mohalla": "محلہ",
    "shehar": "شہر",
    "gaon": "گاؤں",
    "park": "پارک",
    "hospital": "ہسپتال",
    "police": "پولیس",
    "court": "عدالت",
    "qanon": "قانون",

    # Poetic / literary
    "ulfat": "الفت",
    "nigaah": "نگاہ",
    "nazar": "نظر",
    "qaatil": "قاتل",
    "ashk": "اشک",
    "arma": "ارما",
    "humdum": "ہمدم",
    "hamsafar": "ہمسفر",
    "rafeeq": "رفیق",
    "saaqi": "ساقی",
    "maikhana": "مے خانہ",
    "sharab": "شراب",
    "saba": "صبا",
    "bahar": "بہار",
    "khizan": "خزاں",
    "gul": "گل",
    "bulbul": "بلبل",
    "shama": "شمع",
    "parwana": "پروانہ",
    "qafas": "قفس",
    "firaaq": "فراق",
    "visaal": "وسال",
    "gamze": "غمزے",
    "kajal": "کاجل",
    "surma": "سرمہ",
    "mehndi": "مہندی",
    "sindoor": "سندور",
    "ghoonghat": "گھونگھٹ",
    "paayal": "پائل",

    # English loanwords
    "computer": "کمپیوٹر",
    "mobile": "موبائل",
    "internet": "انٹرنیٹ",
    "wiFi": "وائی فائی",
    "battery": "بیٹری",
    "charger": "چارجر",
    "screen": "اسکرین",
    "keyboard": "کی بورڈ",
    "mouse": "ماؤس",
    "printer": "پرنٹر",
    "scanner": "اسکینر",
    "camera": "کیمرہ",
    "video": "ویڈیو",
    "audio": "آڈیو",
    "music": "میوزک",
    "film": "فلم",
    "actor": "اداکار",
    "actress": "اداکارہ",
    "director": "ڈائریکٹر",
    "producer": "پروڈیوسر",
    "ticket": "ٹکٹ",
    "bus": "بس",
    "car": "کار",
    "train": "ٹرین",
    "plane": "ہوائی جہاز",
    "station": "اسٹیشن",
    "airport": "ایئرپورٹ",
    "hotel": "ہوٹل",
    "restaurant": "ریسٹورنٹ",
    "market": "مارکیٹ",

    # Religious
    "Allah": "اللہ",
    "Rasool": "رسول",
    "Quran": "قرآن",
    "Hadith": "حدیث",
    "Namaz": "نماز",
    "Roza": "روزہ",
    "Zakat": "زکوٰۃ",
    "Hajj": "حج",
    "masjid_c": "مسجد",
    "mullah": "ملا",
    "imaam": "امام",
    "muazzin": "مؤذن",
    "wudu": "وضو",
    "dua": "دعا",
    "fateha": "فاتحہ",
    "jannah": "جنت",
    "dozakh": "دوزخ",
    "shaitan": "شیطان",
    "farishta": "فرشتہ",
    "naseeb": "نصیب",
    "taqdeer": "تقدیر",

    # Legal
    "police_station": "پولیس اسٹیشن",
    "thana": "تھانہ",
    "judge": "جج",
    "vakeel": "وکیل",
    "muqadma": "مقدمہ",
    "mujrim": "مجرم",
    "saza": "سزا",
    "jail": "جیل",
    "aain": "آئین",
    "hukumat": "حکومت",
    "vazir": "وزیر",
    "sadr": "صدر",
    "wazir_e_azam": "وزیر اعظم",
    "intikhabaat": "انتخابات",
    "vote": "ووٹ",
    "jamhooriyat": "جمہوریت",
    "riyasat": "ریاست",
    "shahri": "شہری",
    "passport": "پاسپورٹ",
    "visa": "ویزا",

    # Science
    "science": "سائنس",
    "physics": "طبیعیات",
    "chemistry": "کیمسٹری",
    "biology": "حیاتیات",
    "maths": "ریاضی",
    "geometry": "ہندسہ",
    "algebra": "الجبرا",
    "history": "تاریخ",
    "geography": "جغرافیہ",
    "economics": "اقتصادیات",
    "sociology": "سماجیات",
    "psychology": "نفسیات",
    "philosophy": "فلسفہ",
    "logic": "منطق",
    "research": "تحقیق",
    "lab": "لیب",
    "experiment": "تجربہ",
    "theory": "نظریہ",
    "law": "قانون",
    "medicine": "طب",
    "engineering": "انجینئری",

    # Travel
    "safar_karna": "سفر کرنا",
    "musafir": "مسافر",
    "samaan": "سامان",
    "bag": "بیگ",
    "suitcase": "سوٹ کیس",
    "passenger": "مسافر",
    "driver": "ڈرائیور",
    "pilot": "پائلٹ",
    "captain": "کپتان",
    "map": "نقشہ",
    "compass": "قطب نما",
    "hotel_room": "ہوٹل کا کمرہ",
    "booking": "بکنگ",
    "tour": "ٹور",
    "guide": "رہنما",
    "sightseeing": "سیر و تفریح",
    "adventure": "مہم جوئی",
    "beach": "ساحل",
    "mountain": "پہاڑ",
    "desert": "صحرا",

    # Health
    "sehat": "صحت",
    "bemari": "بیماری",
    "bukhar": "بخار",
    "khansi": "کھانسی",
    "zukam": "زکام",
    "dard_sar": "درد سر",
    "dant_dard": "دانت درد",
    "operation": "آپریشن",
    "dawai": "دوا",
    "injection": "انجکشن",
    "tablet": "گولی",
    "sharbat": "شربت",
    "doctor_c": "ڈاکٹر",
    "nurse": "نرس",
    "hospital_c": "ہسپتال",
    "clinic": "کلینک",
    "ambulance": "ایمبولینس",
    "blood_pressure": "بلڈ پریشر",
    "sugar": "شوگر",
    "temperature": "درجہ حرارت",

    # Animals
    "sher": "شیر",
    "chita": "چیتا",
    "hathi": "ہاتھی",
    "ghora": "گھوڑا",
    "gaaye": "گائے",
    "bhains": "بھینس",
    "bakri": "بکری",
    "bher": "بھیڑ",
    "kutta": "کتا",
    "billi": "بلی",
    "chooha": "چوہا",
    "gilehri": "گلہری",
    "khargosh": "خرگوش",

    # Additional poetic entries
    "ishara": "اشارہ",
    "sitam": "ستم",
    "jafa": "جفا",
    "kadam": "قدم",
    "raste": "راستے",
    "rahguzaar": "رہگزار",
    "humrahi": "ہمراہی",
    "dilbar": "دلبر",
    "dildaar": "دلدار",
    "mahboob": "محبوب",
    "sanam": "صنم",
    "parwardigar": "پروردگار",
    "qismat": "قسمت",
    "aah": "آہ",
    "faryaad": "فریاد",
    "ghazal": "غزل",
    "nazm": "نظم",
    "sher": "شعر",
    "shayar": "شاعر",
    "qalam": "قلم",
    "dafatar": "دفتر",
    "shab": "شب",
    "fajr": "فجر",
    "ratjaga": "رات جاگا",
    "chandni": "چاندنی",
    "patjhad": "پت جھڑ",
    "hawain": "ہوائیں",
    "jhonka": "جھونکا",
    "shaam_e_gham": "شام غم",
    "ranj": "رنج",
    "alam": "الم",
    "aazaar": "آزار",
    "beqarari": "بے قراری",
    "iztiraab": "اضطراب",
    "karb": "کرب",
    "marham": "مرہم",
    "darman": "درمان",
    "dukh": "دکھ",
    "sukh": "سکھ",
    "musarrat": "مسرت",
    "rahat": "راحت",
    "chain": "چین",
    "qaraar": "قرار",
    "naghma": "نغمہ",
    "sargam": "سرگم",
    "raag": "راغ",
    "dhadkan": "دھڑکن",
    "sans": "سانس",
    "neend": "نیند",
    "khwab": "خواب",
    "taabeer": "تعبیر",
    "yaas": "یاس",
    "mayaasi": "مایوسی",
    "viraan": "ویران",
    "veeraana": "ویرانہ",
    "ranjish": "رنجش",
    "shikwa": "شکوہ",
    "shikayat": "شکایت",
    "gila": "گلہ",
    "malal": "ملال",
    "afsos": "افسوس",
    "hasrat": "حسرت",
    "tamanna": "تمنا",
    "justaju": "جستجو",
    "talash": "تلاش",
    "rah": "رہ",
    "raaz": "راز",
    "bhay": "بھے",
    "jaana": "جانا",
    "kehana": "کہنا",
    "muskurana": "مسکرانا",
    "roothna": "روٹھنا",
    "manaana": "منانا",
    "bicharna": "بچھڑنا",
    "tharana": "تھرنا",
    "tadapna": "تڑپنا",
    "guzarna": "گزرنا",
    "dharna": "دھرنا",
    "latakna": "لٹکنا",
    "bali": "بچی",
    "yaar": "یار",
    "sathi": "ساتھی",
    "humdam": "ہمدرد",
    "dukhi": "دکھی",
    "pareshan": "پریشان",
    "ghamgeen": "غمین",
    "shaad": "شاد",
    "maayoos": "مایوس",
    "nakaam": "ناکام",
    "kamiyaab": "کامیاب",
    "mukammal": "مکمل",
    "adhoora": "ادھورا",
    "tareek": "تاریک",
    "pur_kaar": "پرکار",
    "be_kaar": "بیکار",
    "rangin": "رنگین",
    "haseen": "حسین",
    "jameel": "جمیل",
    "khubsurat": "خوبصورت",
    "badsurat": "بدصورت",
    "ajeeb": "عجیب",
    "ghaflat": "غفلت",
    "hosh": "ہوش",
    "behosh": "بے ہوش",
    "khayal": "خیال",
    "waswas": "وسواس",
    "shak": "شک",
    "yaqeen": "یقین",
    "guman": "گمان",
    "qadar": "قدر",
    "izzat": "عزت",
    "ruswa": "رسوا",
    "naam": "نام",
    "nishaan": "نشان",
    "pata": "پتہ",
    "thikana": "ٹھکانہ",
    "ghar": "گھر",
    "vatan": "وطن",
    "des": "دیس",
    "pardes": "پردیس",
    "dag": "داغ",
    "zakhm": "زخم",
    "ragh": "رگ",
    "nas": "نس",
    "aankhon mein": "آنکھوں میں",
    "lab par": "لب پر",
    "dil mein": "دل میں",
    "rukh se": "رخ سے",
    "baat": "بات",
    "alfaz": "الفاظ",
    "lafz": "لفظ",
    "misra": "مصرعہ",
    "qafiya": "قافیہ",
    "radeef": "ردیف",
    "matla": "مطلع",
    "maqta": "مقطع",
    "takhallus": "تخلص",

    # Another 200+ entries
    "aaina": "آئینہ",
    "nasheman": "آشیانہ",
    "barg": "برگ",
    "shakh": "شاخ",
    "daman": "دامن",
    "daaman": "دامن",
    "garebaan": "گریباں",
    "jigar": "جگر",
    "deeda": "دیدہ",
    "mizhga": "مژگاں",
    "rukhsaar": "رخسار",
    "zulf": "زلف",
    "gesu": "گیسو",
    "kakul": "کاکل",
    "payambar": "پیغمبر",
    "rusool": "رسول",
    "murshid": "مرشد",
    "deewana": "دیوانہ",
    "mast": "مست",
    "mai": "مے",
    "jaam": "جام",
    "saghar": "ساغر",
    "meena": "مینا",
    "bada": "بڑا",
    "masti": "مستی",
    "nasha": "نشہ",
    "bekaar": "بیکار",
    "darbadar": "دربدر",
    "mukhbari": "مخبری",
    "paighaam": "پیغام",
    "qasid": "قاصد",
    "khat": "خط",
    "ruqaa": "رقاع",
    "tahrir": "تحریر",
    "aawaz": "آواز",
    "sada": "صدا",
    "gunj": "گنج",
    "goonj": "گونج",
    "sookha": "سوکھا",
    "tar": "تر",
    "nam": "نم",
    "numa": "نما",
    "benam": "بے نام",
    "badnaam": "بدنام",
    "sitara_ha": "ستارے",
    "khurshid": "خورشید",
    "mehtaab": "مہتاب",
    "anjum": "انجم",
    "falak": "فلک",
    "gardoon": "گردوں",
    "qamar": "قمر",
    "zamee": "زہرہ",
    "khaak": "خاک",
    "gard": "گرد",
    "shor": "شور",
    "ghul": "غول",
    "gubar": "غبار",
    "dhuwan": "دھواں",
    "shola": "شعلہ",
    "roshni": "روشنی",
    "ujala": "اجالا",
    "chiragh": "چراغ",
    "diya": "دیہ",
    "deep": "دیپ",
    "phool_jhaari": "پھول جھاڑی",
    "kali": "کلی",
    "kuinchi": "کونچ",
    "deh": "دیہ",
    "gaaon": "گاؤں",
    "basti": "بستی",
    "nagar": "نگر",
    "nagri": "نگری",
    "raah": "راہ",
    "raah_e": "راہِ",
    "rahgir": "راہگیر",
    "karwaan": "کارواں",
    "qaafila": "قافلہ",
    "manzil_hr": "منزل",
    "rah_ro": "رہ رو",
    "gird": "گرد",
    "laash": "لاش",
    "jasad": "جسد",
    "kaifiyat": "کیفیت",
    "haal": "حال",
    "jazba": "جذبہ",
    "dil_dari": "دل داری",
    "dil_geer": "دل گیر",
    "dil_shikasta": "دل شکستہ",
    "dil_shikan": "دل شکن",
    "soz": "سوز",
    "gudaz": "گداز",
    "navaa": "نوا",
    "naala": "نالہ",
    "baar": "بار",
    "bala": "بالا",
    "aafaat": "آفات",
    "balaa": "بلا",
    "ghamzada": "غم زدہ",
    "ranj_urdu": "رنج",
    "malaal": "ملال",
    "naadaan": "نادان",
    "ahmaq": "احمق",
    "saada": "سادہ",
    "saada_looh": "سادہ لوح",
    "khaalis": "خالص",
    "nirdosh": "نردوش",
    "gunah": "گناہ",
    "bakhshna": "بخشنا",
    "maaf_karna": "معاف کرنا",
    "rahem": "رحم",
    "reham": "ریحم",
    "karam": "کرم",
    "ehesaan": "احسان",
    "shukr": "شکر",
    "shukriya": "شکریہ",
    "tashakur": "تذکیر",
    "hazir": "حاضر",
    "ghaeb": "غائب",
    "gum": "گم",
    "pa": "پا",
    "paana": "پانا",
    "khona": "کھونا",
    "mil_jaana": "مل جانا",
    "bichharna": "بچھڑنا",
    "lootna": "لوٹنا",
    "lutaana": "لٹانا",
    "ga_na": "گانا",
    "sunaa": "سنا",
    "dekhna": "دیکھنا",
    "takna": "تکنا",
    "ghur_se": "گھور سے",
    "jhaankna": "جھانکنا",
    "chhupna": "چھپنا",
    "chhupana": "چھپانا",
    "ro_dena": "رو دینا",
    "hans_dena": "ہنس دینا",
    "muskar_dena": "مسکر دینا",
    "chal_dena": "چل دینا",
    "bhagna": "بھاگنا",
    "bhaagna": "بھاگنا",
    "aankh_se": "آنکھ سے",
    "nazar_se": "نظر سے",
    "nigah_se": "نگاہ سے",
    "chehre_par": "چہرے پر",
    "honton_pe": "ہونٹوں پے",
    "sanson_mein": "سانسوں میں",
    "dharkanon_mein": "دھڑکنوں میں",
    "kabhi": "کبھی",
    "kabhi_kabhi": "کبھی کبھی",
    "aksar": "اکثر",
    "ab": "اب",
    "tab": "تب",
    "jab": "جب",
    "kab": "کب",
    "yahan": "یہاں",
    "wahan": "وہاں",
    "kahan": "کہاں",
    "idhar": "ادھر",
    "udhar": "ادھر",
    "kidhar": "کدھر",
    "kitna": "کتنا",
    "jitna": "جتنا",
    "itna": "اتنا",
    "thoda": "تھوڑا",
    "zyada": "زیادہ",
    "bohot": "بہت",
    "kafi": "کافی",
    "bilkul": "بلکل",
    "sab_kuch": "سب کچھ",
    "kuch_bhi": "کچھ بھی",
    "kuch_na": "کچھ نا",
    "jaisa": "جیسا",
    "waisa": "ویسا",
    "aisa": "ایسا",
    "kaisa": "کیسا",
    "jaise": "جیسے",
    "waise": "ویسے",
    "jaisey": "جیسے",
    "woh_l": "وہ",
    "yeh_l": "یہ",
    "main_p": "میں",
    "ham_p": "ہم",
    "apna_p": "اپنا",
    "tera": "تیرا",
    "mera": "میرا",
    "uska": "اسکا",
    "inka": "انکا",
    "unki": "انکی",
    "jinki": "جنکی",
    "jiska": "جسکا",
    "jin_ko": "جن کو",
    "jis_se": "جس سے",
    "jin_mein": "جن میں",
    "jis_par": "جس پر",
    "jin_ka": "جن کا",
    "ji_haan": "جی ہاں",
    "nahi": "نہیں",
    "mat": "مت",
    "shayed": "شاید",
    "to": "تو",
    "ki_oor": "کیوں",
    "kis_liye": "کسی لیے",
    "kya": "کیا",
    "na": "نا",
    "haan": "ہاں",
    "jee": "جی",
    "beshak": "بیشک",
    "albatta": "البظا",
    "yaqeenan": "یقینا",
    "goya": "گویا",
    "mann": "من",
    "dil_se": "دل سے",
    "jaan_se": "جان سے",
    "chaar_su": "چار سو",
    "chaar_taraf": "چار طرف",
    "ek_taraf": "ایک طرف",
    "do_pahar": "دو پہر",
    "teen_pahar": "تین پہر",
    "seh": "سہ",
    "paanch_p": "پانچ",
    "chay": "چھے",

    # dil_ruba etc.
    "dil_ruba": "دل ربا",
    "dil_fareb": "دل فریب",
    "dil_awar": "دل آوار",
    "dil_sitani": "دل ستانی",
    "dil_azeeb": "دل عذیب",
    "dil_nashiin": "دل نشیں",
    "dil_kash": "دل کش",
    "jaan_far": "جان فر",
    "jaan_nisaar": "جان نثار",
    "jaan_ba_laab": "جان با لب",
    "jaan_raba": "جان ربا",
    "jaan_sitaan": "جان ستان",
    "ruh": "روح",
    "ruhaani": "روحانی",
    "ruh_afza": "روح افزا",
    "ruh_geer": "روح گیر",
    "ruh_nawaaz": "روح نواز",
    "shab_e_furqat": "شب فرقت",
    "shab_e_hijr": "شب ہجر",
    "shab_e_vida": "شب وداع",
    "shab_e_visaal": "شب وصال",
    "subh_e_azal": "صبح ازل",
    "subh_e_ummeed": "صبح امید",
    "shaam_e_ghurbat": "شام غربت",
    "shaam_e_visaal": "شام وصال",
    "fajar": "فجر",
    "jahan": "جہاں",
    "jahan_aan": "جہاں آراء",
    "jahan_geer": "جہاں گیر",
    "jahan_numaa": "جہاں نما",
    "kainaat": "کائنات",
    "kaunain": "کونین",
    "zamaana": "زمانہ",
    "zamaane": "زمانے",
    "rauzan": "روزن",
    "raughan": "راوگن",
    "kunj": "کنج",
    "kunj_e_jigar": "کنج جگر",
    "kunj_e_dil": "کنج دل",
    "jhoomar": "جھومر",
    "jhalar": "جھالر",
    "kamar": "کمر",
    "qaba": "قبہ",
    "qabaa": "قبا",
    "taj": "تاج",
    "takht": "تخت",
    "taj_daar": "تاج دار",
    "taj_posh": "تاج پوش",
    "jalaal": "جلال",
    "jamaal": "جمال",
    "jalaal_o_jamaal": "جلال و جمال",
    "husn_o_ishq": "حسن و عشق",
    "ishq_o_mohabbat": "عشق و محبت",
    "dard_o_gham": "درد و غم",
    "aah_o_faryaad": "آہ و فریاد",
    "naala_o_fariyaad": "نالہ و فریاد",
    "lab_khama": "لب خامہ",
    "lab_goya": "لب گویا",
    "lab_basta": "لب بستہ",
    "lab_kushada": "لب کشادہ",
    "dil_basta": "دل بستہ",
    "dil_kushada": "دل کشادہ",
    "dil_tang": "دل تنگ",
    "dil_gudaaz": "ل گداز",
    "dil_saaz": "دل ساز",
    "dil_nawaaz": "دل نواز",
    "dil_nashin": "دل نشین",
    "dil_pazeer": "دل پذیر",
    "jaan_gudaaz": "جان گداز",
    "jaan_saaz": "جان ساز",
    "jaan_nawaaz": "جان نواز",
    "jaan_nishaan": "جان نشان",
    "jaan_pazeer": "جان پذیر",
    "jaan_fiza": "جان فزا",
    "jaan_afreen": "جان آفرین",
    "jaan_farsa": "جان فرسا",
    "raah_farsa": "راہ فرسا",
    "rah_e_manzil": "راہ منزل",
    "rah_e_ishq": "راہ عشق",
    "rah_e_wafa": "راہ وفا",
    "rahzan": "رہزن",
    "raah_gir": "راہ گیر",
    "raah_rau": "راہ رو",
    "raah_bin": "راہ بین",
    "raah_bar": "راہ بر",
    "raah_numa": "راہ نما",
    "raah_zan": "راہ زن",
    "raah_pai": "راہ پئے",
    "raah_o_resm": "راہ و رسم",
    "resm": "رسم",
    "riwaaj": "رواج",
    "rivayat": "روایت",
    "riwaayat": "روایت",
    "dastoor": "دستور",
    "dastoor_e_zindagi": "دستور زندگی",
    "dastoor_e_mohabbat": "دستور محبت",
    "dastoor_e_wafa": "دستور وفا",
    "dastoor_e_junoon": "دستور جنون",
    "aap_baiti": "آپ بیتی",
    "jaga_baiti": "جاگ بیتی",
    "raat_baiti": "رات بیتی",
    "din_baiti": "دن بیتی",

    # 100 new words (first batch)
    "be_khudi": "بے خودی",
    "be_hoshi": "بے ہوشی",
    "be_zabaan": "بے زبان",
    "be_asar": "بے اثر",
    "be_chain": "بے چین",
    "be_qaraar": "بے قرار",
    "be_sabab": "بے سبب",
    "be_wafa": "بے وفا",
    "be_parwah": "بے پرواہ",
    "be_gunaah": "بے گناہ",
    "be_imtihaan": "بے امتحان",
    "be_intiha": "بے انتہا",
    "be_misaal": "بے مثال",
    "be_nazar": "بے نظر",
    "be_nisha": "بے نشہ",
    "be_khata": "بے خطا",
    "be_shak": "بے شک",
    "be_khabar": "بے خبر",
    "be_hijaab": "بے حجاب",
    "be_haya": "بے حیا",
    "ba_wafa": "با وفا",
    "ba_shak": "با شک",
    "ba_khabar": "با خبر",
    "ba_hijaab": "با حجاب",
    "ba_izzat": "با عزت",
    "ba_qadar": "با قدر",
    "ba_tamaam": "با تمام",
    "ba_shaoor": "با شعور",
    "ba_hosh": "با ہوش",
    "ba_hiwaas": "با حواس",
    "dardnaak": "دردناک",
    "ghamnaak": "غمناک",
    "dil_saaz_adj": "دل ساز",
    "dil_soz": "دل سوز",
    "dil_azeem": "دل عظیم",
    "dil_pazeer_adj": "دل پذیر",
    "jaan_kah": "جان کہ",
    "jaan_bah": "جان بہ",
    "jaan_soz": "جان سوز",
    "jaan_aazaar": "جان آزار",
    "gul_andaam": "گل اندام",
    "gul_rukh": "گل رخ",
    "gul_badn": "گل بدن",
    "gul_chehra": "گل چہرہ",
    "gul_rakh": "گل رخ",
    "mah_rukh": "ماہ رخ",
    "mah_liqaa": "ماہ لقا",
    "mah_paikar": "ماہ پیکر",
    "mah_jabeen": "ماہ جبیں",
    "shab_gir": "شب گیر",
    "shab_zindagi": "شب زندگی",
    "shab_nam": "شب نم",
    "shab_zameer": "شب ضمیر",
    "subh_geer": "صبح گیر",
    "subh_dam": "صبح دم",
    "subh_naash": "صبح ناش",
    "subh_baan": "صبح بان",
    "salasil": "سلاسل",
    "zanjir": "زنجیر",
    "zabt": "ضبط",
    "zabt_naash": "ضبط ناش",
    "fana": "فنا",
    "baqa": "بقا",
    "fana_fi_Allah": "فنا فی اللہ",
    "baqa_bi_Allah": "بقا باللہ",
    "tajalli": "تجلی",
    "tajrid": "تجرد",
    "tarkeeb": "ترکیب",
    "taqreeb": "تقریب",
    "taqreer": "تقریر",
    "izhaar": "اظہار",
    "zahoor": "ظہور",
    "zameer": "ضمیر",
    "zameer_naak": "ضمیر ناک",
    "fitrat": "فطرت",
    "fitarat": "فطرت",
    "jibillat": "جبلت",
    "wijdan": "وجدان",
    "wijdani": "وجدانی",
    "raaz_o_niaz": "راز و نیاز",
    "raaz_daari": "راز داری",
    "raaz_daan": "راز دان",
    "raaz_go": "راز گو",
    "raaz_shanas": "راز شناس",
    "niyaz": "نیاز",
    "niyazmand": "نیازمند",
    "aashna": "آشنا",
    "aashnaai": "آشنائی",
    "begana": "بیگانہ",
    "beganagi": "بیگانگی",
    "ham_nawa": "ہم نوا",
    "ham_raaz": "ہم راز",
    "ham_dard": "ہم درد",
    "ham_dam": "ہم دم",
    "ham_saaya": "ہم سایہ",
    "ham_zulf": "ہم زلف",
    "ham_sukhan": "ہم سخن",
    "ham_qadam": "ہم قدم",
    "hum_nashin": "ہم نشین",
    "hum_khayal": "ہم خیال",
    "rashk": "رشک",
    "ghairat": "غیرت",
    "ghairatmand": "غیرت مند",

    # 100 NEW WORDS (second batch, no duplicates)
    "aafat": "آفت",
    "aahang": "آہنگ",
    "aaraam_dil": "آرام دل",
    "aas": "آس",
    "abroo": "آبرو",
    "ada": "ادا",
    "adab": "ادب",
    "adawat": "عداوت",
    "aesaar": "ایثار",
    "afaq": "آفاق",
    "afsurdagi": "افسردگی",
    "ahtram": "احترام",
    "aju": "اجو",
    "alam_e_gham": "عالم غم",
    "alif": "الف",
    "amaan": "امان",
    "amal": "عمل",
    "ana": "انا",
    "anmol": "انمول",
    "ard": "ارد",
    "asar": "اثر",
    "asooda": "آسودہ",
    "atish": "آتش",
    "atr": "عطر",
    "awaaz_dena": "آواز دینا",
    "azab": "عذاب",
    "baab": "باب",
    "bahaduri": "بہادری",
    "bahaar_naak": "بہار ناک",
    "bala_e_gham": "بلائے غم",
    "bandagi": "بندگی",
    "barish_naak": "بارش ناک",
    "basta": "بستہ",
    "be_noor": "بے نور",
    "be_raah": "بے راہ",
    "be_saaz": "بے ساز",
    "be_shuba": "بے شبہ",
    "be_waqt": "بے وقت",
    "buraai": "برائی",
    "chashm": "چشم",
    "dagh_naak": "داغ ناک",
    "dagh_daar": "داغ دار",
    "dard_geer": "درد گیر",
    "dardnaak_poem": "دردناک",
    "daulat": "دولت",
    "dil_kush": "دل کش",
    "dil_nawaaz_poetic": "دل نواز",
    "dua_go": "دعا گو",
    "faqeer": "فقیر",
    "fard": "فرد",
    "faza": "فضا",
    "garaj": "گرج",
    "ghair": "غیر",
    "gham_geeri": "غم گیری",
    "gham_naak": "غم ناک",
    "ghazab": "غضب",
    "ghina": "غنا",
    "gul_fam": "گل فام",
    "gul_naar": "گل نار",
    "gul_raan": "گل رعن",
    "gulshan_e_jaan": "گلشن جان",
    "haal_dil": "حال دل",
    "haalat": "حالت",
    "hijab": "حجاب",
    "hijr_naak": "ہجر ناک",
    "hum_nawa_poetic": "ہم نوا",
    "hum_raaz_poetic": "ہم راز",
    "hum_saaz": "ہم ساز",
    "husn_parast": "حسن پرست",
    "iman": "ایمان",
    "intezaar": "انتظار",
    "ishq_bazi": "عشق بازی",
    "ishq_daari": "عشق داری",
    "jaan_geeri": "جان گیری",
    "jaan_kufur": "جان کفر",
    "jaan_layaq": "جان لایق",
    "jaan_naak": "جان ناک",
    "jaan_parvar": "جان پرور",
    "jaan_pehchan": "جان پہچان",
    "jaan_sitani": "جان ستانی",
    "jaan_war": "جان ور",
    "kabood": "کبود",
    "karvaan": "کارواں",
    "kashish": "کشش",
    "kharaab": "خراب",
    "kharaab_haal": "خراب حال",
    "khushi_naak": "خوشی ناک",
    "lab_ba_lab": "لب بہ لب",
    "lab_parast": "لب پرست",
    "lab_ravez": "لب ریز",
    "lazzat": "لذت",
    "maalik": "مالک",
    "mani": "معنی",
    "maqtal": "مقتل",
    "marhaam": "مرہم",
    "mauj": "موج",
    "mayoos": "مایوس",
    "meel": "میل",
    "mehmaan": "مہمان",
    "mushkil": "مشکل",
    "mutmain": "مطمئن"
}

# =========================================================
# STOPWORDS (MUST BE DEFINED BEFORE is_generic_query)
# =========================================================
COMMON_STOPWORDS = {
    "tum", "hum", "woh", "yeh", "dil", "ishq", "raat", "mein", "hai", 
    "aap", "main", "tere", "mera", "tera", "koi", "kya", "na", "se",
    "aur", "bhi", "to", "tha", "thi", "the", "ki", "ke", "ko",
    "se", "par", "pe", "tak", "liye", "baad", "pehle"
}

def is_generic_query(keyword):
    """Return True if query is too broad (stopword-only or very short)."""
    if not keyword:
        return True
    tokens = keyword.split()
    if len(tokens) <= 2 and all(t in COMMON_STOPWORDS for t in tokens):
        return True
    if len(keyword) < 3 and keyword.lower() in COMMON_STOPWORDS:
        return True
    return False

def suggest_alternative(keyword):
    """Return a helpful suggestion for generic queries."""
    suggestions = {
        "tum": "tum aaye, tum se, tumhare",
        "hum": "hum dono, hum na the, hum bhi",
        "woh": "woh log, woh din, woh baat",
        "dil": "dil hi to hai, dil dhadakta hai",
        "ishq": "ishq ne, ishq mein, ishq hai",
        "raat": "raat gayi, raat dhal gayi",
    }
    return suggestions.get(keyword.lower(), "Try adding more words (e.g., 'tum aaye', 'woh log')")

# =========================================================
# NORMALIZATION
# =========================================================
def normalize_roman(text):
    text = text.lower().strip()
    text = text.replace("aa", "a").replace("ee", "i").replace("oo", "u")
    return text

def normalize_urdu(text):
    if not text:
        return ""
    text = text.strip()
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ة": "ہ",
        "أ": "ا",
        "إ": "ا",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def roman_to_urdu(text):
    words = text.split()
    result = []
    for w in words:
        norm = normalize_roman(w)
        if any('\u0600' <= c <= '\u06FF' for c in w):
            result.append(w)
        else:
            result.append(ROMAN_DICT.get(norm, w))
    return " ".join(result)

def extract_matla_line(text):
    if not text:
        return ""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = normalize_urdu(line)
        if len(line) >= 3:
            cleaned.append(line)
    if cleaned:
        return cleaned[0]
    return normalize_urdu(text)

# =========================================================
# HIGHLIGHTING
# =========================================================
def highlight_matches(text, keyword):
    if not text or not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)

# =========================================================
# COSINE SIMILARITY
# =========================================================
def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2 + 1e-8))

# =========================================================
# SEMANTIC SEARCH
# =========================================================
def semantic_search(query_embedding, top_n=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ge.text_id, ge.embedding_vector, t.full_text_hash
        FROM ghazal_embeddings ge
        JOIN texts t ON ge.text_id = t.id
        WHERE t.is_deleted = FALSE
          AND t.full_text_hash IS NOT NULL
          AND ge.embedding_vector IS NOT NULL
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    scored = []
    for r in rows:
        emb = r['embedding_vector']
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                continue
        if not emb:
            continue
        sim = cosine_similarity(query_embedding, emb)
        scored.append((r['text_id'], sim, r['full_text_hash']))

    scored.sort(key=lambda x: x[1], reverse=True)

    seen_hashes = set()
    filtered = []
    for tid, sim, fhash in scored:
        if fhash in seen_hashes:
            continue
        seen_hashes.add(fhash)
        filtered.append((tid, sim))

    return filtered[:top_n]

# =========================================================
# SIMPLE SEARCH FUNCTION (WORKING)
# =========================================================
def search_ghazals(filters):
    conn = get_db_connection()
    cur = conn.cursor()

    keyword = (filters.get('keyword') or '').strip()
    poet_id = filters.get('poet_id')
    contributor_id = filters.get('contributor_id')
    offset = filters.get('offset', 0)
    limit = filters.get('limit', 20)

    # Generic query protection
    if is_generic_query(keyword):
        return [], -1

    # Prepare search terms
    like_kw = f"%{keyword}%"
    urdu_kw = roman_to_urdu(keyword)
    like_ur = f"%{urdu_kw}%" if urdu_kw != keyword else like_kw

    # Build WHERE clause
    where_parts = ["COALESCE(t.is_deleted, FALSE) = FALSE"]
    params = []

    # Search conditions
    where_parts.append("""
        (t.normalized_matla ILIKE %s
         OR t.title_urdu ILIKE %s
         OR t.text_urdu ILIKE %s
         OR t.text_english ILIKE %s
         OR p.name ILIKE %s
         OR EXISTS (
             SELECT 1 FROM verses v
             WHERE v.text_id = t.id
             AND (v.misra1_urdu ILIKE %s OR v.misra2_urdu ILIKE %s)
         ))
    """)
    params.extend([like_ur, like_kw, like_kw, like_kw, like_kw, like_kw, like_kw])

    if poet_id:
        where_parts.append("t.poet_id = %s")
        params.append(poet_id)

    if contributor_id:
        where_parts.append("t.contributor_id = %s")
        params.append(contributor_id)

    where_clause = " AND ".join(where_parts)

    # Count total
    count_sql = f"""
        SELECT COUNT(DISTINCT t.id) AS total
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE {where_clause}
    """
    cur.execute(count_sql, params)
    total = cur.fetchone()['total']

    # Main query - fetch ALL columns needed for display
    query = f"""
        SELECT
            t.id,
            t.title_urdu,
            t.text_urdu,
            t.text_english,
            t.normalized_matla,
            t.form,
            COALESCE(p.name, 'Unknown') AS poet_name,
            COALESCE(p.name_urdu, '') AS poet_name_urdu,
            1 AS relevance,
            'General Match' AS match_type
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE {where_clause}
        ORDER BY t.id DESC
        LIMIT %s OFFSET %s
    """

    final_params = params + [limit, offset]
    cur.execute(query, final_params)
    results = cur.fetchall()

    # Apply highlighting AFTER fetching results
    for row in results:
        if row['text_urdu']:
            # Create highlighted version
            row['text_urdu_highlighted'] = highlight_matches(row['text_urdu'], keyword)
        else:
            row['text_urdu_highlighted'] = ''

    cur.close()
    conn.close()
    return results, total
# =========================================================
# SEARCH SUGGESTIONS
# =========================================================
def get_suggestions(query, limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    like_q = f"%{query}%"
    cur.execute("""
        SELECT DISTINCT suggestion FROM (
            SELECT normalized_matla AS suggestion FROM texts
            WHERE normalized_matla ILIKE %s AND COALESCE(is_deleted, FALSE) = FALSE
            UNION
            SELECT title_urdu FROM texts
            WHERE title_urdu ILIKE %s AND COALESCE(is_deleted, FALSE) = FALSE
            UNION
            SELECT name FROM poets
            WHERE name ILIKE %s
        ) s LIMIT %s
    """, (like_q, like_q, like_q, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r['suggestion'] for r in rows]

# =========================================================
# SMART SEARCH
# =========================================================
def smart_search(query, top_n=20):
    query_emb = generate_embedding(query)
    if not query_emb or len(query_emb) != 384:
        return []
    semantic = semantic_search(query_emb, top_n=50)
    if not semantic:
        return []
    ids = [tid for tid, _ in semantic]
    scores = {tid: score for tid, score in semantic}
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (t.id)
            t.id, t.title_urdu, p.name AS poet_name,
            v.misra1_urdu, v.misra2_urdu
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        LEFT JOIN verses v ON v.text_id = t.id
        WHERE t.id = ANY(%s) AND t.is_deleted = FALSE
        ORDER BY t.id, v.couplet_index ASC NULLS LAST
    """, (ids,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    results = []
    for r in rows:
        misra1 = r['misra1_urdu'] or ''
        misra2 = r['misra2_urdu'] or ''
        first_couplet = f"{misra1}\n{misra2}" if misra1 and misra2 else misra1
        results.append({
            "text_id": r['id'],
            "title": r['title_urdu'],
            "poet": r['poet_name'],
            "first_couplet": first_couplet,
            "score": round(scores.get(r['id'], 0), 3)
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]