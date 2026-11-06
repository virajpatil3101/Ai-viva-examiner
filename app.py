import json
import re
import streamlit as st
from google import genai

st.set_page_config(page_title="AI Viva Examiner", page_icon="🎓", layout="centered")

st.title("🎓 AI-Based Smart Viva Examiner")
st.caption("Practice viva questions, answer like a student, and receive teacher-style feedback.")

# API key can be entered in the sidebar or stored in Streamlit Secrets.
def get_api_key():
    entered = st.session_state.get("api_key_input", "").strip()
    if entered:
        return entered
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

with st.sidebar:
    st.header("⚙️ Setup")
    st.text_input("Gemini API key (optional)", type="password", key="api_key_input",
                  help="Or add GEMINI_API_KEY in Streamlit → Advanced settings → Secrets.")
    st.caption("Without an API key, the app uses a small built-in practice set. AI feedback requires a valid key.")
    subject = st.selectbox("Subject", [
        "Python Programming", "Java Programming", "Machine Learning",
        "Artificial Intelligence", "Data Structures and Algorithms",
        "Database Management Systems", "Cloud Computing",
        "Computer Networks", "Operating Systems", "Digital Signal Processing",
        "Data Engineering and Big Data", "General Engineering"
    ])
    topic = st.text_input("Topic (optional)", placeholder="e.g. Inheritance, Neural Networks")
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    count = st.slider("Number of viva questions", 3, 10, 5)

api_key = get_api_key()

FALLBACK = {
    "Python Programming": [
        ("What is Python?", "Python is a high-level, interpreted, general-purpose programming language known for readable syntax."),
        ("What is the difference between a list and a tuple?", "A list is mutable, while a tuple is immutable."),
        ("What is a dictionary in Python?", "A dictionary stores key-value pairs and is mutable."),
        ("What is a function?", "A function is a reusable block of code that performs a specific task."),
        ("What is an exception?", "An exception is a runtime event that interrupts normal program flow and can be handled using try/except.")
    ],
    "Java Programming": [
        ("What is Java?", "Java is a high-level, class-based, object-oriented programming language."),
        ("What is inheritance?", "Inheritance allows a class to acquire fields and methods from another class."),
        ("What is method overloading?", "Overloading means defining methods with the same name but different parameter lists."),
        ("What is JVM?", "The Java Virtual Machine executes Java bytecode."),
        ("What is an interface?", "An interface defines a contract of methods that implementing classes provide.")
    ],
    "Machine Learning": [
        ("What is Machine Learning?", "Machine Learning is a field of AI in which systems learn patterns from data to make predictions or decisions."),
        ("Differentiate supervised and unsupervised learning.", "Supervised learning uses labelled data; unsupervised learning finds patterns in unlabelled data."),
        ("What is overfitting?", "Overfitting occurs when a model learns training data too closely and performs poorly on unseen data."),
        ("What is a training dataset?", "It is the data used to fit or train a machine-learning model."),
        ("What is classification?", "Classification predicts a discrete class or category.")
    ],
    "Artificial Intelligence": [
        ("What is Artificial Intelligence?", "AI is the field of creating systems that perform tasks normally requiring human intelligence."),
        ("What is an expert system?", "An expert system uses a knowledge base and inference rules to solve domain-specific problems."),
        ("What is an intelligent agent?", "An intelligent agent perceives its environment and takes actions to achieve goals."),
        ("What is NLP?", "Natural Language Processing enables computers to understand and generate human language."),
        ("What is the difference between AI and ML?", "AI is the broader field; ML is a subset that learns patterns from data.")
    ]
}

def make_client():
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        st.error(f"Could not initialize Gemini client: {exc}")
        return None

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)

def generate_questions(client):
    if client:
        prompt = f"""
Act as a patient but academically strict engineering college viva examiner.
Create exactly {count} concise viva questions for subject: {subject}.
Topic: {topic or 'the full subject'}.
Difficulty: {difficulty}.
Return ONLY a valid JSON array. Each item must have:
{{"question":"...", "ideal_answer":"...", "follow_up":"..."}}
Questions must be clear, non-repeated, technically correct, and suitable for an oral viva.
"""
        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            data = extract_json(response.text or "")
            return data[:count]
        except Exception as exc:
            st.warning(f"AI question generation failed; using practice questions instead. Details: {exc}")
    base = FALLBACK.get(subject, [
        (f"Explain the basic concept of {topic or subject}.", "Give a clear definition, explain its purpose, and provide an example."),
        ("Why is this concept useful?", "Explain the problem it solves and where it is applied."),
        ("Give one practical example.", "Describe a real application and how the concept is used."),
        ("What are its advantages and limitations?", "Mention key benefits and at least one limitation."),
        ("How would you explain this concept in a project?", "Connect the concept to a practical implementation.")
    ])
    return [{"question": q, "ideal_answer": a, "follow_up": "Can you give a practical example?"}
            for q, a in base[:count]]

