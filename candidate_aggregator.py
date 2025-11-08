# candidate_aggregator.py
from web_scrapers.professional_apis import ProfessionalDataAggregator
from utils import get_embedding, calculate_similarity, generate_ai_insights


class CandidateAggregator:
    def init(self):
        self.pro_aggregator = ProfessionalDataAggregator()

    def find_candidates_from_web(self, job_description):
        """Find candidates from professional networks"""
        try:
            print(" Starting web candidate search...")

            # Get candidates from APIs
            candidates = self.pro_aggregator.search_professionals(job_description, 15)

            # Process with AI analysis
            processed = self.process_candidates(candidates, job_description)

            print(f" Search completed: {len(processed)} candidates processed")
            return processed

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def process_candidates(self, candidates, job_description):
        """Process candidates with AI scoring"""
        processed = []

        print(" Getting job description embedding...")
        job_embedding = get_embedding(job_description)

        for i, candidate in enumerate(candidates):
            try:
                print(f"Processing candidate {i + 1}/{len(candidates)}: {candidate['name']}")

                # Create profile text for analysis
                profile_text = self.create_profile_text(candidate)

                # Calculate similarity score
                candidate_embedding = get_embedding(profile_text)
                score = calculate_similarity(job_embedding, candidate_embedding)

                # Generate basic AI insights (skip full analysis for speed)
                ai_insights = self.get_basic_insights(candidate, score)

                # Enhanced candidate data
                candidate['score'] = round(score, 3)
                candidate['profile_text'] = profile_text
                candidate['email'] = f"{candidate['name'].lower().replace(' ', '.')}@professional.com"
                candidate['ai_insights'] = ai_insights

                processed.append(candidate)

                print(f"  Scored: {score:.1%}")

            except Exception as e:
                print(f"  Error processing {candidate.get('name')}: {e}")
                continue

        # Sort by score (highest first)
        processed.sort(key=lambda x: x['score'], reverse=True)
        return processed

    def create_profile_text(self, candidate):
        """Create profile text for AI analysis"""
        skills_text = ", ".join(candidate.get('skills', []))
        return f"""
        Name: {candidate['name']}
        Title: {candidate['title']}
        Location: {candidate['location']}
        Skills: {skills_text}
        Experience Level: {candidate['experience_level']}
        Source: {candidate['source']}
        Bio: {candidate.get('bio', 'Professional in the field')}
        """

    def get_basic_insights(self, candidate, score):
        """Generate basic insights for web candidates"""
        score_percent = int(score * 100)

        if score_percent >= 70:
            recommendation = " STRONG MATCH - Immediate review recommended"
            priority = "High"
        elif score_percent >= 50:
            recommendation = " POTENTIAL MATCH - Schedule screening"
            priority = "Medium"
        else:
            recommendation = " CONSIDER - Keep in talent pool"
            priority = "Low"

        return {
            'overall_score': score_percent,
            'hiring_recommendation': recommendation,
            'priority_level': priority,
            'strengths': candidate.get('skills', [])[:3],
            'development_areas': ['Need more specific project details']
        }

    # Test the class directly
    if name == "main":
        print(" Testing CandidateAggregator...")
        aggregator = CandidateAggregator()
        test_results = aggregator.find_candidates_from_web("Python developer with web experience")
        print(f" Test completed: {len(test_results)} candidates")
        for cand in test_results[:3]:
            print(f"  - {cand['name']}: {cand['score']:.1%} - {cand['ai_insights']['hiring_recommendation']}")
