"""
modules/translation/plugins/aibox/api_client.py — Bộ gọi API bậc thấp của AI-Box.
Xử lý đóng gói request payload JSON, gọi HTTP POST qua thư viện chuẩn và parse văn bản trả về.
"""

import json
import re
import urllib.request
import urllib.error
import random
import time
from typing import Dict, List, Tuple
from app.core.contracts import SrtBlock
from modules.translation.contracts import LANG_NAMES, CONTENT_LABELS, SKIP_RE

AIBOX_URL = "https://api.ai-box.vn/v1/chat/completions"


def build_system_prompt(target_lang: str, content_type: str, glossary: Dict[str, str]) -> str:
    """Tạo prompt hệ thống hướng dẫn mô hình dịch thuật cách hành văn và định dạng đầu ra."""
    lang_name = LANG_NAMES.get(target_lang.lower(), target_lang)
    content_label = CONTENT_LABELS.get(content_type, content_type)

    # Đóng gói danh mục glossary nếu người dùng cấu hình
    glossary_section = ""
    if glossary:
        lines = [f"  {src} → {tgt}" for src, tgt in glossary.items() if src and tgt]
        if lines:
            glossary_section = "GLOSSARY (apply consistently):\n" + "\n".join(lines) + "\n\n"

    return f"""You are an expert {content_label} subtitle translator. Translate the SRT batch into {lang_name} for TTS dubbing.

RULES:
1. PACING: Text is for TTS voiceover — match block duration. Compress aggressively: shortest natural expression, no fillers, no redundant words.
   - Alphabetic (Indonesian/English/French/Spanish/German/Turkish): use contractions, short synonyms.
   - CJK (Chinese/Japanese/Korean): target 2.5–3.5 syllables/sec of block duration.
   - Abugida (Thai/Vietnamese/Hindi): direct phrasing, avoid long compounds.
   - RTL (Arabic): high semantic density, correct punctuation.

2. STRICT 1-TO-1 MAPPING: Translate ONLY text inside each block. NO word-shifting between blocks. Count blocks before responding — output count MUST equal input count. Mid-thought blocks: end with `...`; continuing blocks: start with `...`.

3. 100% {lang_name} OUTPUT — ZERO SOURCE CHARACTERS: Every single word MUST be in {lang_name} only. Absolutely NO Chinese (汉字/Hanzi), Japanese (かな/Kanji), Korean (한글), Arabic (عربي), Thai (ไทย), or Cyrillic (кирилл) characters are allowed in the output — not even in parentheses or as notes. If a proper name cannot be translated, write it phonetically in {lang_name} letters only. Example: 北京 → "Beijing", not "北京" or "Beijing (北京)".

4. REGISTER: Natural spoken {lang_name} as heard in {content_label}. Match original tone (casual/formal).

5. OUTPUT FORMAT:
   - Wrap result in `<TRANSLATE_TEXT>` tags.
   - Valid SRT only: index → timestamp → translated text → blank line.
   - No markdown, no explanations, no comments.

{glossary_section}Translate the following SRT batch into {lang_name} inside `<TRANSLATE_TEXT>` tags."""


def build_user_content(blocks: List[SrtBlock]) -> str:
    """Đóng gói danh sách khối phụ đề đầu vào thành chuỗi định dạng SRT thô nằm trong tag <INPUT>."""
    srt_parts = []
    for blk in blocks:
        if not blk.text or SKIP_RE.match(blk.text):
            continue
        srt_parts.append(str(blk.idx))
        srt_parts.append(blk.timestamp)
        srt_parts.append(blk.text)
        srt_parts.append("")  # Dòng phân tách
        
    inner = "\n".join(srt_parts).strip()
    return f"<INPUT>\n{inner}\n</INPUT>"


def parse_response(response_text: str) -> Dict[int, str]:
    """
    Phân tích văn bản thô trả về từ LLM để tách thành cấu trúc dict {block_idx: "nội dung dịch"}.
    Hỗ trợ 3 chiến lược bóc tách (tags SRT, mảng JSON, hoặc dòng chỉ mục [N]).
    """
    result = {}
    text = response_text.strip()

    # Chiến lược 1: Bóc tách cụm văn bản nằm trong thẻ <TRANSLATE_TEXT>
    tag_m = re.search(r"<TRANSLATE_TEXT>(.*?)</TRANSLATE_TEXT>", text, re.DOTALL)
    srt_content = tag_m.group(1).strip() if tag_m else text

    # Loại bỏ code block markdown nếu có (```srt ... ```)
    if srt_content.startswith("```"):
        fence_m = re.search(r"```(?:srt|\w*)?\s*(.*?)\s*```", srt_content, re.DOTALL)
        if fence_m:
            srt_content = fence_m.group(1).strip()

    # Phân tách cấu trúc SRT: dòng chỉ mục -> dòng timestamp -> dòng chữ
    for chunk in re.split(r"\n{2,}", srt_content):
        lines = [l for l in chunk.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        try:
            idx = int(lines[0].strip())
        except ValueError:
            continue
        
        # Nếu dòng 2 là timestamp thì nội dung bắt đầu từ dòng 3 (index 2), ngược lại bắt đầu từ dòng 2 (index 1)
        text_start = 2 if (len(lines) > 2 and "-->" in lines[1]) else 1
        translated = "\n".join(lines[text_start:]).strip()
        if translated:
            result[idx] = translated

    if result:
        return result

    # Chiến lược 2: Tự động thử giải mã nếu LLM trả về cấu trúc dạng mảng JSON
    try:
        parsed = json.loads(srt_content)
        arr = parsed if isinstance(parsed, list) else parsed.get("translations", [])
        for item in arr:
            if "idx" in item and "text" in item:
                result[int(item["idx"])] = str(item["text"]).replace(" | ", "\n")
        if result:
            return result
    except Exception:
        pass

    # Chiến lược 3: Thử bóc tách nếu kết quả trả về dạng danh sách dòng: "[index] văn bản dịch"
    for line in srt_content.splitlines():
        m = re.match(r"^\[(\d+)\]\s*(.+)", line.strip())
        if m:
            result[int(m.group(1))] = m.group(2).strip().replace(" | ", "\n")

    return result


def call_api(
    api_key: str,
    model: str,
    system_prompt: str,
    user_content: str,
    timeout: int = 90
) -> str:
    """Gửi trực tiếp POST request JSON đến endpoint API AI-Box sử dụng thư viện chuẩn urllib."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "temperature": 0.25,
    }).encode("utf-8")

    req = urllib.request.Request(
        AIBOX_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
