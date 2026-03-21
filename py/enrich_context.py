# -*- coding: utf-8 -*-
"""
기존 DB 맥락 보강 스크립트
- 각 명언의 context를 구체적인 일화/상황 형태로 업데이트
사용법: python -X utf8 enrich_context.py
"""
import os
import sqlite3
import anthropic
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')


def get_conn():
    return sqlite3.connect(DB_PATH)


def enrich_one(quote_id, name_kr, name_en, works, quote_original, quote_kr, context_old):
    client = anthropic.Anthropic()

    prompt = f"""영화감독 {name_kr}({name_en})의 다음 발언에 대해 구체적인 배경을 조사해주세요.

감독 대표작: {works}
발언 원문: {quote_original}
기존 맥락 메모: {context_old}

아래 내용을 포함해서 3-5문장으로 작성해주세요:
- 이 말이 나온 구체적인 상황 (어떤 인터뷰/행사/강연/저서에서)
- 어떤 질문에 대한 답이었는지, 또는 어떤 계기로 나온 말인지
- 당시 감독의 상황이나 시대적 배경
- 이 발언이 감독의 어떤 작품/철학과 연결되는지

조건:
- 확실한 사실만 (모르면 "알려지지 않았다"고 솔직히)
- 일반 대중도 이해할 수 있는 언어로
- 스토리텔링이 되도록
- 단락 없이 이어지는 문장으로"""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


def main():
    conn = get_conn()
    rows = conn.execute("""
        SELECT q.id, d.name_kr, d.name_en, d.famous_works,
               q.quote_original, q.quote_kr, q.context
        FROM quotes q JOIN directors d ON q.director_id = d.id
        ORDER BY d.name_kr, q.id
    """).fetchall()
    conn.close()

    print(f"총 {len(rows)}개 명언 맥락 보강 시작\n")

    for i, row in enumerate(rows):
        qid, name_kr, name_en, works, q_orig, q_kr, ctx_old = row
        print(f"[{i+1}/{len(rows)}] {name_kr} - \"{q_orig[:40]}...\"")

        try:
            new_context = enrich_one(qid, name_kr, name_en, works, q_orig, q_kr, ctx_old)

            conn = get_conn()
            conn.execute("UPDATE quotes SET context=? WHERE id=?", (new_context, qid))
            conn.commit()
            conn.close()
            print(f"  완료: {new_context[:80]}...")
        except Exception as e:
            print(f"  오류: {e}")

    print(f"\n전체 완료!")


if __name__ == '__main__':
    main()
