# modules/ai_tools.py
import re
from typing import Optional, List

# ------------------------------------------------------------
# MarianMT (offline AI translation)
# ------------------------------------------------------------
try:
    from transformers import MarianMTModel, MarianTokenizer
    import torch

    MODEL_NAME = "Helsinki-NLP/opus-mt-ur-en"
    tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
    model = MarianMTModel.from_pretrained(MODEL_NAME)
    USE_MARIAN = True
    print("🔥 MarianMT model loaded successfully")
except Exception as e:
    USE_MARIAN = False
    print(f"⚠️ MarianMT failed to load: {e}. Falling back to Google/dictionary.")

# ------------------------------------------------------------
# Google Translate (optional, used if Marian fails)
# ------------------------------------------------------------
try:
    from deep_translator import GoogleTranslator
    USE_DEEP = True
    print("✅ Using Google Translate as fallback.")
except ImportError:
    USE_DEEP = False
    print("⚠️ deep-translator not installed. Google fallback disabled.")

# ------------------------------------------------------------
# Fallback dictionary
# ------------------------------------------------------------
URDU_DICT = {
    'دل': 'heart', 'ہے': 'is', 'تو': 'you', 'نہ': 'not',
    'سنگ': 'stone', 'خشت': 'brick', 'درد': 'pain', 'بھر': 'fill',
    'آئے': 'come', 'کیوں': 'why', 'روئیں': 'weep', 'ہم': 'we',
    'ہزار': 'thousand', 'بار': 'times', 'کوئی': 'someone',
    'ستائے': 'torment', 'غم': 'sorrow', 'حیات': 'life',
    'کا': 'of', 'مزا': 'pleasure', 'مجھے': 'me', 'بتائے': 'tell',
    'دھڑکنے': 'beating', 'سبب': 'reason', 'پوچھے': 'ask',
    'جائے': 'go', 'عشق': 'love', 'نے': 'has', 'غالب': 'Ghalib',
    'نکما': 'useless', 'کر': 'do', 'دیا': 'gave', 'ورنہ': 'otherwise',
    'آدمی': 'man', 'تھے': 'were', 'کام': 'work', 'کے': 'of',
    'خدا': 'god', 'رب': 'lord', 'دنیا': 'world', 'زندگی': 'life',
    'موت': 'death', 'آنکھ': 'eye', 'لب': 'lip', 'چاند': 'moon',
    'ستارہ': 'star', 'صبح': 'morning', 'شام': 'evening', 'رات': 'night',
    'یاد': 'memory', 'انتظار': 'waiting', 'سفر': 'journey', 'منزل': 'destination',
    'وفا': 'loyalty', 'آسمان': 'sky', 'زمین': 'earth', 'پانی': 'water',
    'آگ': 'fire', 'ہوا': 'air', 'پھول': 'flower', 'محبت': 'love',
    'دوست': 'friend', 'غمگین': 'sad', 'خوش': 'happy', 'صبر': 'patience',
    'قیس': 'Qais', 'لیلیٰ': 'Laila', 'عشق': 'love', 'آشفتہ': 'distraught',
    'سری': 'head', 'چھوڑا': 'left', 'بادہ': 'wine', 'کش': 'drinker',
    'گلشن': 'garden', 'لب': 'lips', 'بیٹھے': 'sit', 'عہد': 'era',
    'گل': 'flower', 'ختم': 'ended', 'ٹوٹ': 'broke', 'ساز': 'instrument',
    'چمن': 'garden', 'تھا': 'was', 'عجب': 'wonderful', 'تیرے': 'your',
    'جہاں': 'world', 'منظر': 'scene', 'پر': 'on', 'تیرا': 'your',
    'نام': 'name', 'تلوار': 'sword', 'اٹھائی': 'raised', 'کس': 'who',
    'نے': 'did', 'تھی': 'was', 'کچھ': 'some', 'تیغ': 'sword',
    'زنی': 'strike', 'اپنی': 'own', 'حکومت': 'government', 'کی': 'of',
    'ہیبت': 'awe', 'صنم': 'idol', 'سہمے': 'fearful', 'رہتے': 'remain',
    'امتیں': 'nations', 'اور': 'and', 'بھی': 'also', 'ان': 'them',
    'میں': 'in', 'گنہگار': 'sinner', 'پھر': 'then', 'یہ': 'this',
    'آزردگی': 'annoyance', 'غیر': 'other', 'سبب': 'reason', 'کیا': 'what',
    'معنی': 'meaning', 'وادی': 'valley', 'نجد': 'Najd', 'شور': 'noise',
    'سلاسل': 'chains', 'نہ': 'not', 'رہا': 'remained', 'جوئے': 'stream',
    'خوں': 'blood', 'حسرت': 'longing', 'دیرینہ': 'ancient', 'پرانی': 'old',
    'روشیں': 'ways', 'باغ': 'garden', 'ویراں': 'deserted', 'ہوئیں': 'became',
    'چاک': 'torn', 'بلبل': 'nightingale', 'تنہا': 'alone', 'نوا': 'melody',
    'بت': 'idol', 'صنم': 'idol', 'خانوں': 'houses', 'کہتے': 'say',
    'مسلمان': 'Muslims', 'گئے': 'went', 'ستاروں': 'stars', 'آگے': 'beyond',
    'جہاں': 'world', 'اور': 'and', 'بھی': 'also', 'ہیں': 'are'
}

