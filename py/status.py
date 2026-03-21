"""
콘텐츠 현황 대시보드
사용법: python status.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def print_summary():
    conn = get_conn()

    print("=" * 60)
    print("  Period Shorts — 콘텐츠 현황")
    print("=" * 60)

    # 전체 통계
    total_directors = conn.execute("SELECT COUNT(*) FROM directors").fetchone()[0]
    total_quotes = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    total_scripts = conn.execute("SELECT COUNT(*) FROM scripts").fetchone()[0]
    total_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

    print(f"\n[ 전체 현황 ]")
    print(f"  감독: {total_directors}명  |  명언: {total_quotes}개  |  스크립트: {total_scripts}개  |  영상: {total_videos}개")

    # 명언 상태별
    print(f"\n[ 명언 상태 ]")
    statuses = conn.execute("""
        SELECT status, COUNT(*) as cnt FROM quotes GROUP BY status ORDER BY cnt DESC
    """).fetchall()
    status_map = {
        'COLLECTED': '수집됨',
        'SCRIPTED': '스크립트 완료',
        'RECORDED': '녹음 완료',
        'EDITED': '편집 완료',
        'UPLOADED': '업로드 완료'
    }
    for s, cnt in statuses:
        bar = "█" * cnt
        print(f"  {status_map.get(s, s):12s} {bar} {cnt}개")

    # 스크립트 대기 중
    pending = conn.execute("""
        SELECT q.id, d.name_kr, q.quote_original, q.collected_at
        FROM quotes q JOIN directors d ON q.director_id = d.id
        WHERE q.status = 'COLLECTED'
        ORDER BY q.collected_at DESC
        LIMIT 5
    """).fetchall()

    if pending:
        print(f"\n[ 스크립트 생성 대기 중 (최근 5개) ]")
        for row in pending:
            print(f"  ID {row[0]} | {row[1]} | \"{row[2][:45]}...\"")

    # 최근 생성된 스크립트
    recent_scripts = conn.execute("""
        SELECT s.id, d.name_kr, q.quote_original, s.created_at
        FROM scripts s
        JOIN quotes q ON s.quote_id = q.id
        JOIN directors d ON q.director_id = d.id
        ORDER BY s.created_at DESC
        LIMIT 5
    """).fetchall()

    if recent_scripts:
        print(f"\n[ 최근 생성된 스크립트 ]")
        for row in recent_scripts:
            print(f"  Script {row[0]} | {row[1]} | \"{row[2][:45]}...\" | {row[3][:10]}")

    # 업로드 대기 중
    upload_ready = conn.execute("""
        SELECT COUNT(*) FROM quotes WHERE status = 'EDITED'
    """).fetchone()[0]
    if upload_ready > 0:
        print(f"\n[ 업로드 대기 중: {upload_ready}개 ]")

    print("\n" + "=" * 60)
    conn.close()

def list_all_quotes():
    conn = get_conn()
    rows = conn.execute("""
        SELECT q.id, d.name_kr, q.quote_original, q.status, q.collected_at
        FROM quotes q JOIN directors d ON q.director_id = d.id
        ORDER BY q.collected_at DESC
    """).fetchall()
    conn.close()

    status_map = {
        'COLLECTED': '수집',
        'SCRIPTED': '스크립트',
        'RECORDED': '녹음',
        'EDITED': '편집',
        'UPLOADED': '업로드'
    }

    print("\n[ 전체 명언 목록 ]")
    for r in rows:
        print(f"  [{r[0]:3d}] {r[1]:15s} | {status_map.get(r[3], r[3]):6s} | \"{r[2][:50]}\"")

def main():
    if not os.path.exists(DB_PATH):
        print("DB가 없습니다. 먼저 init_db.py를 실행하세요.")
        return

    print_summary()

    choice = input("\n전체 명언 목록 보기? (y/n): ").strip().lower()
    if choice == 'y':
        list_all_quotes()

if __name__ == '__main__':
    main()
