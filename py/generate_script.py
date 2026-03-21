"""
YouTube Shorts 스크립트 자동 생성 (Claude API 사용)
사용법: python generate_script.py
"""
import sqlite3
import os
import anthropic
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_pending_quotes():
    conn = get_conn()
    rows = conn.execute("""
        SELECT q.id, q.quote_original, q.quote_kr, q.context, q.source_title,
               d.name_kr, d.name_en, d.nationality, d.famous_works
        FROM quotes q
        JOIN directors d ON q.director_id = d.id
        WHERE q.status = 'COLLECTED'
        ORDER BY q.collected_at DESC
    """).fetchall()
    conn.close()
    return rows

def generate_script(quote_data):
    quote_id, quote_original, quote_kr, context, source_title, \
    name_kr, name_en, nationality, famous_works = quote_data

    client = anthropic.Anthropic()

    prompt = f"""YouTube Shorts 낭독 스크립트를 작성해주세요.

감독: {name_kr} ({name_en}) | {nationality} | 대표작: {famous_works}
발언 원문: {quote_original}
발언 번역: {quote_kr or '(번역 없음)'}
맥락/일화: {context}
출처: {source_title or '미상'}

핵심 방향:
- 영화를 만들고 싶은 사람들을 위한 콘텐츠. "이 감독은 어떻게 생각하고 어떤 선택을 했는가"
- 구체적인 상황/일화에서 출발해서 감독의 생각으로 연결
- 영화학도도 흥미롭고, 영화 좋아하는 일반인도 공감할 수 있는 언어
- 미니 다큐 느낌. 설명이 아니라 이야기

형식:
- 한국어 스크립트만 (영어는 별도 생성)
- 헤더/이모지/마크다운/연출노트 없이
- 55-60초 낭독 분량, 구어체
- 구성:
  1. 제목 한 줄: 시청자 호기심을 자극하는 한 줄. "봉준호가 희망을 그리지 않는 진짜 이유" 같은 형식. 제목: 으로 시작
  2. 빈 줄
  3. 본문: 상황/일화 훅 → 감독 발언 (쌍따옴표로 감독 말 구분) → 감독이 왜 이 말을 했는지 → 마무리 한 줄
- 나레이션과 감독의 실제 발언은 반드시 구분: 감독이 직접 한 말은 "..." 쌍따옴표로 감싸기
- 섹션 구분은 빈 줄로만

## 한국어 스크립트"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def save_script(quote_id, script_text):
    # 한국어 스크립트만 (영어는 추후 별도 생성)
    script_kr = script_text.replace("## 한국어 스크립트", "").strip()
    script_en = ""

    # DB 저장
    conn = get_conn()
    conn.execute(
        "INSERT INTO scripts (quote_id, script_kr, script_en, status) VALUES (?, ?, ?, 'SCRIPTED')",
        (quote_id, script_kr, script_en)
    )
    conn.execute("UPDATE quotes SET status='SCRIPTED' WHERE id=?", (quote_id,))
    script_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # 파일 저장
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    file_path = os.path.join(SCRIPTS_DIR, f"script_{script_id}.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(script_text)

    print(f"  → 저장: {file_path}")
    return script_id

def main():
    if not os.path.exists(DB_PATH):
        print("DB가 없습니다. 먼저 init_db.py를 실행하세요.")
        return

    quotes = get_pending_quotes()

    if not quotes:
        print("스크립트 생성 대기 중인 명언이 없습니다.")
        return

    print("=" * 50)
    print("  Period Shorts — 스크립트 생성")
    print("=" * 50)
    print(f"\n대기 중인 명언: {len(quotes)}개\n")

    for i, quote in enumerate(quotes):
        print(f"[{i+1}/{len(quotes)}] {quote[5]} ({quote[6]}) - \"{quote[1][:40]}...\"")

    choice = input("\n전체 생성? (y) 또는 번호 선택: ").strip().lower()

    if choice == 'y':
        targets = quotes
    else:
        try:
            idx = int(choice) - 1
            targets = [quotes[idx]]
        except:
            print("잘못된 입력")
            return

    for quote in targets:
        print(f"\n생성 중: {quote[5]} - \"{quote[1][:50]}\"")
        try:
            script_text = generate_script(quote)
            script_id = save_script(quote[0], script_text)
            print(f"완료 (Script ID: {script_id})")
            print("\n--- 미리보기 ---")
            print(script_text[:300] + "...\n")
        except Exception as e:
            print(f"오류: {e}")

if __name__ == '__main__':
    main()
