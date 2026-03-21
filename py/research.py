# -*- coding: utf-8 -*-
"""
영화감독 명언 자동 리서치 - Wikiquote API + Claude
사용법: python -X utf8 research.py
"""
import os
import re
import sys
import sqlite3
import requests
import anthropic

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')
SOURCES_DIR = os.path.join(os.path.dirname(__file__), '..', 'sources')

WQ_HEADERS = {'User-Agent': 'PeriodShortsBot/1.0 (film quote research)'}

# 감독 리스트 (name_kr, name_en, nationality, famous_works, type, wikiquote_slug)
DIRECTORS = [
    ("봉준호",        "Bong Joon-ho",         "한국",    "기생충, 살인의 추억, 옥자",                        "현대",   "Bong Joon-ho"),
    ("스탠리 큐브릭", "Stanley Kubrick",       "미국",    "2001 스페이스 오디세이, 샤이닝, 풀 메탈 재킷",       "레전드", "Stanley Kubrick"),
    ("박찬욱",        "Park Chan-wook",        "한국",    "올드보이, 친절한 금자씨, 헤어질 결심",               "현대",   "Park Chan-wook"),
    ("구로사와 아키라","Akira Kurosawa",        "일본",    "라쇼몽, 7인의 사무라이, 란",                        "레전드", "Akira Kurosawa"),
    ("이창동",        "Lee Chang-dong",        "한국",    "버닝, 시, 밀양",                                  "현대",   "Lee Chang-dong"),
    ("잉마르 베리만", "Ingmar Bergman",         "스웨덴",  "제7의 봉인, 페르소나, 야생 딸기",                   "레전드", "Ingmar Bergman"),
    ("홍상수",        "Hong Sang-soo",         "한국",    "지금은맞고그때는틀리다, 도망친 여자",                 "현대",   "Hong Sang-soo"),
    ("안드레이 타르코프스키", "Andrei Tarkovsky","러시아", "솔라리스, 스토커, 희생",                            "레전드", "Andrei Tarkovsky"),
    ("나홍진",        "Na Hong-jin",           "한국",    "추격자, 황해, 곡성",                              "현대",   "Na Hong-jin"),
    ("페데리코 펠리니","Federico Fellini",      "이탈리아","8½, 달콤한 인생, 아마코드",                         "레전드", "Federico Fellini"),
    ("윤가영",        "Yoon Ga-eun",           "한국",    "우리들, 영주",                                    "현대",   "Yoon Ga-eun"),
    ("장뤼크 고다르", "Jean-Luc Godard",        "프랑스",  "네 멋대로 해라, 경멸, 주말",                        "레전드", "Jean-Luc Godard"),
    ("크리스토퍼 놀란","Christopher Nolan",     "영국",    "인터스텔라, 다크나이트, 오펜하이머",                  "현대",   "Christopher Nolan"),
    ("알프레드 히치콕","Alfred Hitchcock",      "영국",    "사이코, 현기증, 새",                               "레전드", "Alfred Hitchcock"),
    ("고레에다 히로카즈","Hirokazu Kore-eda",   "일본",    "어느 가족, 태풍이 지나가고, 브로커",                  "현대",   "Hirokazu Kore-eda"),
    ("김기영",        "Kim Ki-young",          "한국",    "하녀, 충녀, 이어도",                               "레전드", "Kim Ki-young"),
    ("하마구치 류스케","Ryusuke Hamaguchi",     "일본",    "드라이브 마이 카, 우연과 상상",                      "현대",   "Ryusuke Hamaguchi"),
    ("임권택",        "Im Kwon-taek",          "한국",    "서편제, 취화선, 아제아제바라아제",                    "레전드", "Im Kwon-taek"),
    ("요아킴 트리에", "Joachim Trier",          "노르웨이","오슬로, 8월 31일, 세상에서 가장 나쁜 사람",           "현대",   "Joachim Trier"),
    ("미하엘 하네케", "Michael Haneke",         "오스트리아","피아니스트, 캐시, 아무르",                        "현대",   "Michael Haneke"),
    ("루벤 외스툴룬드","Ruben Ostlund",         "스웨덴",  "포스, 더 스퀘어, 트라이앵글 오브 새드니스",           "현대",   "Ruben Ostlund"),
    ("라스 폰 트리에","Lars von Trier",         "덴마크",  "멜랑콜리아, 댄서 인 더 다크, 님포매니악",             "현대",   "Lars von Trier"),
    ("웨스 앤더슨",   "Wes Anderson",          "미국",    "그랜드 부다페스트 호텔, 판타스틱 Mr. 폭스",           "현대",   "Wes Anderson"),
    ("다르덴 형제",   "Jean-Pierre and Luc Dardenne","벨기에","로제타, 자전거 탄 소년, 아이",                  "현대",   "Jean-Pierre and Luc Dardenne"),
    ("페드로 알모도바르","Pedro Almodovar",     "스페인",  "내 어머니에 대하여, 그녀에게, 패인 앤 글로리",         "현대",   "Pedro Almodovar"),
    ("켄 로치",       "Ken Loach",             "영국",    "나, 다니엘 블레이크, 미안해요 리키",                  "현대",   "Ken Loach"),
    ("베니 샤프디",   "Benny Safdie",          "미국",    "굿 타임, 언컷 젬스",                               "현대",   "Benny Safdie"),
    ("기타노 다케시", "Takeshi Kitano",         "일본",    "하나비, 소나티네, 기쿠지로의 여름",                   "현대",   "Takeshi Kitano"),
    ("크리스티안 페촐트","Christian Petzold",   "독일",    "바바라, 피닉스, 운디네",                            "현대",   "Christian Petzold"),
    ("소피아 코폴라", "Sofia Coppola",          "미국",    "사랑도 통역이 되나요, 마리 앙투아네트",               "현대",   "Sofia Coppola"),
    ("클로이 자오",   "Chloe Zhao",            "중국/미국","노매드랜드, 이터널스, 더 라이더",                    "현대",   "Chloe Zhao"),
    ("폴 토마스 앤더슨","Paul Thomas Anderson", "미국",    "데어 윌 비 블러드, 매그놀리아, 리코리쉬 피자",         "현대",   "Paul Thomas Anderson"),
    ("요르고스 란티모스","Yorgos Lanthimos",    "그리스",  "더 페이버릿, 가난한 것들, 더 랍스터",                 "현대",   "Yorgos Lanthimos"),
    ("아리 애스터",   "Ari Aster",             "미국",    "헤레디터리, 미드소마, 보 이즈 어프레이드",             "현대",   "Ari Aster"),
    ("션 베이커",     "Sean Baker",            "미국",    "플로리다 프로젝트, 탠저린, 아노라",                   "현대",   "Sean Baker"),
    ("쥐스틴 트리에", "Justine Triet",          "프랑스",  "추락의 해부, 시빌",                                "현대",   "Justine Triet"),
]


