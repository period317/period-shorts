"""
원문 소스 추가 스크립트
사용법: python add_source.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def list_directors():
    conn = get_conn()
    rows = conn.execute("SELECT id, name_kr, name_en, nationality FROM directors ORDER BY name_kr").fetchall()
    conn.close()
    return rows

def add_director():
    print("\n[ 새 감독 추가 ]")
    name_kr = input("이름 (한국어): ").strip()
    name_en = input("이름 (영어): ").strip()
    nationality = input("국적: ").strip()
    birth_year = input("출생연도 (모르면 엔터): ").strip()
    famous_works = input("대표작 (쉼표로 구분): ").strip()

    conn = get_conn()
    conn.execute(
        "INSERT INTO directors (name_kr, name_en, nationality, birth_year, famous_works) VALUES (?, ?, ?, ?, ?)",
        (name_kr, name_en, nationality, int(birth_year) if birth_year else None, famous_works)
    )
    conn.commit()
    director_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"감독 추가 완료 (ID: {director_id})")
    return director_id

def add_quote(director_id):
    print("\n[ 명언/원문 추가 ]")
    quote_original = input("원문 (영어 or 원어): ").strip()
    quote_kr = input("한국어 번역 (없으면 엔터): ").strip()
    context = input("맥락/배경 설명: ").strip()
    source_title = input("출처 제목 (기사명, 책명 등): ").strip()
    source_url = input("출처 URL (없으면 엔터): ").strip()

    # sources 폴더에 원문 텍스트 백업
    source_dir = os.path.join(os.path.dirname(__file__), '..', 'sources')
    os.makedirs(source_dir, exist_ok=True)

    conn = get_conn()
    conn.execute(
        """INSERT INTO quotes (director_id, quote_original, quote_kr, context, source_url, source_title)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (director_id, quote_original, quote_kr or None, context, source_url or None, source_title or None)
    )
    conn.commit()
    quote_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    # 텍스트 파일로도 백업
    backup_path = os.path.join(source_dir, f"quote_{quote_id}.txt")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(f"감독 ID: {director_id}\n")
        f.write(f"원문: {quote_original}\n")
        f.write(f"번역: {quote_kr}\n")
        f.write(f"맥락: {context}\n")
        f.write(f"출처: {source_title}\n")
        f.write(f"URL: {source_url}\n")

    print(f"명언 추가 완료 (ID: {quote_id}) → 백업: {backup_path}")
    return quote_id

def main():
    if not os.path.exists(DB_PATH):
        print("DB가 없습니다. 먼저 init_db.py를 실행하세요.")
        return

    print("=" * 50)
    print("  Period Shorts — 원문 소스 추가")
    print("=" * 50)

    directors = list_directors()

    if directors:
        print("\n[ 등록된 감독 목록 ]")
        for d in directors:
            print(f"  {d[0]}. {d[1]} ({d[2]}) - {d[3]}")
        print("  0. 새 감독 추가")

        choice = input("\n감독 번호 선택 (0=새 감독): ").strip()
        if choice == '0':
            director_id = add_director()
        else:
            director_id = int(choice)
    else:
        print("등록된 감독이 없습니다.")
        director_id = add_director()

    add_quote(director_id)

    more = input("\n명언 더 추가하시겠어요? (y/n): ").strip().lower()
    while more == 'y':
        add_quote(director_id)
        more = input("명언 더 추가하시겠어요? (y/n): ").strip().lower()

    print("\n완료!")

if __name__ == '__main__':
    main()
