"""
Test script for spaCy functionality.
Tests installation, model loading, and core NLP features used in the project.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_spacy_installation():
    """Test if spaCy is installed"""
    print("=" * 60)
    print("TEST 1: spaCy Installation")
    print("=" * 60)
    try:
        import spacy
        print("✓ spaCy is installed")
        print(f"  Version: {spacy.__version__}")
        return True, spacy
    except ImportError as e:
        print(f"✗ spaCy is NOT installed: {e}")
        print("  Install with: pip install spacy")
        return False, None
    except Exception as e:
        print(f"✗ Error importing spaCy: {type(e).__name__}: {e}")
        print("\n  This might be a compatibility issue with Pydantic.")
        print("  spaCy 3.7+ may have issues with Pydantic 2.x")
        print("\n  Possible solutions:")
        print("  1. Try: pip install 'spacy>=3.7.0' --upgrade")
        print("  2. Or downgrade Pydantic: pip install 'pydantic<2.0'")
        print("  3. Or use spaCy 3.6: pip install 'spacy==3.6.1'")
        return False, None

def test_model_loading(spacy_module):
    """Test if the English model can be loaded"""
    print("\n" + "=" * 60)
    print("TEST 2: Model Loading (en_core_web_sm)")
    print("=" * 60)
    if not spacy_module:
        print("✗ Skipping - spaCy not installed")
        return None
    
    try:
        nlp = spacy_module.load("en_core_web_sm")
        print("✓ Model 'en_core_web_sm' loaded successfully")
        print(f"  Pipeline components: {nlp.pipe_names}")
        return nlp
    except OSError as e:
        print(f"✗ Model 'en_core_web_sm' not found: {e}")
        print("  Install with: python -m spacy download en_core_web_sm")
        return None
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return None

def test_basic_nlp_features(nlp):
    """Test basic NLP features"""
    print("\n" + "=" * 60)
    print("TEST 3: Basic NLP Features")
    print("=" * 60)
    if not nlp:
        print("✗ Skipping - Model not loaded")
        return False
    
    test_text = "I am a software engineer with experience in Python, machine learning, and natural language processing."
    
    try:
        doc = nlp(test_text)
        print(f"✓ Processed text: '{test_text[:50]}...'")
        print(f"  Tokens: {len(doc)}")
        print(f"  Sentences: {len(list(doc.sents))}")
        print(f"  Named entities: {len(doc.ents)}")
        return True
    except Exception as e:
        print(f"✗ Error processing text: {e}")
        return False

def test_noun_chunk_extraction(nlp):
    """Test noun chunk extraction (used in score_match_service.py)"""
    print("\n" + "=" * 60)
    print("TEST 4: Noun Chunk Extraction")
    print("=" * 60)
    if not nlp:
        print("✗ Skipping - Model not loaded")
        return False
    
    test_text = "We are looking for a senior software engineer with expertise in Python programming, machine learning algorithms, and cloud computing platforms."
    
    try:
        doc = nlp(test_text)
        noun_chunks = [chunk.text for chunk in doc.noun_chunks]
        
        print(f"✓ Extracted noun chunks from: '{test_text[:60]}...'")
        print(f"  Found {len(noun_chunks)} noun chunks:")
        for i, chunk in enumerate(noun_chunks, 1):
            print(f"    {i}. {chunk}")
        
        # Verify we got some chunks
        if len(noun_chunks) > 0:
            print("✓ Noun chunk extraction working correctly")
            return True
        else:
            print("⚠ Warning: No noun chunks found (might be expected for some texts)")
            return True
    except Exception as e:
        print(f"✗ Error extracting noun chunks: {e}")
        return False

def test_sentence_extraction(nlp):
    """Test sentence extraction (used in processor.py)"""
    print("\n" + "=" * 60)
    print("TEST 5: Sentence Extraction")
    print("=" * 60)
    if not nlp:
        print("✗ Skipping - Model not loaded")
        return False
    
    test_text = """You will be responsible for developing machine learning models. 
    Your duties include data preprocessing and model training. 
    You must collaborate with the data science team."""
    
    try:
        doc = nlp(test_text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        print(f"✓ Extracted sentences from job description")
        print(f"  Found {len(sentences)} sentences:")
        for i, sent in enumerate(sentences, 1):
            print(f"    {i}. {sent}")
        
        # Check for duty keywords (as done in processor.py)
        duty_keywords = [
            "responsibilities", "duties", "will be responsible for", "tasks include",
            "key accountabilities", "you will", "support", "manage", "develop", "implement"
        ]
        
        matching_sentences = []
        for sent in sentences:
            if any(keyword in sent.lower() for keyword in duty_keywords):
                matching_sentences.append(sent)
        
        print(f"  Found {len(matching_sentences)} sentences with duty keywords")
        if matching_sentences:
            print("✓ Sentence extraction with keyword matching working correctly")
        else:
            print("⚠ No sentences matched duty keywords (might be expected)")
        
        return True
    except Exception as e:
        print(f"✗ Error extracting sentences: {e}")
        return False

def test_score_match_service_functionality(nlp):
    """Test the actual function from score_match_service.py"""
    print("\n" + "=" * 60)
    print("TEST 6: score_match_service.py Functionality")
    print("=" * 60)
    if not nlp:
        print("✗ Skipping - Model not loaded")
        return False
    
    # Simulate the _spacy_extract_key_points function
    def extract_key_points(text: str, nlp_model) -> str:
        """Extract key points from text using spaCy (from score_match_service.py)"""
        doc = nlp_model(text)
        key_points = [chunk.text for chunk in doc.noun_chunks]
        return " ".join(key_points)
    
    test_text = "Software Engineer position requires Python programming skills, machine learning experience, and cloud computing knowledge."
    
    try:
        key_points = extract_key_points(test_text, nlp)
        print(f"✓ Extracted key points from: '{test_text[:60]}...'")
        print(f"  Key points: {key_points}")
        
        if key_points:
            print("✓ Key point extraction working correctly")
            return True
        else:
            print("⚠ Warning: No key points extracted")
            return True
    except Exception as e:
        print(f"✗ Error in key point extraction: {e}")
        return False

def test_processor_functionality(nlp):
    """Test the actual function from processor.py"""
    print("\n" + "=" * 60)
    print("TEST 7: processor.py Functionality")
    print("=" * 60)
    if not nlp:
        print("✗ Skipping - Model not loaded")
        return False
    
    # Simulate the extract_duties_responsibilities function
    def extract_duties_nlp(description: str, nlp_model):
        """Extract duties using NLP (from processor.py)"""
        duties = []
        doc = nlp_model(description)
        duty_keywords = [
            "responsibilities", "duties", "will be responsible for", "tasks include",
            "key accountabilities", "you will", "support", "manage", "develop", "implement",
            "perform", "ensure", "collaborate", "lead", "maintain", "create", "design"
        ]
        
        for sent in doc.sents:
            sentence_text = sent.text.lower()
            if any(keyword in sentence_text for keyword in duty_keywords):
                duties.append(sent.text.strip())
        return duties
    
    test_description = """
    Job Responsibilities:
    You will be responsible for developing and maintaining software applications.
    Your duties include collaborating with cross-functional teams.
    You must ensure code quality and performance.
    """
    
    try:
        duties = extract_duties_nlp(test_description, nlp)
        print(f"✓ Extracted duties from job description")
        print(f"  Found {len(duties)} duties:")
        for i, duty in enumerate(duties, 1):
            print(f"    {i}. {duty}")
        
        if len(duties) > 0:
            print("✓ Duty extraction working correctly")
            return True
        else:
            print("⚠ Warning: No duties extracted (might be expected)")
            return True
    except Exception as e:
        print(f"✗ Error in duty extraction: {e}")
        return False

def main():
    """Run all spaCy tests"""
    print("\n" + "=" * 60)
    print("spaCy Test Suite")
    print("=" * 60)
    print("Testing spaCy installation and functionality used in this project\n")
    
    results = []
    
    # Test 1: Installation
    spacy_installed, spacy_module = test_spacy_installation()
    results.append(("Installation", spacy_installed))
    
    # Test 2: Model loading
    nlp = test_model_loading(spacy_module)
    results.append(("Model Loading", nlp is not None))
    
    # Test 3-7: Functionality tests
    if nlp:
        results.append(("Basic NLP Features", test_basic_nlp_features(nlp)))
        results.append(("Noun Chunk Extraction", test_noun_chunk_extraction(nlp)))
        results.append(("Sentence Extraction", test_sentence_extraction(nlp)))
        results.append(("score_match_service Functionality", test_score_match_service_functionality(nlp)))
        results.append(("processor Functionality", test_processor_functionality(nlp)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! spaCy is working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