PHRASE_DICT = {
    'دل ہی تو ہے': 'the heart is',
    'نہ سنگ و خشت': 'not stone or brick',
    'درد سے بھر': 'filled with pain',
    'ہزار بار': 'a thousand times',
    'کوئی ہمیں ستائے': 'someone torments us',
    'ہم نے مانا': 'we admit',
    'کہ تغافل نہ کرو گے': 'that you will not ignore',
    'خاک ہو جائیں گے': 'will turn to dust',
    'تم کو خبر ہونے تک': 'until you know',
    'یہ نہ تھی ہماری قسمت': 'this was not our destiny',
    'کہ وصال یار ہوتا': 'that we would meet the beloved',
    'اگر اور جیتے رہتے': 'if we had lived longer',
    'یہی انتظار ہوتا': 'this is what we waited for',
    'درد لیلیٰ بھی وہی قیس کا پہلو بھی وہی': 'The pain of Laila is the same, the side of Qais is the same',
    'عشق کو عشق کی آشفتہ سری کو چھوڑا': 'Love left the distraught head of love',
    'بادہ کش غیر ہیں گلشن میں لب جو بیٹھے': 'Wine‑drinkers are others; the lips that sit in the garden',
    'عہد گل ختم ہوا ٹوٹ گیا ساز چمن': 'The era of the flower ended, the instrument of the garden broke',
    'ہم سے پہلے تھا عجب تیرے جہاں کا منظر': 'Before us, the scene of your world was wonderful',
    'پر ترے نام پہ تلوار اٹھائی کس نے': 'But who raised the sword in your name?',
    'تھی نہ کچھ تیغ زنی اپنی حکومت کے لیے': 'There was no sword‑striking for one’s own rule',
    'کس کی ہیبت سے صنم سہمے ہوئے رہتے تھے': 'From whose awe did the idols remain fearful?',
    'امتیں اور بھی ہیں ان میں گنہ گار بھی ہیں': 'There are other nations, and among them are sinners too',
    'پھر یہ آزردگی غیر سبب کیا معنی': 'Then what does this annoyance without reason mean?',
    'وادی نجد میں وہ شور سلاسل نہ رہا': 'In the valley of Najd, that noise of chains did not remain',
    'جوئے خوں می چکد از حسرت دیرینۂ ما': 'The stream of blood flows from the longing of our old days',
    'وہ پرانی روشیں باغ کی ویراں بھی ہوئیں': 'Those old ways of the garden have become desolate too',
    'چاک اس بلبل تنہا کی نوا سے دل ہوں': 'The hearts are torn by the melody of this lonely nightingale',
    'بت صنم خانوں میں کہتے ہیں مسلمان گئے': 'In idol houses, they say the Muslims have gone',
    'ستاروں سے آگے جہاں اور بھی ہیں': 'Beyond the stars, there are other worlds too'
}

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def normalize_text(text):
    if not text:
        return ""
    return ' '.join(text.strip().split())

