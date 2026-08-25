import os
import csv
import datetime
import shutil
import json
import io
import secrets
import psycopg
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, Response
 
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'deepfake_research_secret_key_change_me')
 
RESULTS_FILE = 'survey_responses.csv'
REWARDS_FILE = 'reward_results.csv'
DATABASE_URL = os.environ.get('DATABASE_URL')
# Set ADMIN_PASSWORD in your hosting environment for production.
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Evan')
 
# Nine main quiz clips. The quiz and result page use this exact same mapping.
# Clips 2 and 5 are the two Deepfake Label Video Tests. The quiz and result page use this exact same mapping.
QUIZ_MEDIA = {
    1: {
        'source_type': 'google_drive',
        'drive_id': '1ZSJa6MhzvghxAJrGg0NUwdME-Y7UDHNn',
        'source_url': 'https://drive.google.com/file/d/1ZSJa6MhzvghxAJrGg0NUwdME-Y7UDHNn/view?usp=drive_link',
        'source_name': 'Research Video 1',
    },
    2: {
        'source_type': 'google_drive',
        'drive_id': '1yjAF6BDHo3jIaqfPVemMQQrkhqfd15v2',
        'source_url': 'https://drive.google.com/file/d/1yjAF6BDHo3jIaqfPVemMQQrkhqfd15v2/view?usp=drive_link',
        'source_name': 'Deepfake Label Video Test 1',
    },
    3: {
        'source_type': 'google_drive',
        'drive_id': '1B98b2FuRr_Uf8mPbisjKuqEq4Iugstrx',
        'source_url': 'https://drive.google.com/file/d/1B98b2FuRr_Uf8mPbisjKuqEq4Iugstrx/view?usp=drive_link',
        'source_name': 'Research Video 3',
    },
    4: {
        'source_type': 'google_drive',
        'drive_id': '1SIozzMnIBB8vqHFTJIewkEawUsUkRFBk',
        'source_url': 'https://drive.google.com/file/d/1SIozzMnIBB8vqHFTJIewkEawUsUkRFBk/view?usp=drive_link',
        'source_name': 'Research Video 4',
    },
    5: {
        'source_type': 'google_drive',
        'drive_id': '1-aB2OSfdTGI32NSh2H3YSkaM8O3oIdn1',
        'source_url': 'https://drive.google.com/file/d/1-aB2OSfdTGI32NSh2H3YSkaM8O3oIdn1/view?usp=drive_link',
        'source_name': 'Deepfake Label Video Test 2',
    },
    6: {
        'source_type': 'google_drive',
        'drive_id': '1ndoYEAOc4XhdGJG_nGVF0eiLpgPdWB4u',
        'source_url': 'https://drive.google.com/file/d/1ndoYEAOc4XhdGJG_nGVF0eiLpgPdWB4u/view?usp=drive_link',
        'source_name': 'Research Video 6',
    },
    7: {
        'source_type': 'google_drive',
        'drive_id': '1WPjhWQ7FZ0VzewKnIjIaq7-mbcCpI2ot',
        'source_url': 'https://drive.google.com/file/d/1WPjhWQ7FZ0VzewKnIjIaq7-mbcCpI2ot/view?usp=sharing',
        'source_name': 'Research Video 7',
    },
    8: {
        'source_type': 'google_drive',
        'drive_id': '1BIFCYw-d_LZwXoGqEuEiy1osGEFWzvsD',
        'source_url': 'https://drive.google.com/file/d/1BIFCYw-d_LZwXoGqEuEiy1osGEFWzvsD/view?usp=drive_link',
        'source_name': 'Research Video 8',
    },
    9: {
        'source_type': 'google_drive',
        'drive_id': '182dif0WszgHb6Icla3MzJsIc6TX3VvIV',
        'source_url': 'https://drive.google.com/file/d/182dif0WszgHb6Icla3MzJsIc6TX3VvIV/view?usp=drive_link',
        'source_name': 'Research Video 9',
    },
}
 
def drive_media(drive_id, source_name='Research Video'):
    return {
        'source_type': 'google_drive',
        'drive_id': drive_id,
        'source_url': f'https://drive.google.com/file/d/{drive_id}/view',
        'source_name': source_name,
    }
 
