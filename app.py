import os
import csv
import datetime
import shutil
import json
import secrets
import psycopg
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'deepfake_research_secret_key_change_me')

RESULTS_FILE = 'survey_responses.csv'
REWARDS_FILE = 'reward_results.csv'
DATABASE_URL = os.environ.get('DATABASE_URL')
# Set ADMIN_PASSWORD in your hosting environment for production.
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Evan')

MEDIA_SOURCES = {
    1: {'source_type': 'x', 'source_url': 'https://x.com/RajaFaisalPK/status/2033543923101319627?s=20', 'x_post_id': '2033543923101319627'},
    2: {'source_type': 'x', 'source_url': 'https://x.com/tvir_X/status/2083951574401908838?s=20', 'x_post_id': '2083951574401908838'},
    3: {'source_type': 'x', 'source_url': 'https://x.com/GarudEyeIntel/status/2057702492738310186?s=20', 'x_post_id': '2057702492738310186'},
    4: {'source_type': 'x', 'source_url': 'https://x.com/TheRubberDuck79/status/2033211923286708284?s=20', 'x_post_id': '2033211923286708284'},
    5: {'source_type': 'x', 'source_url': 'https://x.com/tvir_X/status/2083951478746620388?s=20', 'x_post_id': '2083951478746620388'},
    6: {'source_type': 'youtube', 'youtube_id': 'vui5TFU3DCM'},
    7: {'source_type': 'youtube', 'youtube_id': 'cQ54GDm1eL0'},
    8: {'source_type': 'external', 'source_url': 'https://www.bbc.com/reel/video/p0hkflt4/watch', 'source_name': 'BBC Reel'},
}

