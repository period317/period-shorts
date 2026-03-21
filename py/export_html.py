# -*- coding: utf-8 -*-
"""
스크립트 HTML 뷰어 생성
사용법: python -X utf8 export_html.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'index.html')


def get_data():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT
            d.name_kr, d.name_en, d.nationality, d.famous_works,
            q.id, q.quote_original, q.quote_kr, q.context, q.source_title, q.source_url,
            s.id as script_id, s.script_kr, s.created_at
        FROM scripts s
        JOIN quotes q ON s.quote_id = q.id
        JOIN directors d ON q.director_id = d.id
        ORDER BY d.name_kr, q.id
    """).fetchall()
    conn.close()
    return rows


def build_html(rows):
    # 감독별로 그룹핑
    directors = {}
    for r in rows:
        name_kr = r[0]
        if name_kr not in directors:
            directors[name_kr] = {
                'name_en': r[1], 'nationality': r[2], 'works': r[3],
                'scripts': []
            }
        directors[name_kr]['scripts'].append({
            'quote_id': r[4],
            'quote_original': r[5],
            'quote_kr': r[6],
            'context': r[7],
            'source_title': r[8],
            'source_url': r[9],
            'script_id': r[10],
            'script_kr': r[11],
            'created_at': r[12],
        })

    # 사이드바 목록
    sidebar_items = ""
    for name_kr, d in directors.items():
        count = len(d['scripts'])
        anchor = name_kr.replace(' ', '_')
        sidebar_items += f'<li><a href="#{anchor}">{name_kr} <span class="count">{count}</span></a></li>\n'

    # 본문 카드
    cards = ""
    for name_kr, d in directors.items():
        anchor = name_kr.replace(' ', '_')
        cards += f"""
        <section id="{anchor}" class="director-section">
            <div class="director-header">
                <h2>{name_kr} <span class="name-en">{d['name_en']}</span></h2>
                <div class="director-meta">{d['nationality']} · {d['works']}</div>
            </div>
        """
        for s in d['scripts']:
            # 제목/본문 분리
            lines = s['script_kr'].strip().split('\n')
            title = ''
            body = s['script_kr'].strip()
            if lines[0].startswith('제목:'):
                title = lines[0].replace('제목:', '').strip()
                body = '\n'.join(lines[1:]).strip()

            body_html = ''.join(
                f'<p>{line}</p>' if line.strip() else '<br>'
                for line in body.split('\n')
            )

            cards += f"""
            <div class="script-card">
                <div class="script-title">{title}</div>
                <div class="quote-box">
                    <div class="quote-original">"{s['quote_original']}"</div>
                    <div class="quote-kr">{s['quote_kr']}</div>
                    <div class="quote-source">{s['source_title'] or ''}</div>
                </div>
                <div class="context-box">
                    <strong>맥락</strong>
                    <p>{s['context']}</p>
                </div>
                <div class="script-body">{body_html}</div>
                <div class="script-meta">Script #{s['script_id']} · Quote #{s['quote_id']} · {s['created_at'][:10] if s['created_at'] else ''}</div>
            </div>
            """
        cards += "</section>"

    total_scripts = sum(len(d['scripts']) for d in directors.values())
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Period Shorts — 스크립트 뷰어</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background: #f5f5f0; color: #1a1a1a; }}

  /* 레이아웃 */
  .layout {{ display: flex; min-height: 100vh; }}
  .sidebar {{ width: 220px; min-width: 220px; background: #1a1a1a; color: #eee; padding: 24px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }}
  .main {{ flex: 1; padding: 40px; max-width: 860px; }}

  /* 사이드바 */
  .sidebar h1 {{ font-size: 14px; color: #888; padding: 0 20px 16px; border-bottom: 1px solid #333; margin-bottom: 12px; letter-spacing: 1px; }}
  .sidebar ul {{ list-style: none; }}
  .sidebar li a {{ display: flex; justify-content: space-between; padding: 8px 20px; color: #ccc; text-decoration: none; font-size: 14px; transition: background 0.15s; }}
  .sidebar li a:hover {{ background: #2a2a2a; color: #fff; }}
  .count {{ background: #333; border-radius: 10px; padding: 1px 7px; font-size: 11px; color: #999; }}
  .sidebar-footer {{ padding: 20px; font-size: 11px; color: #555; margin-top: 20px; border-top: 1px solid #2a2a2a; }}

  /* 검색 */
  .search-box {{ margin-bottom: 32px; }}
  .search-box input {{ width: 100%; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; background: white; }}
  .search-box input:focus {{ outline: none; border-color: #999; }}

  /* 감독 섹션 */
  .director-section {{ margin-bottom: 48px; }}
  .director-header {{ margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #1a1a1a; }}
  .director-header h2 {{ font-size: 22px; font-weight: 700; }}
  .name-en {{ font-size: 14px; font-weight: 400; color: #888; margin-left: 8px; }}
  .director-meta {{ font-size: 13px; color: #888; margin-top: 4px; }}

  /* 스크립트 카드 */
  .script-card {{ background: white; border-radius: 12px; padding: 28px; margin-bottom: 20px; border: 1px solid #e8e8e8; }}
  .script-title {{ font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px; line-height: 1.4; }}

  /* 명언 박스 */
  .quote-box {{ background: #f9f9f7; border-left: 3px solid #1a1a1a; padding: 16px 20px; margin-bottom: 16px; border-radius: 0 8px 8px 0; }}
  .quote-original {{ font-size: 13px; color: #555; font-style: italic; margin-bottom: 6px; line-height: 1.6; }}
  .quote-kr {{ font-size: 14px; color: #333; line-height: 1.6; }}
  .quote-source {{ font-size: 11px; color: #aaa; margin-top: 6px; }}

  /* 맥락 박스 */
  .context-box {{ background: #f0f4ff; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; font-size: 13px; color: #444; line-height: 1.7; }}
  .context-box strong {{ display: block; font-size: 11px; color: #88a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}

  /* 스크립트 본문 */
  .script-body {{ font-size: 15px; line-height: 1.9; color: #222; border-top: 1px solid #eee; padding-top: 16px; }}
  .script-body p {{ margin-bottom: 10px; }}

  .script-meta {{ font-size: 11px; color: #bbb; margin-top: 16px; padding-top: 12px; border-top: 1px solid #f0f0f0; }}

  /* 검색 하이라이트 */
  .highlight {{ background: #fff3a3; }}

  /* 숨김 */
  .hidden {{ display: none !important; }}
</style>
</head>
<body>

<div class="layout">
  <nav class="sidebar">
    <h1>PERIOD SHORTS</h1>
    <ul>{sidebar_items}</ul>
    <div class="sidebar-footer">총 {len(directors)}명 · {total_scripts}개 스크립트<br>생성: {generated_at}</div>
  </nav>

  <main class="main">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="감독 이름, 키워드로 검색..." oninput="search(this.value)">
    </div>
    {cards}
  </main>
</div>

<script>
function search(query) {{
  query = query.trim().toLowerCase();
  document.querySelectorAll('.script-card').forEach(card => {{
    const text = card.textContent.toLowerCase();
    card.classList.toggle('hidden', query.length > 0 && !text.includes(query));
  }});
  document.querySelectorAll('.director-section').forEach(section => {{
    const visibleCards = section.querySelectorAll('.script-card:not(.hidden)');
    section.classList.toggle('hidden', query.length > 0 && visibleCards.length === 0);
  }});
}}
</script>

</body>
</html>"""
    return html


def main():
    rows = get_data()
    html = build_html(rows)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"완료: {OUTPUT_PATH}")
    print(f"브라우저에서 파일을 열어 확인하세요.")


if __name__ == '__main__':
    main()
