import os
import glob
import json
import time
from dotenv import load_dotenv

load_dotenv()  # load .env into environment

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
PROMPT_HTML_PATH = "prompts/customize_cv_and_html_prompt.txt"
INPUT_CV_DIR = "inputs/cvs"
INPUT_JD_DIR = "inputs/job_descriptions"
OUTPUT_DIR = "outputs"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "resume.html")
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "resume.pdf")
RAW_RESP_PREFIX = os.path.join(OUTPUT_DIR, "html_llm_response_attempt_")
TEMPLATE_PATH = "format/generate_cv_template.html"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("prompts", exist_ok=True)
os.makedirs(INPUT_CV_DIR, exist_ok=True)
os.makedirs(INPUT_JD_DIR, exist_ok=True)

if not API_KEY:
    raise SystemExit("OPENROUTER_API_KEY not set in environment.")

from openai import OpenAI
import re

def read_first_file_from(dirpath):
    files = sorted(glob.glob(os.path.join(dirpath, "*")))
    if not files:
        return ""
    with open(files[0], "r", encoding="utf-8") as f:
        return f.read()

def read_prompt_template(path):
    if not os.path.exists(path):
        raise SystemExit(f"Prompt template missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_template_head(path=TEMPLATE_PATH):
    """
    Read the full template.html so we can pass it to the LLM for formatting guidance.
    Returns empty string if template not found (LLM will still work with prompt-only guidance).
    """
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def call_openrouter_for_html(system_prompt, user_prompt, timeout=120):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.01,
        max_tokens=10000,
        extra_body={"reasoning": {"enabled": True}},  # required by the endpoint
        timeout=timeout,
    )
    return resp

def extract_message_content(resp):
    try:
        choice = resp.choices[0]
        if isinstance(choice, dict):
            msg = choice.get("message") or {}
            content = msg.get("content") or msg.get("text") or ""
        else:
            msg = getattr(choice, "message", None)
            if msg is not None:
                content = getattr(msg, "content", "") or getattr(msg, "text", "") or ""
            else:
                content = getattr(choice, "text", "") or ""
    except Exception:
        content = ""
    return content

def save_raw_response(resp, path):
    try:
        if hasattr(resp, "to_dict"):
            data = resp.to_dict()
        else:
            data = resp
        with open(path, "w", encoding="utf-8") as rf:
            json.dump(data, rf, indent=2, ensure_ascii=False)
    except Exception:
        with open(path, "w", encoding="utf-8") as rf:
            rf.write(str(resp))

def looks_like_html(s: str) -> bool:
    if not s:
        return False
    s_str = s.lstrip().lower()
    return s_str.startswith("<!doctype") or "<html" in s_str

def _sanitize_and_normalize_html(html_src: str) -> str:
    if not html_src:
        return html_src
    # remove code fences and leading markers
    html = re.sub(r'```(?:html|\w+)?\s*', '', html_src, flags=re.IGNORECASE)
    html = html.replace('```', '')
    # remove tab characters
    html = html.replace('\t', '    ')
    # remove copyright lines
    html = re.sub(r'(?im)^[^\S\r\n]*.*copyright.*$','', html)
    html = re.sub(r'(?im)^.*©.*$','', html)
    # normalize multiple blank lines
    html = re.sub(r'\n{3,}', '\n\n', html)
    # trim
    html = html.replace('\r\n', '\n').strip()
    return html

def main():
    cv_text = read_first_file_from(INPUT_CV_DIR)
    jd_text = read_first_file_from(INPUT_JD_DIR)
    if not cv_text:
        print("No CV found in inputs/cvs. Place a file there and rerun.")
        return
    if not jd_text:
        print("No job description found in inputs/job_descriptions. Place a file there and rerun.")
        return

    prompt_template = read_prompt_template(PROMPT_HTML_PATH)
    template_html = read_template_head(TEMPLATE_PATH)

    # assemble user prompt: include prompt template, inputs, and the template.html content (if available)
    user_prompt = prompt_template.replace("{cv_text}", cv_text).replace("{jd_text}", jd_text)
    if template_html:
        # include the template inside explicit delimiters so the LLM can "study" it
        user_prompt = (
            user_prompt
            + "\n\nTEMPLATE_HTML_START\n"
            + template_html
            + "\nTEMPLATE_HTML_END\n"
            + "\nNOTE: The HTML above is the required visual template. Produce output that conforms to it."
        )

    # DEBUG: save the raw inputs and the full user prompt so you can verify what was sent to the LLM
    with open(os.path.join(OUTPUT_DIR, "debug_cv.txt"), "w", encoding="utf-8") as f:
        f.write(cv_text)
    with open(os.path.join(OUTPUT_DIR, "debug_jd.txt"), "w", encoding="utf-8") as f:
        f.write(jd_text)
    with open(os.path.join(OUTPUT_DIR, "debug_user_prompt.txt"), "w", encoding="utf-8") as f:
        f.write(user_prompt[:30000])  # cap to avoid huge files

    system_prompt = "You are a professional resume writer and HTML/CSS developer. Follow the user prompt exactly."

    max_attempts = 5
    backoff = 1.0
    html_src = None
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}: calling LLM...")
        try:
            resp = call_openrouter_for_html(system_prompt, user_prompt)
        except Exception as e:
            print(f"LLM call failed on attempt {attempt}: {e}")
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 1.5
                continue
            else:
                return

        raw_path = f"{RAW_RESP_PREFIX}{attempt}.json"
        save_raw_response(resp, raw_path)
        print(f"Saved raw response to {raw_path}")

        html_src = extract_message_content(resp)
        if looks_like_html(html_src):
            html_src = _sanitize_and_normalize_html(html_src)
            # ensure no tab characters remain
            html_src = html_src.replace('\t', '    ')
            with open(OUTPUT_HTML, "w", encoding="utf-8") as hf:
                hf.write(html_src)
            print(f"Wrote HTML resume to {OUTPUT_HTML}")
            break

        print(f"Attempt {attempt} produced invalid HTML. Saved raw response; retrying...")
        html_src = None
        time.sleep(backoff)
        backoff *= 1.5

    if not html_src:
        print("LLM did not return a valid HTML document after multiple attempts.")
        print(f"Inspect files in {OUTPUT_DIR} for debug information.")
        return

    # try to create PDF with weasyprint if available
    try:
        from weasyprint import HTML
        HTML(OUTPUT_HTML).write_pdf(OUTPUT_PDF)
        print(f"Wrote PDF resume to {OUTPUT_PDF}")
    except Exception as e:
        print(f"PDF conversion skipped or failed: {e}")
        print("You can convert the HTML manually with weasyprint or a browser print-to-PDF.")

if __name__ == "__main__":
    main()