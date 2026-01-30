import re
import sys
import os

# Add parent directory to path to import from openRouter
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from openRouter.openrouter import call_openrouter
# =========================
# UNIVERSAL BASE PROMPT
# =========================

SYSTEM_PROMPT_BASE = """
You are a transcript normalization engine.

Your role is STRICTLY MECHANICAL CLEANUP of noisy ASR output.
You are NOT a teacher, explainer, summarizer, or interpreter.

SOURCE CHARACTERISTICS:
- Spoken lecture
- Indian/Hinglish accent
- Frequent false starts, repetitions, and unfinished expressions
- Mathematical or technical notation spoken aloud

HARD CONSTRAINTS (VIOLATION = FAILURE):

1. NO INVENTION
- Do not add missing steps, symbols, variables, or conclusions.
- Do not complete or repair incomplete expressions.
- If an equation or statement is incomplete or corrupted beyond safe repair, REMOVE it.

2. NO INTERPRETATION
- Do not infer intent.
- Do not simplify.
- Do not reorganize.
- Do not resolve ambiguity.

3. CANONICALIZATION ONLY
You may ONLY:
- Correct phonetic spelling
- Normalize terminology
- Normalize notation when intent is unambiguous
- Add punctuation and sentence boundaries
- Remove non-meaningful filler and repeated false starts

4. AMBIGUITY RULE
- If multiple interpretations exist, KEEP ORIGINAL WORDING or DELETE.
- Never choose one interpretation.

5. GARBAGE FILTER
Remove:
- Numeric noise with no semantic structure
- Partial equations lacking operands or operators
- Roll calls, countdowns, self-corrections without final statements

6. EQUATION SAFETY
- Convert spoken math/notation to symbols ONLY if complete and explicit.
- Otherwise keep as words or omit.

7. ORDER PRESERVATION
- Preserve original sequence.
- Do not group, reorder, or restructure content.

8. LANGUAGE PRESERVATION
- Keep English technical terms.
- Do not translate Hinglish into explanations.
- Remove only non-meaningful filler words.

REPETITION RULE:
- If a statement is repeated verbatim or near-verbatim and one instance is clearly complete,
  keep the first complete instance and remove later repetitions.
- If none are clearly complete, remove all.

Remove:
- Live demo narration (commands, clicks, waiting, restarting, copying, pasting)
- Temporal instructions tied to real-time actions
unless they contain standalone conceptual information.



OUTPUT REQUIREMENTS:
- Clean academic prose
- Correct notation where safe
- No headings
- No bullet points
- No commentary
- Output ONLY the cleaned transcript
"""

# =========================
# SUBJECT EXTENSIONS
# =========================

SYSTEM_PROMPT_MATH = SYSTEM_PROMPT_BASE + """
MATH-SPECIFIC RULES:

- Normalize standard symbols (x², y², z =, √()) only when explicit.
- Preserve plus/minus signs exactly as spoken.
- Normalize surface names only if explicitly stated (e.g., "paraboloid").
- Do NOT name or classify a surface unless the name is spoken.
- Do NOT complete squares, shift vertices, or infer geometry.
"""

SYSTEM_PROMPT_DSA = SYSTEM_PROMPT_BASE + """
DSA-SPECIFIC RULES:

- Normalize algorithm names and Big-O notation only if explicitly spoken.
- Correct pseudocode syntax ONLY when structure is complete.
- Remove half-written or broken code fragments.
- Do NOT infer optimizations, steps, or missing logic.
"""

SYSTEM_PROMPT_DBMS = SYSTEM_PROMPT_BASE + """
DBMS-SPECIFIC RULES:

- Normalize SQL keywords only for complete queries.
- Preserve table and column names as spoken.
- Remove malformed or partial SQL statements.
- Do NOT infer joins, keys, constraints, or relationships.
"""

SYSTEM_PROMPT_GENAI = SYSTEM_PROMPT_BASE + """
GENAI-SPECIFIC RULES:

- Normalize standard AI/ML terminology (LLM, transformer, backpropagation).
- Do NOT infer architectures, layers, or training steps.
- Remove speculative or half-spoken model names.
"""

SYSTEM_PROMPT_WEBDEV = SYSTEM_PROMPT_BASE + """
WEB DEVELOPMENT-SPECIFIC RULES:

- Normalize standard web terminology (HTML, CSS, JS, React, Express, API, HTTP) only when explicit.
- Preserve framework/library names as spoken (React, Next.js, Node.js, Express, Tailwind, Bootstrap, etc.).
- For code, ONLY normalize clearly complete fragments (full tag, full function, full component or handler).
- Remove half-written, malformed, or interrupted code snippets and configuration blocks.
- Do NOT infer missing props, routes, hooks, lifecycle methods, or middleware.
- Do NOT create or rename components, endpoints, or files that are not explicitly spoken.
- Keep URLs, HTTP verbs, and status codes exactly as spoken when complete; drop incomplete ones.
"""

# =========================
# PROMPT REGISTRY
# =========================

SYSTEM_PROMPTS = {
    "Maths": SYSTEM_PROMPT_MATH,
    "DSA": SYSTEM_PROMPT_DSA,
    "DBMS": SYSTEM_PROMPT_DBMS,
    "GenAI": SYSTEM_PROMPT_GENAI,
    "WebDev": SYSTEM_PROMPT_WEBDEV,
}

