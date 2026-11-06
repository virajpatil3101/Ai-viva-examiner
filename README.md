# AI-Based Smart Viva Examiner

A mobile-friendly Streamlit app for engineering students to practise oral viva questions.

## Features
- Subject and difficulty selection
- AI-generated viva questions using Gemini
- One-question-at-a-time practice
- Teacher-style feedback and score (0–10)
- Model answers and improvement tips
- Downloadable viva report
- Built-in fallback questions if no API key is configured (AI evaluation requires a key)

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Deploy on Streamlit Community Cloud
1. Upload `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. In Streamlit Community Cloud, choose the repository.
3. Set branch to `main` (or the actual default branch shown by GitHub).
4. Set Main file path to `app.py`.
5. Under Advanced settings → Secrets, add:
   ```toml
   GEMINI_API_KEY = "paste_your_real_key_here"
   ```
6. Save and deploy.

Get a Gemini API key from Google AI Studio. Keep it private. Never upload your real API key or a `secrets.toml` file to GitHub.

## Troubleshooting
- If Streamlit says the branch does not exist, check the exact branch name on GitHub. New repositories commonly use `main`.
- If the main file does not exist, make sure `app.py` is uploaded at the repository root, not inside another folder.
- If packages fail to install, check the build logs and confirm `requirements.txt` is in the repository root.