VIDEO_QUIZ = {
    1: {**QUIZ_MEDIA[1], 'answer': 'AI-Generated',
        'reason_en': 'The study answer key classifies this clip as AI-generated. Look for inconsistencies across face movement, voice, lighting and context rather than relying on one visual clue.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို AI ဖြင့် ဖန်တီးထားသော ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ တစ်ချက်တည်းကို မယုံဘဲ မျက်နှာလှုပ်ရှားမှု၊ အသံ၊ အလင်းရောင်နှင့် အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးပါ။'},
    2: {**QUIZ_MEDIA[2], 'answer': 'AI-Generated',
        'reason_en': 'The study answer key classifies this clip as AI-generated. Compare facial movement, audio synchronization, lighting, frame consistency and source/context evidence.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ မျက်နှာလှုပ်ရှားမှု၊ အသံနှင့်ရုပ်ပုံ ချိန်ညှိမှု၊ အလင်းရောင်၊ frame များ၏ တည်ငြိမ်မှုနှင့် ရင်းမြစ်/အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးပါ။'},
    3: {**QUIZ_MEDIA[3], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. A reliable judgement should combine visual, audio and source/context verification.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ ယုံကြည်စိတ်ချရသော ခွဲခြားမှုအတွက် ရုပ်ပုံ၊ အသံနှင့် သတင်းရင်းမြစ်/အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးသင့်သည်။'},
    4: {**QUIZ_MEDIA[4], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this clip as real. Natural-looking video alone is not proof; source and context verification remain important.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို အစစ်အမှန်ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ သဘာဝကျသလိုမြင်ရခြင်းတစ်ခုတည်းဖြင့် အစစ်ဟု မဆိုနိုင်သဖြင့် ရင်းမြစ်နှင့် အကြောင်းအရာကို ထပ်မံစစ်ဆေးရန် အရေးကြီးသည်။'},
    5: {**QUIZ_MEDIA[5], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Pay attention to synchronization, facial consistency and whether the claim can be verified elsewhere.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အသံနှင့် ရုပ်ပုံချိန်ညှိမှု၊ မျက်နှာပုံစံတည်ငြိမ်မှုနှင့် အခြားရင်းမြစ်များတွင် သတင်းကို အတည်ပြုနိုင်ခြင်းရှိမရှိ စစ်ဆေးပါ။'},
    6: {**QUIZ_MEDIA[6], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this clip as real. Correct verification depends on evidence and provenance, not on finding a single artifact.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ မှန်ကန်စွာ စစ်ဆေးရန် အထောက်အထားနှင့် ဗီဒီယိုရင်းမြစ်ကို အဓိကထားသင့်ပြီး မူမမှန်ချက်တစ်ခုတည်းကိုသာ မမှီခိုသင့်ပါ။'},
    7: {**QUIZ_MEDIA[7], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Check temporal consistency across frames as well as audio and source credibility.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ Frame များကြား တည်ငြိမ်မှု၊ အသံနှင့် ရင်းမြစ်၏ ယုံကြည်စိတ်ချရမှုကို စစ်ဆေးပါ။'},
    8: {**QUIZ_MEDIA[8], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this clip as real. Real clips can still be misleading when removed from context, so authenticity and context should be checked separately.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ အစစ်အမှန်ဗီဒီယိုတစ်ခုလည်း အကြောင်းအရာမှ ဖြတ်ထုတ်ထားပါက လွဲမှားစေနိုင်သောကြောင့် စစ်မှန်မှုနှင့် အကြောင်းအရာကို သီးခြားစစ်ဆေးသင့်သည်။'},
    9: {**QUIZ_MEDIA[9], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. The strongest verification combines media cues with trusted-source cross-checking.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အကောင်းဆုံးစစ်ဆေးနည်းမှာ မီဒီယာလက္ခဏာများနှင့် ယုံကြည်စိတ်ချရသော ရင်းမြစ်များကို နှိုင်းယှဉ်စစ်ဆေးခြင်း ဖြစ်သည်။'}
}
 
# Warning-label videos are intentionally separate from the nine main quiz clips.
WARNING_EXPERIMENT = {
    1: {
        'source_type': 'youtube',
        'youtube_id': 'vui5TFU3DCM',
        'source_url': 'https://www.youtube.com/watch?v=vui5TFU3DCM',
        'source_name': 'YouTube',
        'condition': 'reveal',
        'title_en': 'Condition 1 - Before vs After AI Label',
        'title_my': 'စမ်းသပ်အခြေအနေ ၁ - AI တံဆိပ် မပြမီနှင့် ပြပြီးနောက်',
    },
    2: {
        'source_type': 'youtube',
        'youtube_id': 'cQ54GDm1eL0',
        'source_url': 'https://www.youtube.com/watch?v=cQ54GDm1eL0',
        'source_name': 'YouTube',
        'condition': 'labelled',
        'title_en': 'Condition 2 - AI Label Visible From the Start',
        'title_my': 'စမ်းသပ်အခြေအနေ ၂ - အစကတည်းက AI တံဆိပ်မြင်ရခြင်း',
    },
    3: {
        'source_type': 'external',
        'source_url': 'https://www.bbc.com/reel/video/p0hkflt4/watch',
        'source_name': 'BBC Reel',
        'condition': 'labelled',
        'title_en': 'Condition 3 - Realism Challenge With AI Label',
        'title_my': 'စမ်းသပ်အခြေအနေ ၃ - AI တံဆိပ်ရှိသည့် Realism Challenge',
    },
}
 
# Educational recommendation videos are also kept separate.
EDUCATIONAL_VIDEOS = [
    {
        'source_type': 'youtube',
        'youtube_id': 'TqNXqbTUpQ8',
        'source_url': 'https://www.youtube.com/watch?v=TqNXqbTUpQ8',
        'source': 'The Guardian',
        'title_en': 'How AI deepfake propaganda is created and used',
        'title_my': 'AI Deepfake propaganda ကို ဖန်တီးပြီး အသုံးပြုပုံ',
    },
    {
        'source_type': 'youtube',
        'youtube_id': '-kDtt0QBNRU',
        'source_url': 'https://www.youtube.com/watch?v=-kDtt0QBNRU',
        'source': 'Linus Tech Tips',
        'title_en': 'How to recognize deepfakes and AI-generated video',
        'title_my': 'Deepfake နှင့် AI-generated video ကို ခွဲခြားစစ်ဆေးနည်း',
    },
]
 
REWARD_OPTIONS = [
    {'key': '😊 ဒီတစ်ခါ ငွေသားဆု မရသေးပါ။ စစ်တမ်းမှာ ပါဝင်ဖြေဆိုပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်။', 'label_en': '😊 ဒီတစ်ခါ ငွေသားဆု မရသေးပါ။ စစ်တမ်းမှာ ပါဝင်ဖြေဆိုပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်။', 'label_my': '😊 ဒီတစ်ခါ ငွေသားဆု မရသေးပါ။ စစ်တမ်းမှာ ပါဝင်ဖြေဆိုပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်။!', 'emoji': '', 'weight': 30},
    {'key': '1000 KS', 'label_en': '1,000 KS', 'label_my': '1,000 ကျပ် ဆုရပါပြီ!', 'emoji': '💰', 'weight': 20},
    {'key': '3000 KS', 'label_en': '3,000 KS', 'label_my': '💵 3,000 ကျပ် ဆုရပါပြီ!', 'emoji': '🎊', 'weight': 2},
    {'key': '✨ ဒီတစ်ခါ ဆုမကျသေးပါ — လှည့်ကြည့်ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်!', 'label_en': '✨ ဒီတစ်ခါ ဆုမကျသေးပါ — လှည့်ကြည့်ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်!', 'label_my': '✨ ဒီတစ်ခါ ဆုမကျသေးပါ — လှည့်ကြည့်ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်!', 'emoji': '😊', 'weight': 28},
    {'key': '🎊 ဒီတစ်ခါတော့ ငွေသားဆု မကျသေးပါ။ နောက်တစ်ကြိမ်မှာ ကံကောင်းပါစေ!', 'label_en': '🎊 ဒီတစ်ခါတော့ ငွေသားဆု မကျသေးပါ။ နောက်တစ်ကြိမ်မှာ ကံကောင်းပါစေ!', 'label_my': '🎊 ဒီတစ်ခါတော့ ငွေသားဆု မကျသေးပါ။ နောက်တစ်ကြိမ်မှာ ကံကောင်းပါစေ!', 'emoji': '✨', 'weight': 20},
]
# 'weight' = relative odds, not a percent. With the values above, 3,000 KS is
# picked about 2 times out of 100 spins on average. Raise or lower any single
# weight to change that prize's odds relative to the others — they don't need
# to add up to 100, they just need to be in proportion to each other.
 
 
def weighted_reward_index():
    """Pick a reward index using each option's 'weight' instead of a flat
    1-in-N chance, so rare prizes (like 3,000 KS) can be made unlikely while
    still occasionally possible. Uses `secrets` so it stays unpredictable."""
    weights = [item.get('weight', 1) for item in REWARD_OPTIONS]
    total = sum(weights)
    roll = secrets.randbelow(total)
    running_total = 0
    for index, weight in enumerate(weights):
        running_total += weight
        if roll < running_total:
            return index
    return len(REWARD_OPTIONS) - 1
 
HEADERS = [
    'Timestamp', 'Participant_ID', 'Name', 'Age_Group', 'Gender', 'Education_Level', 'News_Frequency', 'News_Source',
    'Watched_Deepfake_Before', 'Heard_Deepfake', 'Deepfake_Description', 'Suspected_Deepfake_Before',
    'Confidence_Identifying', 'Suspicious_Signs',
    'Political_Video_Authenticity', 'Media_Authenticity_Confidence', 'Deepfake_Believability',
    'Physical_Realism', 'Political_Leader_Trust', 'Opinion_Change', 'Voting_Influence',
    'Social_Media_Trust', 'Election_Fairness_Concern', 'Election_Trust_Reduction', 'War_News_Believability',
    'Post_Warning_Belief', 'Post_Warning_Believability', 'Post_Warning_Trustworthiness',
    'Warning_Effectiveness', 'Action_After_Warning',
    'Qual_Real_Or_Fake_Features', 'Qual_Opinion_Effect', 'Qual_Warning_Impact', 'Qual_Recommended_Actions',
    'Section_F_Participation'
]
for i in range(1, 10):
    HEADERS.extend([f'Video_{i}_Classification', f'Video_{i}_Confidence', f'Video_{i}_Cue'])
for i in range(1, 4):
    HEADERS.extend([
        f'Warning_{i}_Belief_Before', f'Warning_{i}_Trust_Before',
        f'Warning_{i}_Belief_After', f'Warning_{i}_Realism', f'Warning_{i}_Trust_After',
        f'Warning_{i}_Influence_Removed', f'Warning_{i}_Could_Be_True',
        f'Warning_{i}_Realism_Influence', f'Warning_{i}_Reaction', f'Warning_{i}_Reason'
    ])
HEADERS.extend(['Video_Score_Correct', 'Video_Score_Total', 'Video_Score_Percent'])
 
 
def ensure_csv_headers():
    """Create/migrate the CSV while preserving older participant responses."""
    if not os.path.exists(RESULTS_FILE) or os.path.getsize(RESULTS_FILE) == 0:
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(HEADERS)
        return
 
    with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    if not rows:
        rows = [HEADERS]
    old_headers = rows[0]
    if old_headers == HEADERS:
        return
 
    # Keep a backup, then map every existing column into the new schema.
    legacy_file = 'survey_responses_legacy.csv'
    if not os.path.exists(legacy_file):
        shutil.copy2(RESULTS_FILE, legacy_file)
 
    old_index = {h: i for i, h in enumerate(old_headers)}
    migrated = []
    for row_number, row in enumerate(rows[1:], start=1):
        if not row:
            continue
        new_row = []
        for header in HEADERS:
            if header == 'Participant_ID':
                idx = old_index.get(header)
                existing = row[idx] if idx is not None and idx < len(row) else ''
                new_row.append(existing or f'LEGACY-{row_number:04d}')
            else:
                idx = old_index.get(header)
                new_row.append(row[idx] if idx is not None and idx < len(row) else '')
        migrated.append(new_row)
 
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(migrated)
 
 
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped
 
 
def video_page_context(start, end):
    # IMPORTANT: The quiz pages and the result page use this SAME VIDEO_QUIZ
    # configuration. This guarantees Video 1 in the quiz is Video 1 in results,
    # Video 2 is Video 2, and so on through Video 9.
    return {i: VIDEO_QUIZ[i] for i in range(start, end + 1)}
 
 
def calculate_quiz():
    details = []
    correct = 0
 
    for i in range(1, 10):
        if i <= 3:
            data = session.get('page5', {})
        elif i <= 6:
            data = session.get('page6', {})
        else:
            data = session.get('page7', {})
 
        # Use the exact same configured stimulus used on the quiz page.
        stimulus = VIDEO_QUIZ[i]
        selected = data.get(f'v_real_{i}', '')
        expected = stimulus['answer']
        is_correct = selected == expected
        if is_correct:
            correct += 1
 
        details.append({
            'number': i,
            'selected': selected,
            'expected': expected,
            'correct': is_correct,
            'reason_en': stimulus.get('reason_en', ''),
            'reason_my': stimulus.get('reason_my', ''),
            # Preserve the exact media identifiers so the result page embeds
            # the same clip that the participant saw in the quiz.
            'source_type': stimulus.get('source_type', 'youtube'),
            'source_url': stimulus.get('source_url', ''),
            'drive_id': stimulus.get('drive_id', ''),
            'x_post_id': stimulus.get('x_post_id', ''),
            'youtube_id': stimulus.get('youtube_id', ''),
            'source_name': stimulus.get('source_name', '')
        })
 
    percent = round((correct / 9) * 100)
    return correct, 9, percent, details
 
 
@app.route('/')
def index():
    return render_template('index.html')
 
 
@app.route('/consent')
def consent():
    return render_template('consent.html')
 
 
@app.route('/quiz-introduction')
def quiz_intro():
    return render_template('quiz_intro.html', skipped=session.get('skipped_pre_video_sections', False))
 
 
@app.route('/awareness-training/1')
def awareness_training_1():
    phase = session.get('awareness_phase')
    if phase == 'pre_quiz':
        # Both Yes and No paths can use the same awareness module BEFORE the quiz.
        watched = session.get('page2', {}).get('watched_deepfake_before')
        back_url = url_for('survey_page2') if watched == 'No' else url_for('survey_page4')
    else:
        if 'reflection' not in session:
            return redirect(url_for('survey_reflection'))
        back_url = url_for('survey_reflection')
    return render_template('awareness_training_1.html', back_url=back_url)
 
 
@app.route('/awareness-training/2')
def awareness_training_2():
    phase = session.get('awareness_phase')
    if phase != 'pre_quiz' and 'reflection' not in session:
        return redirect(url_for('survey_reflection'))
    return render_template('awareness_training_2.html')
 
 
@app.route('/awareness-training/3')
def awareness_training_3():
    phase = session.get('awareness_phase')
    if phase == 'pre_quiz':
        next_url = url_for('quiz_intro')
        next_en = 'Continue to Video Assessment →'
        next_my = 'ဗီဒီယို စမ်းသပ်မှုသို့ ဆက်သွားရန် →'
    else:
        if 'reflection' not in session:
            return redirect(url_for('survey_reflection'))
        next_url = url_for('survey_page8')
        next_en = 'Continue to Warning-Label Section →'
        next_my = 'သတိပေးတံဆိပ်အပိုင်းသို့ ဆက်သွားရန် →'
    return render_template('awareness_training_3.html', next_url=next_url, next_en=next_en, next_my=next_my)
 
 
@app.route('/survey/page1', methods=['GET', 'POST'])
def survey_page1():
    if request.method == 'POST':
        session.clear()
        # Anonymous tracking ID used by the research dashboard to connect one
        # respondent's quiz, warning-label and demographic answers without
        # relying on their name as the primary identifier.
        session['participant_id'] = 'DF-' + secrets.token_hex(4).upper()
        session['page1'] = request.form.to_dict()
        return redirect(url_for('survey_page2'))
    return render_template('survey_page1.html')
 
 
@app.route('/survey/page2', methods=['GET', 'POST'])
def survey_page2():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['suspicious_signs'] = ', '.join(request.form.getlist('suspicious_signs'))
        watched = form_data.get('watched_deepfake_before', '')
        # The first gate question must be answered before any later logic can run.
        if watched not in {'Yes', 'No'}:
            return redirect(url_for('survey_page2'))
        session['page2'] = form_data
        if watched == 'No':
            session['skipped_pre_video_sections'] = True
            # Participants with no previous deepfake exposure receive the
            # three short awareness pages before the video assessment.
            session['awareness_phase'] = 'pre_quiz'
            return redirect(url_for('awareness_training_1'))
        session['skipped_pre_video_sections'] = False
        session.pop('awareness_phase', None)
        return redirect(url_for('survey_page3'))
    return render_template('survey_page2.html')
 
 
@app.route('/survey/page3', methods=['GET', 'POST'])
def survey_page3():
    if request.method == 'POST':
        session['page3'] = request.form.to_dict()
        return redirect(url_for('survey_page4'))
    return render_template('survey_page3.html')
 
 
@app.route('/survey/page4', methods=['GET', 'POST'])
def survey_page4():
    if request.method == 'POST':
        session['page4'] = request.form.to_dict()
 
        # Yes path: after Sections C and D, show awareness ONCE before the quiz.
        session['awareness_phase'] = 'pre_quiz'
        return redirect(url_for('awareness_training_1'))
 
    return render_template('survey_page4.html')
 
 
@app.route('/survey/page5', methods=['GET', 'POST'])
def survey_page5():
    if request.method == 'POST':
        session['page5'] = request.form.to_dict()
        return redirect(url_for('survey_page6'))
    return render_template('survey_page5.html', videos=video_page_context(1, 3), skipped=session.get('skipped_pre_video_sections', False))
 
 
@app.route('/survey/page6', methods=['GET', 'POST'])
def survey_page6():
    if request.method == 'POST':
        session['page6'] = request.form.to_dict()
        return redirect(url_for('survey_page7'))
 
    # Clips 4–6 come directly from VIDEO_QUIZ, so the quiz and result page always match.
    videos = {
        4: VIDEO_QUIZ[4],
        5: VIDEO_QUIZ[5],
        6: VIDEO_QUIZ[6],
    }
    return render_template('survey_page6.html', videos=videos)
 
 
@app.route('/survey/page7', methods=['GET', 'POST'])
def survey_page7():
    if request.method == 'POST':
        session['page7'] = request.form.to_dict()
 
        # Freeze the quiz result immediately after all 9 clips are answered.
        # calculate_quiz() uses the exact media snapshot shown during the quiz,
        # so the result page displays the same 9 clips the participant answered.
        correct, total, percent, details = calculate_quiz()
        session['quiz_correct'] = correct
        session['quiz_total'] = total
        session['quiz_percent'] = percent
        session['quiz_details'] = details
 
        return redirect(url_for('survey_reflection'))
    return render_template('survey_page7.html', videos=video_page_context(7, 9))
 
 
@app.route('/survey/reflection', methods=['GET', 'POST'])
def survey_reflection():
    if 'page7' not in session:
        return redirect(url_for('survey_page7'))
 
    if request.method == 'POST':
        session['reflection'] = request.form.to_dict()
 
        # The 3-page awareness module is now completed BEFORE the quiz
        # for both Yes and No participants, so never show it again here.
        session.pop('awareness_phase', None)
        return redirect(url_for('survey_page8'))
 
    return render_template('survey_reflection.html', previous=session.get('reflection', {}))
 
 
def warning_summary(data):
    before_belief = data.get('w1_belief_before', '')
    after_belief = data.get('w1_belief_after', '')
    before_trust = data.get('w1_trust_before', '')
    after_trust = data.get('w1_trust_after', '')
 
    def delta(a, b):
        try:
            return int(b) - int(a)
        except (TypeError, ValueError):
            return None
 
    return {
        'before_belief': before_belief,
        'after_belief': after_belief,
        'belief_delta': delta(before_belief, after_belief),
        'before_trust': before_trust,
        'after_trust': after_trust,
        'trust_delta': delta(before_trust, after_trust),
        'labelled_2_belief': data.get('w2_belief_after', ''),
        'labelled_2_realism': data.get('w2_realism', ''),
        'labelled_3_belief': data.get('w3_belief_after', ''),
        'labelled_3_realism': data.get('w3_realism', ''),
    }
 
 
def save_survey_response():
    # Prefer the frozen result created immediately after Video 9.
    # Fall back to calculation only for an older/incomplete session.
    if 'quiz_details' in session:
        correct = session.get('quiz_correct', 0)
        total = session.get('quiz_total', 9)
        percent = session.get('quiz_percent', 0)
        details = session.get('quiz_details', [])
    else:
        correct, total, percent, details = calculate_quiz()
        session['quiz_correct'] = correct
        session['quiz_total'] = total
        session['quiz_percent'] = percent
        session['quiz_details'] = details
 
    p1 = session.get('page1', {})
    p2 = session.get('page2', {})
    p3 = session.get('page3', {})
    p4 = session.get('page4', {})
    p5 = session.get('page5', {})
    p6 = session.get('page6', {})
    p7 = session.get('page7', {})
    p8 = session.get('page8', {})
    reflection = session.get('reflection', {})
 
    if p8.get('section_f_choice') == 'Participate':
        session['warning_summary'] = warning_summary(p8)
        session['section_f_completed'] = True
    else:
        session['warning_summary'] = {}
        session['section_f_completed'] = False
 
    row_map = {
        'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Participant_ID': session.get('participant_id', ''),
        'Name': p1.get('name', ''), 'Age_Group': p1.get('age_group', ''), 'Gender': p1.get('gender', ''),
        'Education_Level': p1.get('education_level', ''), 'News_Frequency': p1.get('news_frequency', ''), 'News_Source': p1.get('news_source', ''),
        'Watched_Deepfake_Before': p2.get('watched_deepfake_before', ''), 'Heard_Deepfake': p2.get('heard_deepfake', ''),
        'Deepfake_Description': p2.get('deepfake_description', ''), 'Suspected_Deepfake_Before': p2.get('suspected_deepfake_before', ''),
        'Confidence_Identifying': p2.get('confidence_identifying', ''), 'Suspicious_Signs': p2.get('suspicious_signs', ''),
        'Political_Video_Authenticity': p3.get('video_real_immediate', ''), 'Media_Authenticity_Confidence': p3.get('confidence_immediate', ''),
        'Deepfake_Believability': p3.get('believability', ''), 'Physical_Realism': p3.get('realism', ''),
        'Political_Leader_Trust': p3.get('figure_trustworthiness', ''), 'Opinion_Change': p3.get('opinion_change', ''),
        'Voting_Influence': p3.get('voting_influence', ''), 'Social_Media_Trust': p3.get('social_media_trust', ''),
        'Election_Fairness_Concern': p3.get('election_fairness_concern', ''), 'Election_Trust_Reduction': p3.get('election_trust_reduction', ''),
        'War_News_Believability': p3.get('war_believability', ''),
        'Post_Warning_Belief': p4.get('post_warning_belief', ''), 'Post_Warning_Believability': p4.get('post_warning_believability', ''),
        'Post_Warning_Trustworthiness': p4.get('post_warning_trustworthiness', ''), 'Warning_Effectiveness': p4.get('warning_effectiveness', ''),
        'Action_After_Warning': p4.get('action_after_warning', ''),
        'Qual_Real_Or_Fake_Features': reflection.get('q27', ''), 'Qual_Opinion_Effect': reflection.get('q28', ''),
        'Qual_Warning_Impact': reflection.get('q29', ''), 'Qual_Recommended_Actions': reflection.get('q30', ''),
        'Section_F_Participation': p8.get('section_f_choice', 'Skip'),
        'Video_Score_Correct': str(correct), 'Video_Score_Total': str(total), 'Video_Score_Percent': str(percent)
    }
    for i in range(1, 10):
        page_data = p5 if i <= 3 else (p6 if i <= 6 else p7)
        row_map[f'Video_{i}_Classification'] = page_data.get(f'v_real_{i}', '')
        row_map[f'Video_{i}_Confidence'] = page_data.get(f'v_confidence_{i}', '')
        row_map[f'Video_{i}_Cue'] = page_data.get(f'v_cue_{i}', '')
    for i in range(1, 4):
        row_map[f'Warning_{i}_Belief_Before'] = p8.get(f'w{i}_belief_before', '')
        row_map[f'Warning_{i}_Trust_Before'] = p8.get(f'w{i}_trust_before', '')
        row_map[f'Warning_{i}_Belief_After'] = p8.get(f'w{i}_belief_after', '')
        row_map[f'Warning_{i}_Realism'] = p8.get(f'w{i}_realism', '')
        row_map[f'Warning_{i}_Trust_After'] = p8.get(f'w{i}_trust_after', '')
        row_map[f'Warning_{i}_Influence_Removed'] = p8.get(f'w{i}_influence_removed', '')
        row_map[f'Warning_{i}_Could_Be_True'] = p8.get(f'w{i}_could_be_true', '')
        row_map[f'Warning_{i}_Realism_Influence'] = p8.get(f'w{i}_realism_influence', '')
        row_map[f'Warning_{i}_Reaction'] = p8.get(f'w{i}_reaction', '')
        row_map[f'Warning_{i}_Reason'] = p8.get(f'w{i}_reason', '')
 
    participant_id = get_participant_id()
 
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO survey_responses
                    (participant_id, data)
                VALUES
                    (%s, %s::jsonb)
                ON CONFLICT (participant_id)
                DO UPDATE SET
                    data = EXCLUDED.data,
                    submitted_at = CURRENT_TIMESTAMP
                """,
                (
                    participant_id,
                    json.dumps(row_map)
                )
            )
 
        conn.commit()
 
    session['survey_saved'] = True
 
 
def validate_section_f(form):
    # All three labelled clips now use the same five visible questions (original questions 1, 2, 5, 6 and 7).
    # The legacy before-label fields are hidden/blank for database compatibility
    # and must NOT be required, otherwise the form loops back forever.
    required = []
    for i in (1, 2, 3):
        required.extend([
            f'w{i}_belief_after', f'w{i}_realism',
            f'w{i}_could_be_true', f'w{i}_realism_influence', f'w{i}_reaction'
        ])
    return [field for field in required if not str(form.get(field, '')).strip()]
 
 
@app.route('/survey/page8', methods=['GET', 'POST'])
def survey_page8():
    if 'page7' not in session:
        return redirect(url_for('survey_page7'))
    if 'reflection' not in session:
        return redirect(url_for('survey_reflection'))
    error = None
    if request.method == 'POST':
        choice = request.form.get('section_f_choice', '')
        if choice not in {'Participate', 'Skip'}:
            error = 'choose_section_f'
        elif choice == 'Skip':
            session['page8'] = {'section_f_choice': 'Skip'}
            save_survey_response()
            return redirect(url_for('results_page'))
        else:
            missing = validate_section_f(request.form)
            if missing:
                error = 'complete_section_f'
            else:
                form_data = request.form.to_dict()
                form_data['section_f_choice'] = 'Participate'
                session['page8'] = form_data
                save_survey_response()
                return redirect(url_for('reward_page'))
    return render_template('survey_page8.html', experiments=WARNING_EXPERIMENT, error=error)
 
 
def save_reward(prize):
    if not DATABASE_URL:
        return
 
    participant_id = get_participant_id()
 
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reward_results (participant_id, name, prize)
                VALUES (%s, %s, %s)
                ON CONFLICT (participant_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    prize = EXCLUDED.prize,
                    submitted_at = CURRENT_TIMESTAMP
                """,
                (
                    participant_id,
                    session.get('page1', {}).get('name', ''),
                    prize['key']
                )
            )
        conn.commit()
 
 
@app.route('/reward', methods=['GET', 'POST'])
def reward_page():
    if not session.get('section_f_completed'):
        return redirect(url_for('results_page'))
 
    prize = None
    prize_index = None
    if session.get('reward_key'):
        for idx, item in enumerate(REWARD_OPTIONS):
            if item['key'] == session['reward_key']:
                prize = item
                prize_index = idx
                break
    elif request.method == 'POST':
        prize_index = weighted_reward_index()
        prize = REWARD_OPTIONS[prize_index]
        session['reward_key'] = prize['key']
        save_reward(prize)
 
    return render_template('reward.html', rewards=REWARD_OPTIONS, prize=prize, prize_index=prize_index)
 
 
@app.route('/results')
def results_page():
    if 'quiz_details' not in session:
        return redirect(url_for('index'))
    return render_template('results.html',
                           correct=session.get('quiz_correct', 0),
                           total=session.get('quiz_total', 9),
                           percent=session.get('quiz_percent', 0),
                           details=session.get('quiz_details', []),
                           warning=session.get('warning_summary', {}),
                           educational_videos=EDUCATIONAL_VIDEOS)
 
 
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        error = 'invalid'
    return render_template('admin_login.html', error=error)
 
 
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))
    
def get_all_responses():
    responses = []
 
    if not DATABASE_URL:
        return responses
 
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.participant_id, s.submitted_at, s.data, COALESCE(r.prize, '')
                FROM survey_responses AS s
                LEFT JOIN reward_results AS r ON r.participant_id = s.participant_id
                ORDER BY s.submitted_at DESC
            """)
 
            for participant_id, submitted_at, data, prize in cur.fetchall():
                responses.append({
                    'participant_id': participant_id,
                    'submitted_at': submitted_at,
                    'data': data,
                    'prize': prize or ''
                })
 
    return responses
 
@app.route('/admin')
@admin_required
def admin():
    """Research dashboard: descriptive analysis of participant-level deepfake study data."""
    responses = get_all_responses()
    participant_summaries = []

    total_real_answers = 0
    total_ai_answers = 0
    total_unsure_answers = 0
    scores = []
    all_confidence = []
    per_video_correct = {i: 0 for i in range(1, 10)}
    per_video_answered = {i: 0 for i in range(1, 10)}
    per_video_confidence = {i: [] for i in range(1, 10)}
    per_video_classifications = {i: {'Real': 0, 'AI-Generated': 0, 'Not sure': 0} for i in range(1, 10)}
    per_video_high_conf_wrong = {i: 0 for i in range(1, 10)}
    per_video_high_conf_answered = {i: 0 for i in range(1, 10)}
    cue_stats = {}

    section_f_count = 0
    warning_before_belief = []
    warning_after_belief = []
    warning_before_trust = []
    warning_after_trust = []
    labelled_belief_values = []
    condition_belief = {1: [], 2: [], 3: []}
    condition_realism = {1: [], 2: [], 3: []}
    condition_trust = {1: [], 2: [], 3: []}
    condition_could_be_true = {1: [], 2: [], 3: []}
    condition_realism_influence = {1: [], 2: [], 3: []}
    condition_reactions = {1: {}, 2: {}, 3: {}}

    # Group-level data used for research questions.
    experience_scores = {'Yes': [], 'No': []}
    news_scores = {}
    age_scores = {}
    education_scores = {}
    prior_awareness_scores = {'Yes': [], 'No': []}
    prior_suspicion_scores = {'Yes': [], 'No': []}
    gender_scores = {}

    # Section C / D descriptive responses.
    pre_believability = []
    pre_realism = []
    pre_voting_influence = []
    warning_effectiveness_counts = {}
    warning_action_counts = {}
    post_warning_belief_counts = {}
    post_warning_trust_counts = {}

    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def avg(values):
        return round(sum(values) / len(values), 2) if values else 0

    def map_scale(value, mapping):
        if value is None:
            return None
        return mapping.get(str(value))

    # Explicit mappings preserve the questionnaire's wording while making
    # ordinal Likert-style responses chartable on a common 1–5 scale.
    believability_map = {
        'Very unbelievable': 1, 'Unbelievable': 2, 'Neutral': 3,
        'Believable': 4, 'Very believable': 5
    }
    voting_map = {
        'Very unlikely': 1, 'Unlikely': 2, 'Neutral': 3,
        'Likely': 4, 'Very likely': 5
    }

    for response in responses:
        participant_id = response['participant_id']
        submitted_at = response['submitted_at']
        data = response['data'] or {}

        name = data.get('Name') or '—'
        watched_before = data.get('Watched_Deepfake_Before') or '—'
        section_f = data.get('Section_F_Participation') or 'Skip'
        if section_f == 'Participate':
            section_f_count += 1

        score_correct = data.get('Video_Score_Correct') or '0'
        score_total = data.get('Video_Score_Total') or '9'
        score_percent = safe_float(data.get('Video_Score_Percent'))
        score_value = safe_float(score_correct)
        if score_percent is not None:
            scores.append(score_percent)

        participant_video_details = []
        participant_conf = []

        for i in range(1, 10):
            answer = data.get(f'Video_{i}_Classification', '')
            confidence = safe_float(data.get(f'Video_{i}_Confidence'))
            cue = data.get(f'Video_{i}_Cue', '')
            expected = VIDEO_QUIZ[i]['answer']
            is_correct = answer == expected if answer else False

            if answer:
                per_video_answered[i] += 1
                if answer in per_video_classifications[i]:
                    per_video_classifications[i][answer] += 1
                if is_correct:
                    per_video_correct[i] += 1
                if answer == 'Real':
                    total_real_answers += 1
                elif answer == 'AI-Generated':
                    total_ai_answers += 1
                elif answer == 'Not sure':
                    total_unsure_answers += 1

            if confidence is not None:
                per_video_confidence[i].append(confidence)
                all_confidence.append(confidence)
                participant_conf.append(confidence)
                if confidence >= 4 and answer:
                    per_video_high_conf_answered[i] += 1
                    if not is_correct:
                        per_video_high_conf_wrong[i] += 1

            if cue:
                cue_stats.setdefault(cue, {'count': 0, 'correct': 0})
                cue_stats[cue]['count'] += 1
                if is_correct:
                    cue_stats[cue]['correct'] += 1

            participant_video_details.append({
                'number': i,
                'answer': answer or '—',
                'expected': expected,
                'correct': is_correct,
                'confidence': confidence if confidence is not None else '—',
                'cue': cue or '—'
            })

        # Research-question grouping variables.
        if watched_before in experience_scores and score_value is not None:
            experience_scores[watched_before].append(score_value)
        for field, target in [('News_Frequency', news_scores), ('Age_Group', age_scores),
                              ('Education_Level', education_scores), ('Gender', gender_scores)]:
            value = data.get(field)
            if value and score_value is not None:
                target.setdefault(value, []).append(score_value)
        for field, target in [('Heard_Deepfake', prior_awareness_scores),
                              ('Suspected_Deepfake_Before', prior_suspicion_scores)]:
            value = data.get(field)
            if value in target and score_value is not None:
                target[value].append(score_value)

        # Section C: pre-exposure perception.
        b = map_scale(data.get('Deepfake_Believability'), believability_map)
        r = safe_float(data.get('Physical_Realism'))
        v = map_scale(data.get('Voting_Influence'), voting_map)
        if b is not None: pre_believability.append(b)
        if r is not None: pre_realism.append(r)
        if v is not None: pre_voting_influence.append(v)

        # Section D: warning label expectations.
        effectiveness = data.get('Warning_Effectiveness')
        if effectiveness:
            warning_effectiveness_counts[effectiveness] = warning_effectiveness_counts.get(effectiveness, 0) + 1
        post_belief = data.get('Post_Warning_Belief')
        if post_belief:
            post_warning_belief_counts[post_belief] = post_warning_belief_counts.get(post_belief, 0) + 1
        post_trust = data.get('Post_Warning_Trustworthiness')
        if post_trust:
            post_warning_trust_counts[post_trust] = post_warning_trust_counts.get(post_trust, 0) + 1
        actions = data.get('Action_After_Warning', '')
        if actions:
            for action in [x.strip() for x in str(actions).split(',') if x.strip()]:
                warning_action_counts[action] = warning_action_counts.get(action, 0) + 1

        b_before = safe_float(data.get('Warning_1_Belief_Before'))
        b_after = safe_float(data.get('Warning_1_Belief_After'))
        t_before = safe_float(data.get('Warning_1_Trust_Before'))
        t_after = safe_float(data.get('Warning_1_Trust_After'))
        if b_before is not None: warning_before_belief.append(b_before)
        if b_after is not None: warning_after_belief.append(b_after)
        if t_before is not None: warning_before_trust.append(t_before)
        if t_after is not None: warning_after_trust.append(t_after)

        warning_details = []
        for wi in range(1, 4):
            belief_after = safe_float(data.get(f'Warning_{wi}_Belief_After'))
            realism = safe_float(data.get(f'Warning_{wi}_Realism'))
            trust_after = safe_float(data.get(f'Warning_{wi}_Trust_After'))
            could_be_true = safe_float(data.get(f'Warning_{wi}_Could_Be_True'))
            realism_influence = safe_float(data.get(f'Warning_{wi}_Realism_Influence'))
            reaction = data.get(f'Warning_{wi}_Reaction') or '—'

            if belief_after is not None:
                labelled_belief_values.append(belief_after)
                condition_belief[wi].append(belief_after)
            if realism is not None: condition_realism[wi].append(realism)
            if trust_after is not None: condition_trust[wi].append(trust_after)
            if could_be_true is not None: condition_could_be_true[wi].append(could_be_true)
            if realism_influence is not None: condition_realism_influence[wi].append(realism_influence)
            if reaction != '—':
                condition_reactions[wi][reaction] = condition_reactions[wi].get(reaction, 0) + 1

            warning_details.append({
                'number': wi,
                'belief_before': data.get(f'Warning_{wi}_Belief_Before') or '—',
                'belief_after': data.get(f'Warning_{wi}_Belief_After') or '—',
                'realism': data.get(f'Warning_{wi}_Realism') or '—',
                'trust_before': data.get(f'Warning_{wi}_Trust_Before') or '—',
                'trust_after': data.get(f'Warning_{wi}_Trust_After') or '—',
                'could_be_true': data.get(f'Warning_{wi}_Could_Be_True') or '—',
                'realism_influence': data.get(f'Warning_{wi}_Realism_Influence') or '—',
                'reaction': reaction,
                'reason': data.get(f'Warning_{wi}_Reason') or '—'
            })

        participant_summaries.append({
            'id': participant_id,
            'name': name,
            'timestamp': data.get('Timestamp') or (submitted_at.strftime('%Y-%m-%d %H:%M:%S') if submitted_at else '—'),
            'age_group': data.get('Age_Group') or '—',
            'gender': data.get('Gender') or '—',
            'education': data.get('Education_Level') or '—',
            'watched_before': watched_before,
            'score_correct': score_correct,
            'score_total': score_total,
            'score_percent': round(score_percent, 1) if score_percent is not None else 0,
            'avg_confidence': avg(participant_conf),
            'section_f': section_f,
            'belief_before': b_before if b_before is not None else '—',
            'belief_after': b_after if b_after is not None else '—',
            'belief_change': round(b_after - b_before, 2) if b_before is not None and b_after is not None else '—',
            'trust_before': t_before if t_before is not None else '—',
            'trust_after': t_after if t_after is not None else '—',
            'trust_change': round(t_after - t_before, 2) if t_before is not None and t_after is not None else '—',
            'videos': participant_video_details,
            'warnings': warning_details,
        })

    total_submissions = len(participant_summaries)
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    avg_confidence = avg(all_confidence)
    section_f_rate = round((section_f_count / total_submissions) * 100, 1) if total_submissions else 0
    median_score = round(sorted(scores)[len(scores)//2] if scores and len(scores) % 2 else ((sorted(scores)[len(scores)//2 - 1] + sorted(scores)[len(scores)//2]) / 2 if scores else 0), 1)

    score_distribution = [sum(1 for p in participant_summaries if p['score_correct'] == str(i)) for i in range(10)]
    # If an older record stores a numeric value with formatting, fall back to numeric parsing.
    if sum(score_distribution) != total_submissions:
        score_distribution = []
        for i in range(10):
            score_distribution.append(sum(1 for p in participant_summaries if safe_float(p['score_correct']) == i))

    video_labels = [f'Video {i}' for i in range(1, 10)]
    video_correct_rates = [round((per_video_correct[i] / per_video_answered[i]) * 100, 1) if per_video_answered[i] else 0 for i in range(1, 10)]
    video_avg_confidence = [avg(per_video_confidence[i]) for i in range(1, 10)]
    video_classification_real = [per_video_classifications[i]['Real'] for i in range(1, 10)]
    video_classification_ai = [per_video_classifications[i]['AI-Generated'] for i in range(1, 10)]
    video_classification_unsure = [per_video_classifications[i]['Not sure'] for i in range(1, 10)]
    high_conf_wrong_rates = [round((per_video_high_conf_wrong[i] / per_video_high_conf_answered[i]) * 100, 1) if per_video_high_conf_answered[i] else 0 for i in range(1, 10)]

    # Rank the videos from hardest to easiest for a research-friendly table/chart.
    video_rank = sorted(zip(video_labels, video_correct_rates), key=lambda x: x[1])
    video_rank_labels = [x[0] for x in video_rank]
    video_rank_rates = [x[1] for x in video_rank]

    top_cues = sorted(cue_stats.items(), key=lambda kv: kv[1]['count'], reverse=True)[:10]
    cue_labels = [k for k, _ in top_cues]
    cue_values = [v['count'] for _, v in top_cues]
    cue_accuracy = [round((v['correct'] / v['count']) * 100, 1) if v['count'] else 0 for _, v in top_cues]

    def grouped_average(group_dict, preferred_order=None):
        keys = [k for k in (preferred_order or []) if k in group_dict]
        keys += [k for k in group_dict if k not in keys]
        return keys, [avg(group_dict[k]) for k in keys], [len(group_dict[k]) for k in keys]

    exp_labels, exp_avg, exp_n = grouped_average(experience_scores, ['Yes', 'No'])
    news_order = ['Daily', 'Several times a week', 'Weekly', 'Less than weekly', 'Rarely/Never']
    news_labels, news_avg, news_n = grouped_average(news_scores, news_order)
    age_labels, age_avg, age_n = grouped_average(age_scores, ['Under 18', '18-24', '25-34', '35-44', '45+'])
    edu_labels, edu_avg, edu_n = grouped_average(education_scores)
    aware_labels, aware_avg, aware_n = grouped_average(prior_awareness_scores, ['Yes', 'No'])
    suspicion_labels, suspicion_avg, suspicion_n = grouped_average(prior_suspicion_scores, ['Yes', 'No'])

    condition_labels = ['Labelled Clip 1', 'Labelled Clip 2', 'Labelled Clip 3']
    condition_belief_avg = [avg(condition_belief[i]) for i in range(1, 4)]
    condition_realism_avg = [avg(condition_realism[i]) for i in range(1, 4)]
    condition_trust_avg = [avg(condition_trust[i]) for i in range(1, 4)]
    condition_true_avg = [avg(condition_could_be_true[i]) for i in range(1, 4)]
    condition_realism_influence_avg = [avg(condition_realism_influence[i]) for i in range(1, 4)]

    # Warning reaction categories across the three labelled clips.
    reaction_order = [
        'Knew fake and did not believe',
        'Some parts believable',
        'Realism caused uncertainty',
        'Still affected opinion',
        'Would verify claims'
    ]
    reaction_labels = reaction_order
    reaction_values = [sum(condition_reactions[i].get(r, 0) for i in range(1, 4)) for r in reaction_order]

    avg_before_belief = avg(warning_before_belief)
    avg_after_belief = avg(warning_after_belief)
    avg_before_trust = avg(warning_before_trust)
    avg_after_trust = avg(warning_after_trust)
    belief_change = round(avg_after_belief - avg_before_belief, 2) if warning_before_belief and warning_after_belief else 0
    trust_change = round(avg_after_trust - avg_before_trust, 2) if warning_before_trust and warning_after_trust else 0
    continued_belief_rate = round((sum(1 for v in labelled_belief_values if v >= 3) / len(labelled_belief_values)) * 100, 1) if labelled_belief_values else 0

    # Overall calibration: high confidence is defined descriptively as 4–5/5.
    high_conf_wrong = 0
    high_conf_total = 0
    for p in participant_summaries:
        for v in p['videos']:
            c = safe_float(v['confidence'])
            if c is not None and c >= 4:
                high_conf_total += 1
                if not v['correct']:
                    high_conf_wrong += 1
    high_conf_wrong_rate = round((high_conf_wrong / high_conf_total) * 100, 1) if high_conf_total else 0

    return render_template(
        'admin.html',
        total_submissions=total_submissions,
        section_f_count=section_f_count,
        section_f_rate=section_f_rate,
        avg_score=avg_score,
        median_score=median_score,
        avg_confidence=avg_confidence,
        high_conf_wrong_rate=high_conf_wrong_rate,
        real_answers=total_real_answers,
        ai_answers=total_ai_answers,
        unsure_answers=total_unsure_answers,
        avg_before_belief=avg_before_belief,
        avg_after_belief=avg_after_belief,
        avg_before_trust=avg_before_trust,
        avg_after_trust=avg_after_trust,
        belief_change=belief_change,
        trust_change=trust_change,
        continued_belief_rate=continued_belief_rate,
        video_labels=video_labels,
        video_correct_rates=video_correct_rates,
        video_avg_confidence=video_avg_confidence,
        video_classification_real=video_classification_real,
        video_classification_ai=video_classification_ai,
        video_classification_unsure=video_classification_unsure,
        high_conf_wrong_rates=high_conf_wrong_rates,
        video_rank_labels=video_rank_labels,
        video_rank_rates=video_rank_rates,
        score_distribution=score_distribution,
        cue_labels=cue_labels,
        cue_values=cue_values,
        cue_accuracy=cue_accuracy,
        exp_labels=exp_labels, exp_avg=exp_avg, exp_n=exp_n,
        news_labels=news_labels, news_avg=news_avg, news_n=news_n,
        age_labels=age_labels, age_avg=age_avg, age_n=age_n,
        edu_labels=edu_labels, edu_avg=edu_avg, edu_n=edu_n,
        aware_labels=aware_labels, aware_avg=aware_avg, aware_n=aware_n,
        suspicion_labels=suspicion_labels, suspicion_avg=suspicion_avg, suspicion_n=suspicion_n,
        pre_believability_avg=avg(pre_believability),
        pre_realism_avg=avg(pre_realism),
        pre_voting_influence_avg=avg(pre_voting_influence),
        warning_effectiveness_labels=list(warning_effectiveness_counts.keys()),
        warning_effectiveness_values=list(warning_effectiveness_counts.values()),
        post_warning_belief_labels=list(post_warning_belief_counts.keys()),
        post_warning_belief_values=list(post_warning_belief_counts.values()),
        post_warning_trust_labels=list(post_warning_trust_counts.keys()),
        post_warning_trust_values=list(post_warning_trust_counts.values()),
        warning_action_labels=list(warning_action_counts.keys()),
        warning_action_values=list(warning_action_counts.values()),
        condition_labels=condition_labels,
        condition_belief_avg=condition_belief_avg,
        condition_realism_avg=condition_realism_avg,
        condition_trust_avg=condition_trust_avg,
        condition_true_avg=condition_true_avg,
        condition_realism_influence_avg=condition_realism_influence_avg,
        reaction_labels=reaction_labels,
        reaction_values=reaction_values,
        participant_summaries=participant_summaries,
    )


@app.route('/admin/export.csv')
@admin_required
def admin_export_csv():
    """Export all participant-level survey fields for statistical analysis."""
    responses = get_all_responses()
    rows = []
    all_columns = set()

    for response in responses:
        data = response.get('data') or {}
        row = {
            'Participant_ID': response.get('participant_id', ''),
            'Submitted_At': response.get('submitted_at').isoformat() if response.get('submitted_at') else '',
            'Reward': response.get('prize', '') or '',
        }
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value, ensure_ascii=False)
            else:
                row[key] = value
        rows.append(row)
        all_columns.update(row.keys())

    preferred = [
        'Participant_ID', 'Submitted_At', 'Name', 'Age_Group', 'Gender',
        'Education_Level', 'News_Frequency', 'News_Source',
        'Watched_Deepfake_Before', 'Heard_Deepfake', 'Suspected_Deepfake_Before',
        'Video_Score_Correct', 'Video_Score_Total', 'Video_Score_Percent',
        'Section_F_Participation', 'Reward'
    ]
    columns = [c for c in preferred if c in all_columns]
    columns += sorted(all_columns - set(columns))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=deepfake_research_analysis.csv'}
    )


def init_database():
    if not DATABASE_URL:
        print("DATABASE_URL is not configured.")
        return
 
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS survey_responses (
                    id SERIAL PRIMARY KEY,
                    participant_id VARCHAR(50) UNIQUE NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSONB NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reward_results (
                    id SERIAL PRIMARY KEY,
                    participant_id VARCHAR(50) UNIQUE NOT NULL,
                    name TEXT,
                    prize TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
 
 
def get_participant_id():
    if 'participant_id' not in session:
        session['participant_id'] = 'DF-' + secrets.token_hex(4).upper()
 
    return session['participant_id']
 
 
init_database()
 
 
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5001)),
        debug=False
    )