def get_conn():
    return sqlite3.connect(DB_PATH)


def ensure_director(d):
    name_kr, name_en, nationality, famous_works = d[0], d[1], d[2], d[3]
    conn = get_conn()
    row = conn.execute("SELECT id FROM directors WHERE name_en=?", (name_en,)).fetchone()
    if row:
        conn.close()
        return row[0]
    conn.execute(
        "INSERT INTO directors (name_kr, name_en, nationality, famous_works) VALUES (?,?,?,?)",
        (name_kr, name_en, nationality, famous_works)
    )
    conn.commit()
    did = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return did


def fetch_wikiquote(slug):
    """Wikiquote에서 감독 페이지 raw 텍스트 가져오기"""
    r = requests.get('https://en.wikiquote.org/w/api.php', params={
        'action': 'query', 'titles': slug,
        'prop': 'revisions', 'rvprop': 'content',
        'format': 'json', 'rvslots': 'main'
    }, headers=WQ_HEADERS, timeout=15)
    r.raise_for_status()
    pages = r.json()['query']['pages']
    page = list(pages.values())[0]
    if 'missing' in page:
        return None
    return page['revisions'][0]['slots']['main']['*']


def extract_with_claude(raw_wikitext, name_kr, name_en, famous_works):
    """Claude로 Wikiquote raw 텍스트에서 명언 추출 + 번역"""
    client = anthropic.Anthropic()
    prompt = f"""아래는 Wikiquote의 영화감독 {name_kr}({name_en}) 페이지의 원문(위키 마크업)입니다.

{raw_wikitext[:6000]}

---
위 내용에서 {name_kr}({name_en})가 직접 한 말을 추출해주세요.

선택 기준:
- 영화 철학, 창작론, 삶과 예술에 대한 통찰이 담긴 발언 우선
- 의미있는 발언 최대 5개만 선별 (좋은 것 위주)
- [[...]] 같은 위키 마크업은 제거하고 순수 텍스트만

각 명언마다 아래 형식으로 작성 (빈 줄로 구분):

---
원문: [영어 원문]
번역: [자연스러운 한국어 번역]
맥락: [아래 내용을 포함한 3-5문장 스토리텔링: 어떤 인터뷰/행사/저서에서 나온 말인지, 어떤 질문이나 상황에서 나온 건지, 당시 감독의 상황이나 시대 배경, 어떤 작품과 연결되는지. 일반 대중도 이해할 수 있는 언어로, 사실 기반으로]
출처: Wikiquote - {name_en}
URL: https://en.wikiquote.org/wiki/{name_en.replace(' ', '_')}
---

추출 가능한 명언이 없으면 "없음"이라고만 써주세요."""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


