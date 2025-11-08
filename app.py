from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import requests
import secrets
import json
import os
import uuid
from werkzeug.utils import secure_filename
from utils import extract_text_from_pdf, get_embedding, calculate_similarity, generate_ai_insights, detect_fake_resume
app = Flask(__name__)
app.secret_key = 'quantum_recruitment_secret_2024'
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000/google-auth-callback"
RECRUITERS = {
    'admin@company.com': {'name': 'Admin User', 'password': 'admin123'},
    'asravani557@gmail.com': {'name': 'Sravani', 'password': None}
}
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'recruiter_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# ---------- Routes ----------

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email in RECRUITERS and RECRUITERS[email]['password'] == password:
            session['recruiter_email'] = email
            session['recruiter_name'] = RECRUITERS[email]['name']
            session['login_method'] = 'email'
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})

    return render_template('login.html')


@app.route('/google-login')
def google_login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)


@app.route('/google-auth-callback')
def google_auth_callback():
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            return f"Google OAuth error: {error}", 400

        saved_state = session.get('oauth_state')
        if not saved_state or state != saved_state:
            return "Security error: State mismatch.", 400

        session.pop('oauth_state', None)

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        if token_response.status_code != 200:
            return f"Token exchange failed: {token_json.get('error_description', 'Unknown error')}", 400

        access_token = token_json.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
        user_info = userinfo_response.json()

        if user_info.get('email'):
            email = user_info['email']
            name = user_info.get('name', 'Google User')

            if email not in RECRUITERS:
                RECRUITERS[email] = {'name': name, 'password': None}

            session['recruiter_email'] = email
            session['recruiter_name'] = name
            session['login_method'] = 'google'

            return redirect(url_for('dashboard'))
        else:
            return "Failed to get user info from Google", 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Authentication failed: {str(e)}", 400


@app.route('/dashboard')
@login_required
def dashboard():
    recruiter_email = session.get('recruiter_email')
    recruiter_data = RECRUITERS.get(recruiter_email, {})
    dashboard_data = {
        'total_candidates': 156,
        'interviews': 42,
        'hired': 18,
        'recruiter': recruiter_data
    }
    return render_template('dashboard.html', data=dashboard_data)


@app.route('/quantum-search', methods=['GET', 'POST'])
@login_required
def quantum_search():
    if request.method == 'POST':
        job_description = request.form.get('job_description', '')
        uploaded_files = request.files.getlist('resumes')
        analyzed_candidates = []

        print(f"\n🔍 Starting Quantum Search with {len(uploaded_files)} resumes")
        print(f"📋 Job Description: {job_description[:100]}...")

        # Get job description embedding once
        job_embedding = get_embedding(job_description)

        for idx, file in enumerate(uploaded_files):
            if file and allowed_file(file.filename):
                print(f"\n📄 Processing {idx + 1}/{len(uploaded_files)}: {file.filename}")

                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                # Extract actual resume text
                resume_text = extract_text_from_pdf(open(file_path, 'rb'))
                print(f"✅ Extracted {len(resume_text)} characters from resume")

                # Get resume embedding and calculate similarity
                resume_embedding = get_embedding(resume_text)
                similarity_score = calculate_similarity(job_embedding, resume_embedding)
                match_percentage = int(similarity_score * 100)

                print(f"🎯 Match Score: {match_percentage}%")

                # Generate candidate name from filename
                candidate_name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()

                # Generate AI insights
                ai_analysis = generate_ai_insights(job_description, resume_text, candidate_name)

                # Detect fake resume
                fake_check = detect_fake_resume(resume_text, candidate_name)

                # Determine status based on score
                if match_percentage >= 85:
                    status = 'Perfect Match'
                elif match_percentage >= 70:
                    status = 'Strong Match'
                elif match_percentage >= 50:
                    status = 'Good Match'
                else:
                    status = 'Partial Match'

                # Extract email (or generate one)
                import re
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
                candidate_email = email_match.group(
                    0) if email_match else f"{candidate_name.lower().replace(' ', '.')}@email.com"

                analyzed_candidates.append({
                    'name': candidate_name,
                    'email': candidate_email,
                    'filename': filename,
                    'score': match_percentage,
                    'status': status,
                    'matched_keywords': ai_analysis['skill_gap_analysis']['strong_skills'],
                    'experience': '3+ years' if match_percentage > 70 else '1-3 years',
                    'ai_insights': ai_analysis,
                    'fake_detection': fake_check,
                    'resume_text': resume_text  # Store for scorecard view
                })

                print(f"✨ Analysis complete: {status}")

        # Sort by score
        analyzed_candidates.sort(key=lambda x: x['score'], reverse=True)

        session['last_search_results'] = {
            'job_description': job_description,
            'total_resumes': len(analyzed_candidates),
            'matched_candidates': len([c for c in analyzed_candidates if c['score'] >= 50]),
            'shortlisted': len([c for c in analyzed_candidates if c['score'] >= 85]),
            'candidates': analyzed_candidates
        }

        print(f"\n🎉 Search Complete: {len(analyzed_candidates)} candidates analyzed")
        return redirect(url_for('results'))

    return render_template('quantum_search.html')