def subject_classifier(text):
    """categorizes raw lecture text for normalization"""

    word_dict = {
        "DSA": [
            "algorithm", "data structure", "array", "string", "linked list",
            "stack", "queue", "heap", "hash", "hashmap", "tree", "binary tree",
            "bst", "graph", "dfs", "bfs", "recursion", "dynamic programming",
            "greedy", "two pointer", "sliding window",
            "time complexity", "space complexity", "big o", "optimization",
            "pseudo code", "edge case"
        ],
        "Maths": [
            "formula", "equation", "expression", "theorem", "proof",
            "derivative", "integral", "limit", "matrix", "determinant",
            "vector", "eigen", "probability", "statistics", "mean", "variance",
            "standard deviation", "permutation", "combination",
            "logarithm", "exponential"
        ],
        "DBMS": [
            "database", "dbms", "table", "row", "column", "schema",
            "primary key", "foreign key", "index", "normalization",
            "sql", "select", "insert", "update", "delete",
            "join", "inner join", "left join", "right join",
            "transaction", "acid", "lock", "deadlock",
            "mongodb", "collection", "document", "aggregation"
        ],
        "GenAI": [
            "model", "training", "testing", "validation",
            "neural network", "deep learning", "machine learning",
            "dataset", "label", "loss", "optimizer",
            "gradient", "backpropagation",
            "transformer", "attention", "embedding",
            "llm", "prompt", "fine tuning", "inference",
            "overfitting", "underfitting"
        ],
        "WebDev": [
            "html", "css", "javascript", "js", "typescript", "ts",
            "frontend", "backend", "full stack", "full-stack",
            "react", "next js", "next.js", "vue", "angular",
            "component", "props", "state", "hook", "use state", "use effect",
            "dom", "event listener", "event handler",
            "api", "rest", "rest api", "http", "request", "response",
            "endpoint", "route", "router", "controller",
            "express", "node", "node js", "node.js",
            "json", "fetch", "axios",
            "layout", "flexbox", "grid", "responsive", "media query",
            "tailwind", "bootstrap", "css module", "styled components"
        ]
    }

    text = text.lower()
    scores = {k: 0 for k in word_dict}

    for subject, keywords in word_dict.items():
        for kw in keywords:
            if kw in text:
                scores[subject] += 1

    return max(scores, key=scores.get)




def filter_by_script(text: str) -> str:
    # Unicode ranges

    DEVANAGARI = r"\u0900-\u097F"
    LATIN = r"a-zA-Z"
    DIGITS = r"0-9"
    MATH = r"\+\-\*/=\^\(\)\[\]\{\}<>,\.:"

    ALLOWED_PATTERN = re.compile(
        rf"[{DEVANAGARI}{LATIN}{DIGITS}{MATH}\s]+"
    )
    tokens = text.split()
    kept = []
    for t in tokens:
        if ALLOWED_PATTERN.fullmatch(t):
            kept.append(t)
    return " ".join(kept)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\.\,\=\+\-\*/\^\(\)]", "", text)
    return text.strip()


FILLERS = [
    "okay", "achha", "bolo", "samjhe", "yes or no",
    "theek hai", "right", "fine", "guys",
    "देखो", "समझो"
]

def remove_fillers(text: str) -> str:
    for f in FILLERS:
        # remove only if repeated or standalone
        text = re.sub(rf"(\b{f}\b\s*){{2,}}", "", text)
    return text.strip()



def collapse_token_repetition(text: str, max_repeat=2) -> str:
    tokens = text.split()
    result = []
    prev = None
    count = 0

    for t in tokens:
        if t == prev:
            count += 1
            if count < max_repeat:
                result.append(t)
        else:
            prev = t
            count = 1
            result.append(t)

    return " ".join(result)


def collapse_ngram_repetition(text: str, n=3):
    words = text.split()
    seen = set()
    out = []

    i = 0
    while i < len(words):
        gram = tuple(words[i:i+n])
        if len(gram) == n and gram in seen:
            i += n
            continue
        seen.add(gram)
        out.append(words[i])
        i += 1

    return " ".join(out)



def remove_numeric_spam(text: str) -> str:
    return re.sub(r"\b(\d+)(\s+\1){2,}\b", r"\1", text)


def is_low_entropy(text: str) -> bool:
    words = text.split()
    if not words:
        return True
    unique_ratio = len(set(words)) / len(words)
    return unique_ratio < 0.4

def AllMerged(text: str) -> str:
    text = normalize_text(text)
    text = filter_by_script(text)
    text = remove_fillers(text)
    text = collapse_token_repetition(text)
    text = collapse_ngram_repetition(text)
    text = remove_numeric_spam(text)
    if is_low_entropy(text):
        return     ""  # drop chunk
    subject = subject_classifier(text)
    SYSTEM_PROMPT = SYSTEM_PROMPTS.get(subject, SYSTEM_PROMPTS["Maths"])  # Default to Maths if subject not found
    text = call_openrouter(text, system_prompt = SYSTEM_PROMPT)



    return text


if __name__ == "__main__":
    AllMerged(text)