def save_quotes(text, director_id, name_kr):
    conn = get_conn()
    count = 0
    for block in text.split("---"):
        block = block.strip()
        if not block or block == "없음":
            continue
        lines = {}
        for line in block.splitlines():
            if ": " in line:
                k, v = line.split(": ", 1)
                lines[k.strip()] = v.strip()

        quote_original = lines.get("원문", "")
        if not quote_original:
            continue

        exists = conn.execute(
            "SELECT id FROM quotes WHERE quote_original=? AND director_id=?",
            (quote_original, director_id)
        ).fetchone()
        if exists:
            continue

        conn.execute(
            "INSERT INTO quotes (director_id, quote_original, quote_kr, context, source_url, source_title) VALUES (?,?,?,?,?,?)",
            (director_id, quote_original,
             lines.get("번역", ""), lines.get("맥락", ""),
             lines.get("URL", ""), lines.get("출처", ""))
        )
        conn.commit()
        qid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        os.makedirs(SOURCES_DIR, exist_ok=True)
        with open(os.path.join(SOURCES_DIR, f"quote_{qid}.txt"), 'w', encoding='utf-8') as f:
            f.write(f"감독: {name_kr}\n원문: {quote_original}\n번역: {lines.get('번역','')}\n맥락: {lines.get('맥락','')}\n출처: {lines.get('출처','')}\nURL: {lines.get('URL','')}\n")

        count += 1

    conn.close()
    return count


def research_director(d):
    name_kr, name_en, slug = d[0], d[1], d[5]
    print(f"\n{'='*50}")
    print(f"  {name_kr} ({name_en})")
    print(f"{'='*50}")

    director_id = ensure_director(d)

    print(f"  Wikiquote 검색 중...")
    raw = fetch_wikiquote(slug)
    if not raw:
        print(f"  Wikiquote 페이지 없음 — 건너뜀")
        return 0

    print(f"  Claude로 명언 추출 중...")
    try:
        extracted = extract_with_claude(raw, name_kr, name_en, d[3])
        if "없음" in extracted[:20]:
            print(f"  추출 가능한 명언 없음")
            return 0
        count = save_quotes(extracted, director_id, name_kr)
        print(f"  저장 완료: {count}개")
        return count
    except Exception as e:
        print(f"  오류: {e}")
        return 0


def main():
    if not os.path.exists(DB_PATH):
        print("DB가 없습니다. 먼저 init_db.py를 실행하세요.")
        return

    print("=" * 50)
    print("  Period Shorts - 자동 리서치 (Wikiquote)")
    print("=" * 50)
    print(f"\n감독 {len(DIRECTORS)}명 등록됨\n")
    print("[1] 전체 리서치")
    print("[2] 특정 감독 선택")
    print("[3] 오늘의 감독 (한국/외국 각 1명 랜덤)")

    choice = input("\n선택: ").strip()

    if choice == "1":
        targets = DIRECTORS
    elif choice == "2":
        for i, d in enumerate(DIRECTORS):
            print(f"  {i+1:2d}. {d[0]} ({d[1]}) [{d[4]}]")
        idx = int(input("번호: ")) - 1
        targets = [DIRECTORS[idx]]
    elif choice == "3":
        import random
        korean = [d for d in DIRECTORS if d[2] == "한국"]
        foreign = [d for d in DIRECTORS if d[2] != "한국"]
        targets = [random.choice(korean), random.choice(foreign)]
        print(f"\n오늘의 감독: {targets[0][0]}, {targets[1][0]}")
    else:
        print("잘못된 입력")
        return

    total = 0
    for d in targets:
        total += research_director(d)

    print(f"\n완료! 총 {total}개 명언 수집됨")


if __name__ == '__main__':
    main()
