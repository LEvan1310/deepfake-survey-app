import os
import csv
import datetime
import shutil
import secrets
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'deepfake_research_secret_key_change_me')

RESULTS_FILE = 'survey_responses.csv'
REWARDS_FILE = 'reward_results.csv'
# Set ADMIN_PASSWORD in your hosting environment for production.
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Evan')

VIDEO_QUIZ = {
    1: {'youtube_id': 'cQ54GDm1eL0', 'answer': 'AI-Generated',
        'reason_en': 'The study answer key classifies this research clip as AI-generated. Look for inconsistencies across face movement, voice, lighting and context rather than relying on one visual clue.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို AI ဖြင့် ဖန်တီးထားသော ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ တစ်ချက်တည်းကို မယုံဘဲ မျက်နှာလှုပ်ရှားမှု၊ အသံ၊ အလင်းရောင်နှင့် အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးပါ။'},
    2: {'youtube_id': 'JZl3cQTL6U0', 'answer': 'AI-Generated',
        'reason_en': 'This copy uses the same verified research clip as Video 1, so the answer is also AI-generated. Repeated exposure tests whether confidence changes over time.',
        'reason_my': 'ဤကလစ်သည် ဗီဒီယို ၁ နှင့် တူညီသော သုတေသနကလစ်ဖြစ်သောကြောင့် AI ဖြင့် ဖန်တီးထားသော ဗီဒီယိုဟု သတ်မှတ်ထားသည်။ ထပ်ခါတလဲလဲ ကြည့်ရှုခြင်းကြောင့် ယုံကြည်ချက် ပြောင်းလဲမှုရှိမရှိ လေ့လာရန် အသုံးပြုထားသည်။'},
    3: {'youtube_id': 'vON7Y5MRBlw', 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. A reliable judgement should combine visual, audio and source/context verification.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ ယုံကြည်စိတ်ချရသော ခွဲခြားမှုအတွက် ရုပ်ပုံ၊ အသံနှင့် သတင်းရင်းမြစ်/အကြောင်းအရာကို ပေါင်းစပ်စစ်ဆေးသင့်သည်။'},
    4: {'youtube_id': 'C5qglgqQrnQ', 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Natural-looking video alone is not proof; source and context verification remain important.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေတွင် ဤကလစ်ကို အစစ်အမှန်ဗီဒီယိုအဖြစ် သတ်မှတ်ထားသည်။ သဘာဝကျသလိုမြင်ရခြင်းတစ်ခုတည်းဖြင့် အစစ်ဟု မဆိုနိုင်သဖြင့် ရင်းမြစ်နှင့် အကြောင်းအရာကို ထပ်မံစစ်ဆေးရန် အရေးကြီးသည်။'},
    5: {'youtube_id': 'vON7Y5MRBlw', 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Pay attention to synchronization, facial consistency and whether the claim can be verified elsewhere.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အသံနှင့် ရုပ်ပုံချိန်ညှိမှု၊ မျက်နှာပုံစံတည်ငြိမ်မှုနှင့် အခြားရင်းမြစ်များတွင် သတင်းကို အတည်ပြုနိုင်ခြင်းရှိမရှိ စစ်ဆေးပါ။'},
    6: {'youtube_id': 'C5qglgqQrnQ', 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Correct verification depends on evidence and provenance, not on finding a single artifact.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ မှန်ကန်စွာ စစ်ဆေးရန် အထောက်အထားနှင့် ဗီဒီယိုရင်းမြစ်ကို အဓိကထားသင့်ပြီး မူမမှန်ချက်တစ်ခုတည်းကိုသာ မမှီခိုသင့်ပါ။'},
    7: {'youtube_id': 'vON7Y5MRBlw', 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. Check temporal consistency across frames as well as audio and source credibility.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ Frame များကြား တည်ငြိမ်မှု၊ အသံနှင့် ရင်းမြစ်၏ ယုံကြည်စိတ်ချရမှုကို စစ်ဆေးပါ။'},
    8: {'youtube_id': 'C5qglgqQrnQ', 'answer': 'Real',
        'reason_en': 'The study answer key classifies this research clip as real. Real clips can still be misleading when removed from context, so authenticity and context should be checked separately.',
        'reason_my': 'သုတေသနအတွက် သတ်မှတ်ထားသော အဖြေမှာ အစစ်အမှန်ဗီဒီယို ဖြစ်သည်။ အစစ်အမှန်ဗီဒီယိုတစ်ခုလည်း အကြောင်းအရာမှ ဖြတ်ထုတ်ထားပါက လွဲမှားစေနိုင်သောကြောင့် စစ်မှန်မှုနှင့် အကြောင်းအရာကို သီးခြားစစ်ဆေးသင့်သည်။'},
    9: {'youtube_id': 'vON7Y5MRBlw', 'answer': 'AI-Generated',
        'reason_en': 'The configured answer is AI-generated. The strongest verification combines media cues with trusted-source cross-checking.',
        'reason_my': 'သတ်မှတ်ထားသော အဖြေမှာ AI ဖြင့် ဖန်တီးထားသော ဗီဒီယို ဖြစ်သည်။ အကောင်းဆုံးစစ်ဆေးနည်းမှာ မီဒီယာလက္ခဏာများနှင့် ယုံကြည်စိတ်ချရသော ရင်းမြစ်များကို နှိုင်းယှဉ်စစ်ဆေးခြင်း ဖြစ်သည်။'}
}



# Warning-label experiment. These are research conditions, not quiz items.
# IMPORTANT: Before real data collection, replace the three youtube_id values with
# three DIFFERENT clips whose AI-generated/deepfake status you have independently verified.
WARNING_EXPERIMENT = {
    1: {
    'youtube_id': 'vui5TFU3DCM',
    'condition': 'reveal',
    'title_en': 'Condition 1 - Before vs After AI Label',
    'title_my': 'စမ်းသပ်အခြေအနေ ၁ - AI တံဆိပ် မပြမီနှင့် ပြပြီးနောက်',
},
    2: {
        'youtube_id': 'vON7Y5MRBlw',
        'condition': 'labelled',
        'title_en': 'Condition 2 - AI Label Visible From the Start',
        'title_my': 'စမ်းသပ်အခြေအနေ ၂ - အစကတည်းက AI တံဆိပ်မြင်ရခြင်း',
    },
    3: {
        'youtube_id': 'vON7Y5MRBlw',
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
    'Timestamp', 'Name', 'Age_Group', 'Gender', 'Education_Level', 'News_Frequency', 'News_Source',
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
    if not os.path.exists(RESULTS_FILE) or os.path.getsize(RESULTS_FILE) == 0:
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(HEADERS)
        return

    with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    if not rows:
        rows = [HEADERS]
    if rows[0] == HEADERS:
        return

    # Preserve older survey data instead of rewriting it into an incompatible schema.
    legacy_file = 'survey_responses_legacy.csv'
    if not os.path.exists(legacy_file):
        shutil.copy2(RESULTS_FILE, legacy_file)
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(HEADERS)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def video_page_context(start, end):
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
        selected = data.get(f'v_real_{i}', '')
        expected = VIDEO_QUIZ[i]['answer']
        is_correct = selected == expected
        if is_correct:
            correct += 1
        details.append({
            'number': i,
            'selected': selected,
            'expected': expected,
            'correct': is_correct,
            'reason_en': VIDEO_QUIZ[i]['reason_en'],
            'reason_my': VIDEO_QUIZ[i]['reason_my'],
            'youtube_id': VIDEO_QUIZ[i]['youtube_id']
        })
    percent = round((correct / 9) * 100)
    return correct, 9, percent, details


@app.before_request
def prepare_storage():
    ensure_csv_headers()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/survey/page1', methods=['GET', 'POST'])
def survey_page1():
    if request.method == 'POST':
        session.clear()
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
    return render_template('survey_page6.html', videos=video_page_context(4, 6))


@app.route('/survey/page7', methods=['GET', 'POST'])
def survey_page7():
    if request.method == 'POST':
        session['page7'] = request.form.to_dict()
        return redirect(url_for('survey_page8'))
    return render_template('survey_page7.html', videos=video_page_context(7, 9))


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

    if p8.get('section_f_choice') == 'Participate':
        session['warning_summary'] = warning_summary(p8)
        session['section_f_completed'] = True
    else:
        session['warning_summary'] = {}
        session['section_f_completed'] = False

    row_map = {
        'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
        'Qual_Real_Or_Fake_Features': p5.get('q27', ''), 'Qual_Opinion_Effect': p5.get('q28', ''),
        'Qual_Warning_Impact': p5.get('q29', ''), 'Qual_Recommended_Actions': p5.get('q30', ''),
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

    with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([row_map.get(h, '') for h in HEADERS])
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
    new_file = not os.path.exists(REWARDS_FILE) or os.path.getsize(REWARDS_FILE) == 0
    with open(REWARDS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(['Timestamp', 'Name', 'Prize'])
        writer.writerow([
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            session.get('page1', {}).get('name', ''),
            prize['key']
        ])


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


@app.route('/admin')
@admin_required
def admin():
    responses = []
    headers = []
    real_answers = 0
    ai_answers = 0
    scores = []
    warning_before_belief = []
    warning_after_belief = []
    warning_before_trust = []
    warning_after_trust = []
    labelled_belief_values = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            hmap = {h: i for i, h in enumerate(headers)}
            for row in reader:
                if not row:
                    continue
                responses.append(row)
                for i in range(1, 10):
                    idx = hmap.get(f'Video_{i}_Classification')
                    if idx is not None and idx < len(row):
                        if row[idx] == 'Real': real_answers += 1
                        elif row[idx] == 'AI-Generated': ai_answers += 1
                sidx = hmap.get('Video_Score_Percent')
                if sidx is not None and sidx < len(row):
                    try: scores.append(float(row[sidx]))
                    except ValueError: pass

                def add_numeric(header, target):
                    idx = hmap.get(header)
                    if idx is not None and idx < len(row):
                        try: target.append(float(row[idx]))
                        except (ValueError, TypeError): pass

                add_numeric('Warning_1_Belief_Before', warning_before_belief)
                add_numeric('Warning_1_Belief_After', warning_after_belief)
                add_numeric('Warning_1_Trust_Before', warning_before_trust)
                add_numeric('Warning_1_Trust_After', warning_after_trust)
                for wi in range(1, 4):
                    add_numeric(f'Warning_{wi}_Belief_After', labelled_belief_values)

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    avg_before_belief = round(sum(warning_before_belief) / len(warning_before_belief), 2) if warning_before_belief else 0
    avg_after_belief = round(sum(warning_after_belief) / len(warning_after_belief), 2) if warning_after_belief else 0
    avg_before_trust = round(sum(warning_before_trust) / len(warning_before_trust), 2) if warning_before_trust else 0
    avg_after_trust = round(sum(warning_after_trust) / len(warning_after_trust), 2) if warning_after_trust else 0
    continued_belief_rate = round((sum(1 for v in labelled_belief_values if v >= 3) / len(labelled_belief_values)) * 100, 1) if labelled_belief_values else 0

    return render_template('admin.html', responses=responses, headers=headers,
                           total_submissions=len(responses), real_answers=real_answers,
                           ai_answers=ai_answers, avg_score=avg_score,
                           avg_before_belief=avg_before_belief, avg_after_belief=avg_after_belief,
                           avg_before_trust=avg_before_trust, avg_after_trust=avg_after_trust,
                           continued_belief_rate=continued_belief_rate)


if __name__ == '__main__':
    ensure_csv_headers()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)