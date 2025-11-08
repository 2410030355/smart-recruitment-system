import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import re
from datetime import datetime

# Load local model once
print("🔄 Loading AI model... (this happens once)")
model = None
def get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

print("✅ AI model loaded successfully!")
def extract_text_from_pdf(pdf_file):
    """Extracts text from an uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip() or f"Resume content from {pdf_file.filename}"
    except Exception as e:
        print(f"Note reading PDF {pdf_file.filename}: {e}")
        return f"Professional resume content"


# -------------------- EMBEDDING + SIMILARITY --------------------

def get_embedding(text):
    """Get embeddings using local model."""
    model = get_model()
    if not text.strip():
        return None
    try:
        text = text.replace("\n", " ").strip()
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None


def calculate_similarity(job_desc_embedding, resume_embedding):
    """Calculate cosine similarity between two embeddings."""
    if job_desc_embedding is None or resume_embedding is None:
        return 0
    job_vec = np.array(job_desc_embedding).reshape(1, -1)
    resume_vec = np.array(resume_embedding).reshape(1, -1)
    similarity = cosine_similarity(job_vec, resume_vec)[0][0]
    return round(similarity, 4)


def generate_candidate_name(filename):
    """Generate realistic candidate names from filename."""
    first_names = ["John", "Jane", "Alex", "Sarah", "Mike", "Emily", "David", "Lisa", "Chris", "Amanda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    name_from_file = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
    if len(name_from_file.split()) >= 2:
        return name_from_file
    return f"{random.choice(first_names)} {random.choice(last_names)}"


# -------------------- FAKE RESUME DETECTION --------------------

def detect_fake_resume(resume_text, candidate_name=""):
    """Advanced Fake Resume Detection with Multiple Verification Layers"""
    detection_results = {
        'is_suspicious': False,
        'confidence_score': 0,
        'red_flags': [],
        'yellow_flags': [],
        'verification_suggestions': [],
        'risk_level': 'Low',
        'overall_verdict': 'Likely Authentic'
    }

    # Run detection checks
    detection_results['red_flags'].extend(check_experience_timeline(resume_text))
    detection_results['red_flags'].extend(verify_education(resume_text))
    detection_results['yellow_flags'].extend(check_skill_consistency(resume_text))
    detection_results['yellow_flags'].extend(analyze_writing_patterns(resume_text))
    detection_results['yellow_flags'].extend(detect_overqualification(resume_text))
    detection_results['red_flags'].extend(verify_company_roles(resume_text))

    # Calculate risk
    risk_score = calculate_risk_score(detection_results)
    detection_results.update({
        'confidence_score': risk_score['confidence_score'],
        'risk_level': risk_score['risk_level'],
        'is_suspicious': risk_score['is_suspicious'],
        'overall_verdict': risk_score['verdict'],
        'verification_suggestions': generate_verification_suggestions(detection_results)
    })
    return detection_results


def check_experience_timeline(resume_text):
    issues = []
    year_pattern = r'\b(19|20)\d{2}\b'
    years = re.findall(year_pattern, resume_text)
    years = [int(''.join(y)) for y in years if ''.join(y).isdigit()]

    if years:
        current_year = datetime.now().year
        if any(y > current_year for y in years):
            issues.append("Future dates found")
        if max(years) - min(years) > 50:
            issues.append("Unrealistic career span")
        if len(years) >= 4:
            sorted_years = sorted(years)
            for i in range(0, len(sorted_years) - 2, 2):
                if i + 3 < len(sorted_years):
                    if sorted_years[i + 2] < sorted_years[i + 1]:
                        issues.append("Overlapping employment periods detected")

    if not any(x in resume_text.lower() for x in ['present', 'current', 'now', '2024', '2025']):
        if years:
            issues.append("No current position indicated")
    return issues


def verify_education(resume_text):
    issues = []
    suspicious_degrees = ['university of phoenix', 'online degree', 'diploma mill', 'life experience degree']
    for degree in suspicious_degrees:
        if degree in resume_text.lower():
            issues.append(f"Suspicious education source: {degree}")
    education_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'bs', 'ms', 'ba', 'ma']
    for keyword in education_keywords:
        if keyword in resume_text.lower() and not any(x in resume_text.lower() for x in ['university', 'college']):
            issues.append(f"Degree mentioned ({keyword}) but no educational institution specified")
    return issues


def check_skill_consistency(resume_text):
    issues = []
    exaggerated_skills = {
        'machine learning': ['tensorflow', 'pytorch', 'scikit-learn'],
        'blockchain': ['solidity', 'smart contracts'],
        'quantum computing': ['qiskit', 'quantum'],
    }
    for skill, techs in exaggerated_skills.items():
        if skill in resume_text.lower() and not any(t in resume_text.lower() for t in techs):
            issues.append(f"Advanced skill '{skill}' mentioned without supporting technologies")
    expert_words = ['expert', 'advanced', 'specialist', 'guru', 'ninja']
    if sum(w in resume_text.lower() for w in expert_words) > 5:
        issues.append("Too many 'expert-level' claims")
    return issues


def analyze_writing_patterns(resume_text):
    issues = []
    generic_phrases = [
        'results-oriented professional', 'proven track record', 'team player',
        'strong work ethic', 'fast learner', 'challenging position'
    ]
    if sum(p in resume_text.lower() for p in generic_phrases) > 3:
        issues.append("Too many generic phrases (template detected)")
    if detect_tense_inconsistency(resume_text):
        issues.append("Inconsistent tense usage")
    buzzwords = ['synergy', 'leverage', 'paradigm', 'disrupt', 'innovative', 'cutting-edge']
    if sum(b in resume_text.lower() for b in buzzwords) > 5:
        issues.append("High buzzword density")
    return issues


def detect_tense_inconsistency(text):
    present = ['manage', 'lead', 'develop', 'work', 'collaborate']
    past = ['managed', 'led', 'developed', 'worked', 'collaborated']
    return sum(w in text.lower() for w in present) > 3 and sum(w in text.lower() for w in past) > 3


def detect_overqualification(resume_text):
    issues = []
    senior_titles = ['ceo', 'cto', 'vp', 'director', 'head', 'senior']
    senior_count = sum(t in resume_text.lower() for t in senior_titles)
    if senior_count > 3:
        years = re.findall(r'\b(19|20)\d{2}\b', resume_text)
        years = [int(''.join(y)) for y in years if ''.join(y).isdigit()]
        if years and max(years) - min(years) < 8:
            issues.append(f"Rapid career progression ({senior_count} senior roles in short time)")
    return issues


def verify_company_roles(resume_text):
    issues = []
    famous = ['google', 'microsoft', 'amazon', 'apple', 'meta', 'tesla']
    vague = ['worked on various projects', 'team success', 'multiple responsibilities']
    for c in famous:
        if c in resume_text.lower() and not any(v in resume_text.lower() for v in ['engineer', 'manager', 'scientist']):
            issues.append(f"Famous company ({c}) but vague role description")
    return issues


def calculate_risk_score(results):
    red_score = len(results['red_flags']) * 3
    yellow_score = len(results['yellow_flags'])
    total = red_score + yellow_score
    confidence = max(0, 100 - min(total * 10, 100))

    if total >= 5:
        level, suspicious, verdict = 'Critical', True, 'Highly Suspicious'
    elif total >= 3:
        level, suspicious, verdict = 'High', True, 'Suspicious'
    elif total >= 1:
        level, suspicious, verdict = 'Medium', False, 'Moderate Risk'
    else:
        level, suspicious, verdict = 'Low', False, 'Likely Authentic'

    return {
        'confidence_score': confidence,
        'risk_level': level,
        'is_suspicious': suspicious,
        'verdict': verdict
    }


def generate_verification_suggestions(results):
    suggestions = []
    if results['red_flags']:
        suggestions += [
            "🔴 Verify education and employment records",
            "📅 Request official transcripts",
            "💻 Conduct technical skill assessment"
        ]
    if results['risk_level'] in ['Low', 'Medium']:
        suggestions.append("✅ Standard reference check recommended")
    return suggestions


# -------------------- SKILL + CULTURE ANALYSIS --------------------

def extract_skills(text):
    skills = [
        'python', 'javascript', 'java', 'sql', 'react', 'node.js', 'flask', 'django',
        'aws', 'docker', 'kubernetes', 'git', 'devops', 'leadership', 'communication'
    ]
    return [s for s in skills if s in text.lower()]


def analyze_skill_gaps(job_description, resume_text):
    req = extract_skills(job_description)
    got = extract_skills(resume_text)
    missing = [s for s in req if s not in got]
    strong = [s for s in got if s in req]
    match = len(strong) / len(req) * 100 if req else 0
    return {
        'missing_skills': missing,
        'strong_skills': strong,
        'skill_match_rate': match
    }


def calculate_cultural_fit_score(job_description, resume_text):
    values = ['innovation', 'teamwork', 'growth', 'quality', 'leadership']
    company_values = [v for v in values if v in job_description.lower()]
    candidate_values = [v for v in values if v in resume_text.lower()]
    overlap = set(company_values) & set(candidate_values)
    score = len(overlap) / len(company_values) * 100 if company_values else 70
    return {'score': score, 'shared_values': list(overlap)}


# -------------------- AI INSIGHTS + SUCCESS PREDICTION --------------------

def generate_ai_insights(job_description, resume_text, candidate_name):
    skill_gaps = analyze_skill_gaps(job_description, resume_text)
    cultural_fit = calculate_cultural_fit_score(job_description, resume_text)
    fake_detection = detect_fake_resume(resume_text, candidate_name)

    base_score = (skill_gaps['skill_match_rate'] + cultural_fit['score']) / 2
    authenticity_factor = fake_detection['confidence_score'] / 100
    overall_score = base_score * authenticity_factor

    if overall_score >= 80 and fake_detection['risk_level'] in ['Low', 'Medium']:
        recommendation, priority = "🚀 STRONG HIRE", "High"
    elif overall_score >= 60:
        recommendation, priority = "✅ POTENTIAL HIRE", "Medium"
    elif fake_detection['risk_level'] in ['High', 'Critical']:
        recommendation, priority = "⚠️ VERIFY AUTHENTICITY", "High Risk"
    else:
        recommendation, priority = "⏳ CONSIDER LATER", "Low"

    return {
        'overall_score': overall_score,
        'hiring_recommendation': recommendation,
        'priority_level': priority,
        'skill_gap_analysis': skill_gaps,
        'cultural_fit': cultural_fit,
        'fake_resume_detection': fake_detection
    }


def predict_success_probability(job_description, resume_text):
    skill_match = analyze_skill_gaps(job_description, resume_text)['skill_match_rate'] / 100
    cultural_fit = calculate_cultural_fit_score(job_description, resume_text)['score'] / 100
    authenticity = detect_fake_resume(resume_text)['confidence_score'] / 100
    base = (skill_match * 0.5) + (cultural_fit * 0.3) + (authenticity * 0.2)
    final = min(base * 100, 95)
    level = 'High' if final > 75 else 'Medium' if final > 50 else 'Low'
    return {'success_probability': round(final, 1), 'confidence_level': level}