def is_mostly_urdu(text: str) -> bool:
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total = len(text)
    return urdu_chars / total > 0.3 if total > 0 else False

def fallback_translate(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    if text in PHRASE_DICT:
        return PHRASE_DICT[text]
    words = text.split()
    translated = []
    for word in words:
        translated.append(URDU_DICT.get(word, word))
    return ' '.join(translated)

def clean_translation(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = text.replace(" is of", "")
    text = text.replace(" of is", "")
    text = text.replace("  ", " ")
    if len(text) > 1:
        text = text[0].upper() + text[1:]
    return text

# ------------------------------------------------------------
# MarianMT translation
# ------------------------------------------------------------
def marian_translate(text: str) -> str:
    if not USE_MARIAN:
        return ""
    try:
        inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            translated = model.generate(**inputs, max_length=128)
        result = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        return result.strip()
    except Exception as e:
        print(f"⚠️ Marian error: {e}")
        return ""

def batch_marian_translate(texts: List[str]) -> List[str]:
    if not USE_MARIAN:
        return []
    try:
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            translated = model.generate(**inputs, max_length=128)
        return tokenizer.batch_decode(translated, skip_special_tokens=True)
    except Exception as e:
        print(f"⚠️ Batch Marian error: {e}")
        return []

# ------------------------------------------------------------
# Main translation function (priority: Marian -> Google -> dict)
# ------------------------------------------------------------
def translate_urdu_to_english(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""

    # If text is mostly English, return as is
    if not is_mostly_urdu(text):
        return text

    # 1. Phrase dictionary
    if text in PHRASE_DICT:
        return PHRASE_DICT[text]

    # 2. MarianMT (primary)
    if USE_MARIAN:
        result = marian_translate(text)
        if result and not is_mostly_urdu(result):
            return clean_translation(result)

    # 3. Google Translate (if available)
    if USE_DEEP:
        try:
            from deep_translator import GoogleTranslator
            result = GoogleTranslator(source='ur', target='en').translate(text)
            if result and not is_mostly_urdu(result):
                return clean_translation(result)
        except Exception as e:
            print(f"⚠️ Google error: {e}")

    # 4. Fallback dictionary
    fallback = fallback_translate(text)
    if fallback and len(fallback.split()) > 2:
        return clean_translation(fallback)

    return "[Translation unavailable]"

def batch_translate(texts: List[str]) -> List[str]:
    if USE_MARIAN:
        results = batch_marian_translate(texts)
        if results:
            # Post-process each result
            cleaned = [clean_translation(r) for r in results]
            return cleaned
    # Fallback to individual translation
    return [translate_urdu_to_english(t) for t in texts]

# ------------------------------------------------------------
# Language detection (unchanged)
# ------------------------------------------------------------
def detect_language(text: str) -> str:
    if not text:
        return 'unknown'
    urdu_chars = 0
    roman_chars = 0
    for c in text:
        if '\u0600' <= c <= '\u06FF':
            urdu_chars += 1
        elif c.isalpha() and c.isascii():
            roman_chars += 1
    total = len([c for c in text if c.isalpha()])
    if total == 0:
        return 'unknown'
    urdu_ratio = urdu_chars / total
    roman_ratio = roman_chars / total
    if urdu_ratio > 0.3:
        return 'urdu'
    elif roman_ratio > 0.5:
        return 'roman'
    else:
        return 'mixed'

def is_urdu(text: str) -> bool:
    return detect_language(text) == 'urdu'

def is_roman_urdu(text: str) -> bool:
    return detect_language(text) == 'roman'

# ------------------------------------------------------------
# Class for compatibility
# ------------------------------------------------------------
class AITools:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def translate_urdu_to_english(self, urdu_text: str) -> Optional[str]:
        return translate_urdu_to_english(urdu_text)

    def batch_translate(self, texts: List[str]) -> List[str]:
        return batch_translate(texts)

    def detect_language(self, text: str) -> str:
        return detect_language(text)

# Create instance for import
ai_tools = AITools()