VIDEO_QUIZ = {
    1: {**MEDIA_SOURCES[1], 'answer': 'AI-Generated',
        'reason_en': 'The study answer key classifies this research clip as AI-generated. Look for inconsistencies across face movement, voice, lighting and context rather than relying on one visual clue.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို AI ဖြင့် ဖန်တီးထားသော ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ တစ်ချက်တည်းကို မယုံဘဲ မျက်နှာလှုပ်ရှားမှု၊ အသံ၊ အလင်းရောင်နှင့် အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးပါ။'},
    2: {**MEDIA_SOURCES[2], 'answer': 'AI-Generated',
        'reason_en': 'This copy uses the same verified research clip as Video 1, so the answer is also AI-generated. Repeated exposure tests whether confidence changes over time.',
        'reason_my': 'ဤကလစ်သည် ဗီဒီယို ၁ နှင့် တူညီသော သုတေသနကလစ်ဖြစ်သောကြောင့် AI ဖြင့် ဖန်တီးထားသော ဗီဒီယိုဟု သတ်မှတ်ထားသည်။ ထပ်ခါတလဲလဲ ကြည့်ရှုခြင်းကြောင့် ယုံကြည်ချက် ပြောင်းလဲမှုရှိမရှိ လေ့လာရန် အသုံးပြုထားသည်။'},
    3: {**MEDIA_SOURCES[3], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. A reliable judgement should combine visual, audio and source/context verification.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ ယုံကြည်စိတ်ချရသော ခွဲခြားမှုအတွက် ရုပ်ပုံ၊ အသံနှင့် သတင်းရင်းမြစ်/အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးသင့်သည်။'},
    4: {**MEDIA_SOURCES[3], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Natural-looking video alone is not proof; source and context verification remain important.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို အစစ်အမှန်ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ သဘာဝကျသလိုမြင်ရခြင်းတစ်ခုတည်းဖြင့် အစစ်ဟု မဆိုနိုင်သဖြင့် ရင်းမြစ်နှင့် အကြောင်းအရာကို ထပ်မံစစ်ဆေးရန် အရေးကြီးသည်။'},
    5: {**MEDIA_SOURCES[4], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Pay attention to synchronization, facial consistency and whether the claim can be verified elsewhere.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အသံနှင့် ရုပ်ပုံချိန်ညှိမှု၊ မျက်နှာပုံစံတည်ငြိမ်မှုနှင့် အခြားရင်းမြစ်များတွင် သတင်းကို အတည်ပြုနိုင်ခြင်းရှိမရှိ စစ်ဆေးပါ။'},
    6: {**MEDIA_SOURCES[5], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Correct verification depends on evidence and provenance, not on finding a single artifact.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ မှန်ကန်စွာ စစ်ဆေးရန် အထောက်အထားနှင့် ဗီဒီယိုရင်းမြစ်ကို အဓိကထားသင့်ပြီး မူမမှန်ချက်တစ်ခုတည်းကိုသာ မမှီခိုသင့်ပါ။'},
    7: {**MEDIA_SOURCES[7], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Check temporal consistency across frames as well as audio and source credibility.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ Frame များကြား တည်ငြိမ်မှု၊ အသံနှင့် ရင်းမြစ်၏ ယုံကြည်စိတ်ချရမှုကို စစ်ဆေးပါ။'},
    8: {**MEDIA_SOURCES[8], 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Real clips can still be misleading when removed from context, so authenticity and context should be checked separately.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ အစစ်အမှန်ဗီဒီယိုတစ်ခုလည်း အကြောင်းအရာမှ ဖြတ်ထုတ်ထားပါက လွဲမှားစေနိုင်သောကြောင့် စစ်မှန်မှုနှင့် အကြောင်းအရာကို သီးခြားစစ်ဆေးသင့်သည်။'},
    9: {**MEDIA_SOURCES[1], 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. The strongest verification combines media cues with trusted-source cross-checking.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အကောင်းဆုံးစစ်ဆေးနည်းမှာ မီဒီယာလက္ခဏာများနှင့် ယုံကြည်စိတ်ချရသော ရင်းမြစ်များကို နှိုင်းယှဉ်စစ်ဆေးခြင်း ဖြစ်သည်။'}
}



# Warning-label experiment. These are research conditions, not quiz items.
# IMPORTANT: Before real data collection, replace the three youtube_id values with
# three DIFFERENT clips whose AI-generated/deepfake status you have independently verified.
WARNING_EXPERIMENT = {
    1: {
        **MEDIA_SOURCES[6],
        'condition': 'reveal',
        'title_en': 'Condition 1 - Before vs After AI Label',
        'title_my': 'စမ်းသပ်အခြေအနေ ၁ - AI တံဆိပ် မပြမီနှင့် ပြပြီးနောက်',
    },
    2: {
        **MEDIA_SOURCES[7],
        'condition': 'labelled',
        'title_en': 'Condition 2 - AI Label Visible From the Start',
        'title_my': 'စမ်းသပ်အခြေအနေ ၂ - အစကတည်းက AI တံဆိပ်မြင်ရခြင်း',
    },
    3: {
        **MEDIA_SOURCES[8],
        'condition': 'labelled',
        'title_en': 'Condition 3 - Realism Challenge With AI Label',
        'title_my': 'စမ်းသပ်အခြေအနေ ၃ - AI တံဆိပ်ရှိသည့် Realism Challenge',
    },
}

# Educational videos are shown only after experimental responses are submitted,
# so they do not teach detection cues before measurement.
EDUCATIONAL_VIDEOS = [
    {'youtube_id': 'TqNXqbTUpQ8', 'source': 'The Guardian',
     'title_en': 'How AI deepfake propaganda is created and used',
     'title_my': 'AI Deepfake propaganda ကို ဖန်တီးပြီး အသုံးပြုပုံ'},
    {'youtube_id': '-kDtt0QBNRU', 'source': 'Linus Tech Tips',
     'title_en': 'How to recognize deepfakes and AI-generated video',
     'title_my': 'Deepfake နှင့် AI-generated video ကို ခွဲခြားစစ်ဆေးနည်း'},
]

REWARD_OPTIONS = [
    {'key': '3000 KS', 'label_en': '3000 KS', 'label_my': '3000 ကျပ်', 'emoji': '💵'},
    {'key': 'Fool Emoji', 'label_en': 'Fool Emoji', 'label_my': 'Fool Emoji', 'emoji': '🤡'},
    {'key': 'Good Luck Wish', 'label_en': 'A wish for good luck from the heart', 'label_my': 'စိတ်ထဲကနေ ကံကောင်းပါစေလို့ ဆုတောင်းပေးပါတယ်', 'emoji': '💫'},
    {'key': '5000 KS', 'label_en': '5000 KS', 'label_my': '5000 ကျပ်', 'emoji': '💰'},
    {'key': 'Beautiful Thank You', 'label_en': 'Thank you for answering — with a beautiful smile!', 'label_my': 'ဖြေဆိုပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ် — လှပတဲ့အပြုံးလေးနဲ့!', 'emoji': '😊'},
]

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
            'source_type': stimulus.get('source_type', 'youtube'),
            'source_url': stimulus.get('source_url', ''),
            'x_post_id': stimulus.get('x_post_id', ''),
            'youtube_id': stimulus.get('youtube_id', ''),
            'source_name': stimulus.get('source_name', '')
        })

    percent = round((correct / 9) * 100)
    return correct, 9, percent, details


@app.route('/')
def index():
    return render_template('index.html')


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
            return redirect(url_for('survey_page5'))
        session['skipped_pre_video_sections'] = False
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
        return redirect(url_for('survey_page5'))
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

    # Clips 4–6 are explicitly the same three X sources used by the score page.
    # Keeping this explicit prevents an older YouTube mapping from appearing here.
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
    required = [
        'w1_belief_before', 'w1_trust_before',
        'w1_belief_after', 'w1_realism', 'w1_trust_after', 'w1_influence_removed', 'w1_could_be_true', 'w1_realism_influence', 'w1_reaction', 'w1_reason'
    ]
    for i in (2, 3):
        required.extend([
            f'w{i}_belief_after', f'w{i}_realism', f'w{i}_trust_after', f'w{i}_influence_removed',
            f'w{i}_could_be_true', f'w{i}_realism_influence', f'w{i}_reaction', f'w{i}_reason'
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
        prize_index = secrets.randbelow(len(REWARD_OPTIONS))
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
                SELECT participant_id, submitted_at, data
                FROM survey_responses
                ORDER BY submitted_at DESC
            """)

            for participant_id, submitted_at, data in cur.fetchall():
                responses.append({
                    'participant_id': participant_id,
                    'submitted_at': submitted_at,
                    'data': data
                })

    return responses

@app.route('/admin')
@admin_required
def admin():
    """Research-focused dashboard built from participant-level responses stored in Neon."""
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
    cue_counts = {}

    section_f_count = 0
    warning_before_belief = []
    warning_after_belief = []
    warning_before_trust = []
    warning_after_trust = []
    labelled_belief_values = []
    condition_belief = {1: [], 2: [], 3: []}
    condition_realism = {1: [], 2: [], 3: []}
    condition_trust = {1: [], 2: [], 3: []}

    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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

            if cue:
                cue_counts[cue] = cue_counts.get(cue, 0) + 1

            participant_video_details.append({
                'number': i,
                'answer': answer or '—',
                'expected': expected,
                'correct': is_correct,
                'confidence': confidence if confidence is not None else '—',
                'cue': cue or '—'
            })

        b_before = safe_float(data.get('Warning_1_Belief_Before'))
        b_after = safe_float(data.get('Warning_1_Belief_After'))
        t_before = safe_float(data.get('Warning_1_Trust_Before'))
        t_after = safe_float(data.get('Warning_1_Trust_After'))

        if b_before is not None:
            warning_before_belief.append(b_before)
        if b_after is not None:
            warning_after_belief.append(b_after)
        if t_before is not None:
            warning_before_trust.append(t_before)
        if t_after is not None:
            warning_after_trust.append(t_after)

        warning_details = []
        for wi in range(1, 4):
            belief_after = safe_float(data.get(f'Warning_{wi}_Belief_After'))
            realism = safe_float(data.get(f'Warning_{wi}_Realism'))
            trust_after = safe_float(data.get(f'Warning_{wi}_Trust_After'))

            if belief_after is not None:
                labelled_belief_values.append(belief_after)
                condition_belief[wi].append(belief_after)
            if realism is not None:
                condition_realism[wi].append(realism)
            if trust_after is not None:
                condition_trust[wi].append(trust_after)

            warning_details.append({
                'number': wi,
                'belief_before': data.get(f'Warning_{wi}_Belief_Before') or '—',
                'belief_after': data.get(f'Warning_{wi}_Belief_After') or '—',
                'realism': data.get(f'Warning_{wi}_Realism') or '—',
                'trust_before': data.get(f'Warning_{wi}_Trust_Before') or '—',
                'trust_after': data.get(f'Warning_{wi}_Trust_After') or '—',
                'reaction': data.get(f'Warning_{wi}_Reaction') or '—',
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
            'avg_confidence': round(sum(participant_conf) / len(participant_conf), 2) if participant_conf else 0,
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
    avg_confidence = round(sum(all_confidence) / len(all_confidence), 2) if all_confidence else 0
    section_f_rate = round((section_f_count / total_submissions) * 100, 1) if total_submissions else 0

    avg_before_belief = round(sum(warning_before_belief) / len(warning_before_belief), 2) if warning_before_belief else 0
    avg_after_belief = round(sum(warning_after_belief) / len(warning_after_belief), 2) if warning_after_belief else 0
    avg_before_trust = round(sum(warning_before_trust) / len(warning_before_trust), 2) if warning_before_trust else 0
    avg_after_trust = round(sum(warning_after_trust) / len(warning_after_trust), 2) if warning_after_trust else 0
    belief_change = round(avg_after_belief - avg_before_belief, 2) if warning_before_belief and warning_after_belief else 0
    trust_change = round(avg_after_trust - avg_before_trust, 2) if warning_before_trust and warning_after_trust else 0
    continued_belief_rate = round((sum(1 for v in labelled_belief_values if v >= 3) / len(labelled_belief_values)) * 100, 1) if labelled_belief_values else 0

    video_labels = [f'Video {i}' for i in range(1, 10)]
    video_correct_rates = [
        round((per_video_correct[i] / per_video_answered[i]) * 100, 1) if per_video_answered[i] else 0
        for i in range(1, 10)
    ]
    video_avg_confidence = [
        round(sum(per_video_confidence[i]) / len(per_video_confidence[i]), 2) if per_video_confidence[i] else 0
        for i in range(1, 10)
    ]

    top_cues = sorted(cue_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    cue_labels = [k for k, _ in top_cues]
    cue_values = [v for _, v in top_cues]

    condition_labels = ['Condition 1', 'Condition 2', 'Condition 3']
    condition_belief_avg = [round(sum(condition_belief[i]) / len(condition_belief[i]), 2) if condition_belief[i] else 0 for i in range(1, 4)]
    condition_realism_avg = [round(sum(condition_realism[i]) / len(condition_realism[i]), 2) if condition_realism[i] else 0 for i in range(1, 4)]
    condition_trust_avg = [round(sum(condition_trust[i]) / len(condition_trust[i]), 2) if condition_trust[i] else 0 for i in range(1, 4)]

    return render_template(
        'admin.html',
        total_submissions=total_submissions,
        section_f_count=section_f_count,
        section_f_rate=section_f_rate,
        avg_score=avg_score,
        avg_confidence=avg_confidence,
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
        cue_labels=cue_labels,
        cue_values=cue_values,
        condition_labels=condition_labels,
        condition_belief_avg=condition_belief_avg,
        condition_realism_avg=condition_realism_avg,
        condition_trust_avg=condition_trust_avg,
        participant_summaries=participant_summaries,
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
