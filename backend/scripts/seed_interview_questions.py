"""
Seed initial interview questions for IT and Finance domains.
Run this script to populate the interview_questions table with sample questions.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase
import uuid

def seed_questions():
    """Seed the database with initial interview questions."""
    supabase = get_supabase()

    it_questions = [
        {
            "id": str(uuid.uuid4()),
            "question_text": "Explain the difference between a stack and a queue data structure. Provide examples of when you would use each.",
            "role_type": "IT",
            "domain": "IT",
            "category": "technical",
            "difficulty": "beginner",
            "ideal_answer": "A stack follows LIFO (Last In First Out) principle - like a stack of plates. A queue follows FIFO (First In First Out) - like a line at a store. Stacks are used for undo operations, function call management, and expression evaluation. Queues are used for task scheduling, breadth-first search, and handling requests in order.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "What is the difference between SQL and NoSQL databases? When would you choose one over the other?",
            "role_type": "IT",
            "domain": "IT",
            "category": "technical",
            "difficulty": "intermediate",
            "ideal_answer": "SQL databases are relational with fixed schemas, ACID compliance, and structured data. NoSQL databases are flexible, horizontally scalable, and handle unstructured data. Choose SQL for complex queries, transactions, and structured data. Choose NoSQL for high scalability, flexible schemas, and large volumes of varied data.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "How would you design a distributed caching system with cache invalidation?",
            "role_type": "IT",
            "domain": "IT",
            "category": "technical",
            "difficulty": "advanced",
            "ideal_answer": "Key considerations include: distributed hash ring for data distribution, cache eviction policies (LRU, LFU), invalidation strategies (TTL, write-through, write-behind), consistency models (eventual vs strong), replication for availability, and monitoring. Consider using Redis or Memcached as building blocks. Handle cache stampede and cold start problems.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Tell me about a time when you had to debug a particularly difficult problem. What was your approach?",
            "role_type": "IT",
            "domain": "General",
            "category": "behavioral",
            "difficulty": "intermediate",
            "ideal_answer": "Should describe a specific situation, the systematic approach taken (logging, reproduction, isolation, hypothesis testing), tools used, collaboration with team members, and the resolution. Should demonstrate problem-solving skills, persistence, and learning from the experience.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Explain RESTful API design principles and best practices.",
            "role_type": "IT",
            "domain": "IT",
            "category": "technical",
            "difficulty": "intermediate",
            "ideal_answer": "REST principles include: resource-based URLs, HTTP methods (GET, POST, PUT, DELETE), stateless communication, proper status codes, versioning, pagination, filtering, authentication (JWT/OAuth), rate limiting, and consistent error handling. Use nouns for endpoints, implement HATEOAS where appropriate, and follow naming conventions.",
            "is_active": True
        },
    ]

    finance_questions = [
        {
            "id": str(uuid.uuid4()),
            "question_text": "What is the difference between a balance sheet and an income statement?",
            "role_type": "Finance",
            "domain": "Finance",
            "category": "technical",
            "difficulty": "beginner",
            "ideal_answer": "A balance sheet shows a company's financial position at a specific point in time (assets, liabilities, equity). An income statement shows financial performance over a period (revenues, expenses, profit/loss). The balance sheet is a snapshot, while the income statement shows flow over time. Both are key financial statements used in analysis.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "How would you value a company using discounted cash flow (DCF) analysis?",
            "role_type": "Finance",
            "domain": "Finance",
            "category": "technical",
            "difficulty": "intermediate",
            "ideal_answer": "DCF involves: projecting future free cash flows (typically 5-10 years), determining an appropriate discount rate (WACC), calculating the terminal value, discounting all cash flows to present value, and summing them. Key considerations include growth assumptions, working capital changes, capital expenditures, and sensitivity analysis. Compare to market multiples for validation.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Explain the Black-Scholes model and its key assumptions for option pricing.",
            "role_type": "Finance",
            "domain": "Finance",
            "category": "technical",
            "difficulty": "advanced",
            "ideal_answer": "Black-Scholes is a mathematical model for pricing European options. Key assumptions: efficient markets, no dividends, constant volatility and risk-free rate, log-normal price distribution, no transaction costs. The model uses five inputs: current stock price, strike price, time to expiration, risk-free rate, and volatility. It's foundational but has limitations in real markets.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Walk me through a company you've analyzed recently. What made it interesting?",
            "role_type": "Finance",
            "domain": "Finance",
            "category": "case_study",
            "difficulty": "intermediate",
            "ideal_answer": "Should demonstrate: company overview, industry analysis, financial metrics (profitability, growth, margins), competitive advantages, valuation, risks, and investment thesis. Shows analytical thinking, financial knowledge, and ability to communicate clearly. Should reference specific numbers and comparisons.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "What are the three main financial statements and how are they connected?",
            "role_type": "Finance",
            "domain": "Finance",
            "category": "technical",
            "difficulty": "beginner",
            "ideal_answer": "The three statements are: Income Statement (profitability), Balance Sheet (financial position), and Cash Flow Statement (cash movements). They're connected: net income from income statement flows to retained earnings on balance sheet and starts cash flow statement. Changes in balance sheet accounts affect cash flow. Understanding these connections is fundamental to financial analysis.",
            "is_active": True
        },
    ]

    general_questions = [
        {
            "id": str(uuid.uuid4()),
            "question_text": "Tell me about yourself and your background.",
            "role_type": "Both",
            "domain": "General",
            "category": "behavioral",
            "difficulty": "beginner",
            "ideal_answer": "Should provide a concise professional summary covering: educational background, relevant work experience, key skills and achievements, current situation, and why interested in this role. Keep it focused (2-3 minutes), relevant to the position, and end with enthusiasm for the opportunity. Avoid personal details unrelated to the job.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Describe a situation where you had to work with a difficult team member. How did you handle it?",
            "role_type": "Both",
            "domain": "General",
            "category": "behavioral",
            "difficulty": "intermediate",
            "ideal_answer": "Use STAR method: describe the Situation, Task, Action taken, and Result. Should demonstrate emotional intelligence, communication skills, conflict resolution, and professionalism. Focus on understanding their perspective, finding common ground, and achieving a positive outcome. Show self-awareness and learning.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Where do you see yourself in 5 years?",
            "role_type": "Both",
            "domain": "General",
            "category": "behavioral",
            "difficulty": "beginner",
            "ideal_answer": "Should demonstrate ambition balanced with realism, alignment with the company's growth trajectory, desire to develop specific skills relevant to the role, and commitment to adding value. Avoid overly specific titles or implying you'll leave quickly. Show genuine interest in career development within the field.",
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "What is your biggest weakness?",
            "role_type": "Both",
            "domain": "General",
            "category": "behavioral",
            "difficulty": "intermediate",
            "ideal_answer": "Be honest but strategic: choose a real weakness that isn't critical to the role, explain the context, and most importantly, describe concrete steps you're taking to improve. Show self-awareness, commitment to growth, and ability to learn. Avoid clichés like 'I'm a perfectionist' or 'I work too hard.'",
            "is_active": True
        },
    ]

    all_questions = it_questions + finance_questions + general_questions

    print(f"Inserting {len(all_questions)} questions...")

    try:
        result = supabase.table("interview_questions").insert(all_questions).execute()
        print(f"✅ Successfully inserted {len(result.data)} questions!")
        print("\nQuestions by domain:")
        print(f"  - IT: {len(it_questions)}")
        print(f"  - Finance: {len(finance_questions)}")
        print(f"  - General: {len(general_questions)}")
    except Exception as e:
        print(f"❌ Error inserting questions: {e}")

if __name__ == "__main__":
    print("🌱 Seeding interview questions...")
    seed_questions()
    print("✨ Done!")
