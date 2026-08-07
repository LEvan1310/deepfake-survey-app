Deepfake Warning & Continued-Belief Experiment

New flow:
1. Detection quiz (Videos 1–9)
2. Warning-label experiment
   - Condition 1: participant rates believability/trust BEFORE the AI label, then reveals the label and answers post-label questions.
   - Condition 2: AI label visible from the start.
   - Condition 3: realism challenge with AI label visible.
3. Results page compares before/after belief and trust, then shows an educational debrief.
4. Admin Dashboard calculates aggregate before/after averages and a descriptive continued-belief rate (post-label believability >= 3/5).

IMPORTANT BEFORE REAL DATA COLLECTION:
The three warning-experiment conditions currently reuse the project's already-configured AI research clip so the workflow works immediately.
For a stronger experiment, replace WARNING_EXPERIMENT youtube_id values in app.py with THREE DIFFERENT AI-generated/deepfake clips whose status you have independently verified.
Do not label an unverified real-world clip as AI-generated.

Educational debrief videos are placed AFTER responses so they do not teach detection cues before measurement.

V4 OPTIONAL SECTION F + GIFT WHEEL
----------------------------------
- Sections A-E now show an estimated completion time on the demographic page.
- Section F is optional. A respondent can skip it and still complete the survey.
- If the respondent chooses Section F, all Section F questions are required; server-side validation also prevents incomplete submission.
- Completing Section F unlocks one gift-wheel spin.
- The wheel has five equal-probability (20% each) outcomes: 3000 KS, Fool Emoji, Good Luck Wish, 5000 KS, and Thank You/Beautiful Smile.
- The random result is generated on the Flask server using Python's secrets module and is stored in reward_results.csv.
- One result is stored in the respondent's session, preventing repeat spins in the same survey session.

RESEARCH / ETHICS NOTE
----------------------
If the 3000 KS and 5000 KS outcomes are real cash incentives, clearly disclose the incentive rules, eligibility, odds, how prizes are claimed/paid, and any limits in your participant information/consent materials. Obtain any instructor/ethics approval required by your institution before data collection.