@app.route('/results')
@login_required
def results():
    results_data = session.get('last_search_results', {
        'job_description': 'No search performed yet',
        'total_resumes': 0,
        'matched_candidates': 0,
        'shortlisted': 0,
        'candidates': []
    })
    return render_template('results.html', **results_data)


@app.route('/scorecard/<candidate_name>')
@login_required
def scorecard(candidate_name):
    """Display detailed scorecard for a candidate"""
    results = session.get('last_search_results', {})
    candidates = results.get('candidates', [])

    candidate = next((c for c in candidates if c['name'] == candidate_name), None)

    if not candidate:
        return redirect(url_for('results'))

    job_description = results.get('job_description', '')

    return render_template('scorecard.html',
                           candidate=candidate,
                           job_description=job_description)


@app.route('/api/candidate-details/<candidate_name>')
@login_required
def candidate_details(candidate_name):
    """Get detailed information about a specific candidate"""
    results = session.get('last_search_results', {})
    candidates = results.get('candidates', [])

    candidate = next((c for c in candidates if c['name'] == candidate_name), None)

    if candidate:
        return jsonify({'success': True, 'candidate': candidate})
    else:
        return jsonify({'success': False, 'message': 'Candidate not found'})


@app.route('/api/generate-email', methods=['POST'])
@login_required
def generate_email():
    data = request.json
    candidate_name = data.get('candidate_name', 'Candidate')
    candidate_email = data.get('candidate_email', '')
    score = data.get('score', 85)
    experience = data.get('experience', '3+ years')
    matched_skills = data.get('matched_skills', [])

    recruiter_name = session.get('recruiter_name', 'Recruitment Team')

    skills_text = ', '.join(matched_skills[:3]) if matched_skills else 'relevant technical skills'

    # Generate personalized email based on score
    if score >= 90:
        greeting = "We are extremely impressed with your exceptional profile"
        interest_level = "strongly believe you would be an outstanding addition"
    elif score >= 75:
        greeting = "We were very impressed with your strong profile"
        interest_level = "believe you would be a great fit"
    else:
        greeting = "We found your profile interesting"
        interest_level = "think you could be a good match"

    email_content = f"""Dear {candidate_name},

{greeting} and would like to invite you for an interview opportunity.

Your resume achieved an impressive {score}% match with our requirements, particularly highlighting your expertise in {skills_text} with {experience} of relevant experience.

We {interest_level} for our team and would love to discuss this opportunity in more detail.

Interview Details:
• Format: Initial screening call (30 minutes)
• Next Steps: Technical assessment & team interview
• Timeline: We're looking to fill this position within 2-3 weeks

Would you be available for a conversation in the coming week? Please share your preferred time slots and we'll schedule accordingly.

Looking forward to connecting with you!

Best regards,
{recruiter_name}
Quantum Recruitment System

---
This is an automated invitation. If you have any questions, please reply to this email."""

    return jsonify({
        'success': True,
        'email_content': email_content,
        'candidate_email': candidate_email,
        'subject': f'Interview Invitation - {score}% Match | Exciting Opportunity'
    })


@app.route('/api/send-email', methods=['POST'])
@login_required
def send_email():
    """Send actual email using SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    data = request.json
    candidate_email = data.get('email')
    subject = data.get('subject')
    content = data.get('content')

    # Email configuration - UPDATE THESE WITH YOUR CREDENTIALS
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = session.get('recruiter_email', 'your-email@gmail.com')
    SENDER_PASSWORD = "your-app-password"  # Use App Password for Gmail

    try:
        # Create message
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = candidate_email
        message['Subject'] = subject
        message.attach(MIMEText(content, 'plain'))

        # Send email (commented out for safety - uncomment when ready)
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SENDER_EMAIL, SENDER_PASSWORD)
        #     server.send_message(message)

        # For now, just log it
        print(f"\n📧 EMAIL WOULD BE SENT:")
        print(f"To: {candidate_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{content}\n")

        return jsonify({
            'success': True,
            'message': f'Email sent successfully to {candidate_email}'
        })

    except Exception as e:
        print(f"❌ Email error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)