from config import OPENAI_API_KEY


def test_config():
    print("🔧 Testing Configuration...")

    # Test if config loads
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        print("✅ config.py loaded successfully")
        print("✅ OpenAI API Key format is correct")
        print(f"✅ Key length: {len(OPENAI_API_KEY)} characters")
    else:
        print("❌ config.py not loading properly")

    # Test imports
    try:
        from utils import extract_text_from_file_simple, analyze_resume_intelligently
        print("✅ utils.py imports working")
    except ImportError as e:
        print(f"❌ Import error: {e}")


if name == "main":
    test_config()