def evaluate_answer(client, question, ideal, answer):
    if not answer.strip():
        return {"score": 0, "feedback": "No answer submitted. Try explaining the concept in your own words.", "model_answer": ideal}
    if client:
        prompt = f"""
You are an engineering college viva examiner. Evaluate fairly and constructively.
Question: {question}
Expected answer guide: {ideal}
Student answer: {answer}
Return ONLY valid JSON with keys:
score (integer 0 to 10), feedback (2-4 short sentences; mention what was correct and what is missing),
model_answer (a concise ideal answer), improvement_tip (one practical tip).
Do not give full marks for vague answers. Be encouraging, not harsh.
"""
        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            txt = response.text or "{}"
            match = re.search(r"\{.*\}", txt, flags=re.S)
            result = json.loads(match.group(0) if match else txt)
            result["score"] = max(0, min(10, int(result.get("score", 0))))
            return result
        except Exception as exc:
            st.warning(f"AI evaluation failed; showing the answer guide instead. Details: {exc}")
    return {
        "score": 0,
        "feedback": "AI evaluation is unavailable without a working Gemini API key. Compare your response with the answer guide and improve it.",
        "model_answer": ideal,
        "improvement_tip": "Add a definition, explain the key point, and give one example."
    }

if "questions" not in st.session_state:
    st.session_state.questions = []
if "index" not in st.session_state:
    st.session_state.index = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "answer" not in st.session_state:
    st.session_state.answer = ""

col1, col2 = st.columns(2)
with col1:
    st.metric("Questions", len(st.session_state.questions))
with col2:
    st.metric("Answered", len(st.session_state.results))

if st.button("🚀 Start / Restart Viva", type="primary", use_container_width=True):
    client = make_client()
    with st.spinner("Preparing your viva questions..."):
        st.session_state.questions = generate_questions(client)
    st.session_state.index = 0
    st.session_state.results = []
    st.session_state.answer = ""
    st.rerun()

if st.session_state.questions:
    i = st.session_state.index
    if i < len(st.session_state.questions):
        item = st.session_state.questions[i]
        st.progress(i / len(st.session_state.questions))
        st.subheader(f"Question {i+1} of {len(st.session_state.questions)}")
        st.markdown(f"**{item['question']}**")
        answer = st.text_area("Your answer", key=f"answer_{i}", height=150,
                              placeholder="Speak or type your answer here...")
        if st.button("Submit answer & get teacher feedback", type="primary", use_container_width=True):
            client = make_client()
            with st.spinner("Examiner is evaluating your answer..."):
                result = evaluate_answer(client, item["question"], item["ideal_answer"], answer)
            st.session_state.results.append({"question": item["question"], "answer": answer, **result})
            st.session_state.index += 1
            st.rerun()
    else:
        st.success("🎉 Viva completed!")
        scores = [r.get("score", 0) for r in st.session_state.results]
        total = sum(scores)
        possible = len(scores) * 10
        percentage = round(total / possible * 100) if possible else 0
        st.metric("Overall score", f"{total}/{possible}", f"{percentage}%")
        if percentage >= 80:
            st.balloons()
            st.write("Excellent preparation! Keep revising and practise explaining concepts aloud.")
        elif percentage >= 50:
            st.write("Good effort. Revise the missing points and try another round.")
        else:
            st.write("Keep practising. Review the model answers and repeat the viva.")
        for n, r in enumerate(st.session_state.results, 1):
            with st.expander(f"Q{n}. {r['question']} — {r.get('score', 0)}/10"):
                st.write("**Your answer:**", r["answer"] or "No answer")
                st.write("**Examiner feedback:**", r.get("feedback", ""))
                st.write("**Model answer:**", r.get("model_answer", ""))
                if r.get("improvement_tip"):
                    st.info(r["improvement_tip"])
        report = "\n\n".join(
            [f"Q{n}. {r['question']}\nYour answer: {r['answer']}\nScore: {r.get('score',0)}/10\nFeedback: {r.get('feedback','')}\nModel answer: {r.get('model_answer','')}"
             for n, r in enumerate(st.session_state.results, 1)]
        )
        st.download_button("⬇️ Download viva report", report, file_name="viva_report.txt")
        if st.button("Practise again"):
            st.session_state.questions = []
            st.session_state.index = 0
            st.session_state.results = []
            st.rerun()
else:
    st.info("Choose a subject in the sidebar, then tap **Start / Restart Viva**.")
    st.markdown("**How it works:** The examiner asks one question at a time, checks your answer, gives feedback, and prepares a final score report.")
