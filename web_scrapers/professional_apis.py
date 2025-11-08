# web_scrapers/professional_apis.py
import requests


class ProfessionalDataAggregator:
    def init(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_professionals(self, job_description, max_results=10):
        """Search for professionals using public APIs"""
        try:
            print(f"🔍 Searching professional networks for: {job_description[:50]}...")

            keywords = self.extract_keywords(job_description)
            print(f"📝 Keywords: {keywords}")

            candidates = []

            # Try GitHub API
            github_candidates = self.search_github(keywords, max_results // 2)
            candidates.extend(github_candidates)

            # Try Stack Overflow API
            stackoverflow_candidates = self.search_stackoverflow(keywords, max_results // 2)
            candidates.extend(stackoverflow_candidates)

            print(f"✅ Found {len(candidates)} professionals")
            return candidates[:max_results]

        except Exception as e:
            print(f"❌ Error in professional search: {e}")
            return self.get_sample_professionals(keywords, max_results)

    def search_github(self, keywords, max_results):
        """Search GitHub for developer profiles"""
        candidates = []
        try:
            query = "+".join(keywords)
            url = f"https://api.github.com/search/users?q={query}&per_page={max_results}"

            print(f"🌐 Calling GitHub API: {url}")
            response = self.session.get(url)
            print(f"📡 GitHub API response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📊 GitHub found {len(data.get('items', []))} users")

                for user in data.get('items', [])[:max_results]:
                    user_details = self.get_github_user_details(user['login'])
                    if user_details:
                        candidates.append(user_details)
            else:
                print(f"⚠️ GitHub API returned {response.status_code}")

        except Exception as e:
            print(f"⚠️ GitHub API error: {e}")

        return candidates

    def get_github_user_details(self, username):
        """Get GitHub user details"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = self.session.get(url)

            if response.status_code == 200:
                user_data = response.json()

                return {
                    'name': user_data.get('name', username),
                    'title': 'Software Developer',
                    'location': user_data.get('location', 'Remote'),
                    'source': 'GitHub',
                    'profile_url': user_data.get('html_url', ''),
                    'skills': ['Python', 'JavaScript', 'Git'],
                    'experience_level': 'Mid-level',
                    'bio': user_data.get('bio', 'Open source contributor')
                }
        except Exception as e:
            print(f"⚠️ Error fetching GitHub user {username}: {e}")

        return None

    def search_stackoverflow(self, keywords, max_results):
        """Search Stack Overflow for technical profiles"""
        candidates = []
        try:
            query = ";".join(keywords[:2])  # Use only first 2 keywords
            url = f"https://api.stackexchange.com/2.3/users?order=desc&sort=reputation&inname={query}&site=stackoverflow&pagesize={max_results}"

            print(f"🌐 Calling Stack Overflow API: {url}")
            response = self.session.get(url)
            print(f"📡 Stack Overflow API response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📊 Stack Overflow found {len(data.get('items', []))} users")
        for user in data.get('items', [])[:max_results]:
            candidate = {
                'name': user.get('display_name', 'Stack Overflow User'),
                'title': 'Technical Expert',
                'location': user.get('location', 'Global'),
                'source': 'Stack Overflow',
                'profile_url': user.get('link', ''),
                'skills': keywords[:3],
                'experience_level': 'Senior' if user.get('reputation', 0) > 5000 else 'Mid-level',
                'reputation': user.get('reputation', 0)
            }
            candidates.append(candidate)
        else:
            print(f"⚠️ Stack Overflow API returned {response.status_code}")

        except Exception as e:
        print(f"⚠️ Stack Overflow API error: {e}")

    return candidates

    def extract_keywords(self, job_description):
        """Extract keywords from job description"""
        technical_skills = [
            'python', 'javascript', 'java', 'react', 'node', 'aws', 'docker',
            'kubernetes', 'sql', 'mongodb', 'machine learning', 'ai'
        ]

        job_desc_lower = job_description.lower()
        found_skills = [skill for skill in technical_skills if skill in job_desc_lower]

        if not found_skills:
            # Fallback to general terms
            found_skills = ['developer', 'software', 'engineer']

        return found_skills[:5]

    def get_sample_professionals(self, keywords, max_results):
        """Generate sample profiles if APIs fail"""
        print(" Generating sample professional profiles...")

        sample_names = ["Arjun Patel", "Neha Gupta", "Sandeep Reddy", "Ananya Singh"]
        sample_titles = ["Software Engineer", "Full Stack Developer", "Data Scientist", "DevOps Engineer"]
        sample_locations = ["Bangalore, India", "Hyderabad, India", "Pune, India", "Delhi, India"]

        profiles = []
        for i in range(min(max_results, 8)):
            profiles.append({
                'name': sample_names[i % len(sample_names)],
                'title': sample_titles[i % len(sample_titles)],
                'location': sample_locations[i % len(sample_locations)],
                'source': 'Professional Network',
                'profile_url': f"https://portfolio-{i}.dev",
                'skills': keywords[:3] if keywords else ['Python', 'JavaScript', 'SQL'],
                'experience_level': 'Mid-level',
                'bio': f"Experienced {sample_titles[i % len(sample_titles)].lower()} with strong technical skills."
            })

        return profiles


# Test the class directly
if name == "main":
    print(" Testing ProfessionalDataAggregator...")
    aggregator = ProfessionalDataAggregator()
    test_candidates = aggregator.search_professionals("Python developer with Django experience")
    print(f" Test found {len(test_candidates)} candidates")
    for cand in test_candidates[:3]:
        print(f"  - {cand['name']} ({cand['source']}): {cand['title']}")