# =========================================================
# common.py : 두 페이지(인지과제 / 창의적 글쓰기)가 함께 쓰는 공통 기능 모음
# - 학생 정보(이름·학년)를 한 번만 입력해도 모든 페이지에서 이어지게 합니다.
# - 10분 타이머, 기록 저장, 기록 내려받기 기능도 여기에 모아 두었어요.
# =========================================================

import io
import csv
import time
import datetime
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ---------------------------------------------------------
# 1) AI에게 줄 '성격' (시스템 프롬프트)
#    - 정답은 절대 알려주지 않고, 스스로 생각하도록 도와주는(비계) 역할입니다.
# ---------------------------------------------------------
SYSTEM_PROMPT = (
    "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해. "
    "정답을 알려달라고 해도 절대 정답을 알려주지 마. 어떤 일이 있어도 정답을 이야기하면 안돼. "
    "대신 학생이 스스로 답을 찾도록 도와줘. 문제를 더 작은 단계로 쪼개 주거나, "
    "무엇부터 생각하면 좋을지 되묻거나, 비슷하지만 더 쉬운 예를 들어 주는 방식으로 도와줘. "
    "최종 답이나 최종 계산 결과는 절대 말하지 말고, 초등학생이 이해할 수 있는 쉬운 말로 설명해."
)


# ---------------------------------------------------------
# 2) Solar API 연결 클라이언트 만들기
# ---------------------------------------------------------
def 클라이언트():
    """Solar API에 연결하는 통로를 만들어 돌려줍니다."""
    return OpenAI(
        api_key=st.secrets["SOLAR_API_KEY"],   # 코드에 쓰지 않고 비밀 금고에서 불러옴
        base_url="https://api.upstage.ai/v1",  # Solar API 접속 주소
    )


# ---------------------------------------------------------
# 3) 세션 상태(기억 장치) 준비하기
#    - 세션 상태는 페이지를 옮겨 다녀도 값이 그대로 남는 '기억 장치'예요.
# ---------------------------------------------------------
def 세션_준비():
    if "_이름" not in st.session_state:
        st.session_state["_이름"] = ""                    # 학생 이름 (페이지 공통)
    if "_학년" not in st.session_state:
        st.session_state["_학년"] = "초등학교 5학년"        # 학년 (페이지 공통)
    if "records" not in st.session_state:
        st.session_state["records"] = {}                  # 이름별 저장 기록
    if "_ver" not in st.session_state:
        st.session_state["_ver"] = 0                      # 입력칸 '버전' (초기화용)


# ---------------------------------------------------------
# 4) 사이드바에 학생 정보(이름·학년)를 그려 주는 함수
#    - 한 페이지에서 입력하면 다른 페이지에도 그대로 이어집니다.
#    - 비밀은 '_이름', '_학년'이라는 저장용 칸에 값을 옮겨 두는 것이에요.
#      (위젯에 붙은 값은 페이지를 옮기면 사라질 수 있어서 따로 보관합니다.)
# ---------------------------------------------------------
def 학생정보_사이드바(페이지키):
    학년목록 = ["초등학교 5학년", "초등학교 6학년"]
    버전 = st.session_state.get("_ver", 0)   # 초기화할 때마다 1씩 올라가는 번호

    with st.sidebar:
        st.header("학생 정보")

        # 이름: 이 이름이 '하나의 코드(구분자)'가 되어
        #      정답과 AI 프롬프트/결과물이 이 이름에 묶여 저장됩니다.
        이름 = st.text_input(
            "이름을 입력하세요",
            value=st.session_state["_이름"],       # 이전에 입력한 값을 그대로 보여 줌
            key=f"이름칸_{페이지키}_{버전}",
        )

        # 나이(학년): 초등학교 5학년 / 6학년 중에서 선택
        학년 = st.radio(
            "나이(학년)를 선택하세요",
            학년목록,
            index=학년목록.index(st.session_state["_학년"]),
            key=f"학년칸_{페이지키}_{버전}",
        )

        # 입력한 값을 공통 보관함에 저장 -> 다른 페이지에서도 그대로 사용
        st.session_state["_이름"] = 이름
        st.session_state["_학년"] = 학년

        if 이름:
            st.success(f"👤 {이름} · {학년}")
        else:
            st.info("이름을 입력하면 모든 페이지에서 함께 사용돼요.")

    return 이름, 학년


# ---------------------------------------------------------
# 5) 10분 타이머
#    - 페이지마다 따로 돌아갑니다. (인지과제 10분, 글쓰기 10분)
#    - 시간이 끝나면 True(종료)를 돌려주어 입력칸을 잠그게 합니다.
# ---------------------------------------------------------
def 타이머(페이지키, 분=10):
    총초 = 분 * 60
    시작키 = f"타이머시작_{페이지키}"
    if 시작키 not in st.session_state:
        st.session_state[시작키] = None   # 아직 시작하지 않음

    버튼1, 버튼2, 버튼3 = st.columns([1, 1, 2])
    with 버튼1:
        if st.button("⏱ 시작", key=f"시작_{페이지키}", use_container_width=True):
            st.session_state[시작키] = time.time()   # 지금 시각 기록 -> 카운트다운 시작
            st.rerun()
    with 버튼2:
        if st.button("리셋", key=f"리셋_{페이지키}", use_container_width=True):
            st.session_state[시작키] = None          # 다시 10:00 으로
            st.rerun()
    with 버튼3:
        # 시간이 다 됐는지 화면에 반영하려면 한 번 새로 그려야 해서 만든 버튼이에요.
        st.button("🔄 남은 시간 확인", key=f"새로고침_{페이지키}", use_container_width=True)

    # 남은 시간 계산
    if st.session_state[시작키] is not None:
        흐른시간 = time.time() - st.session_state[시작키]
        남은초 = max(0, int(round(총초 - 흐른시간)))
        실행중 = 남은초 > 0
        종료 = 남은초 <= 0        # 시작했는데 남은 시간이 0 -> 종료
    else:
        남은초 = 총초
        실행중 = False
        종료 = False

    # 화면 시계는 브라우저(JS)가 1초마다 스스로 줄여서 보여 줍니다.
    시계_HTML = f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif; text-align:center;">
      <div id="disp" style="font-size:44px; font-weight:800; letter-spacing:2px; color:#1a1a1a;">10:00</div>
      <div id="msg" style="font-size:13px; color:#888; margin-top:2px;">남은 시간 ({분}분)</div>
    </div>
    <script>
      let remaining = {남은초};
      const running = {"true" if 실행중 else "false"};
      const disp = document.getElementById('disp');
      const msg  = document.getElementById('msg');
      function fmt(s){{
        const m = Math.floor(s/60), c = s%60;
        return String(m).padStart(2,'0') + ':' + String(c).padStart(2,'0');
      }}
      function render(){{
        disp.textContent = fmt(remaining);
        if(remaining<=0){{
          disp.style.color='#c0392b';
          msg.textContent="시간이 끝났어요! '남은 시간 확인' 버튼을 눌러 주세요.";
        }}
      }}
      render();
      if(running){{
        const id = setInterval(function(){{
          remaining -= 1;
          if(remaining<=0){{ remaining=0; render(); clearInterval(id); }}
          else {{ render(); }}
        }}, 1000);
      }}
    </script>
    """
    components.html(시계_HTML, height=105)

    # 시간이 끝났으면 안내문을 크게 보여 줍니다.
    if 종료:
        st.error("⏰ 10분이 모두 지났어요! 이제 답을 작성하거나 저장할 수 없습니다. 수고했어요 😊")

    return 남은초, 종료


# ---------------------------------------------------------
# 6) 이름별 저장 공간 만들기
# ---------------------------------------------------------
def 이름_저장공간_준비(이름, 학년):
    if 이름 not in st.session_state["records"]:
        st.session_state["records"][이름] = {
            "학년": 학년,
            "인지과제": {},   # {문제번호: 학생이 쓴 답}
            "글쓰기": [],     # 창의적 글쓰기로 제출한 글들
            "대화": [],       # AI와 나눈 대화 (어느 페이지인지도 함께 기록)
        }
    st.session_state["records"][이름]["학년"] = 학년   # 항상 최신 학년으로 갱신


# ---------------------------------------------------------
# 7) AI 대화 칸을 그려 주는 함수 (두 페이지에서 함께 사용)
#    - 문제_설명을 넣어 주면 AI가 그 문제를 알고 힌트를 줄 수 있어요. (정답은 알려주지 않음)
# ---------------------------------------------------------
def AI대화칸(페이지키, 이름, 학년, 문제_설명=None, 높이=380):
    메시지키 = f"messages_{페이지키}"
    if 메시지키 not in st.session_state:
        st.session_state[메시지키] = []

    # 대화가 길어져도 위쪽 내용이 밀려 사라지지 않도록 높이가 고정된 스크롤 상자를 씁니다.
    대화상자 = st.container(height=높이)
    with 대화상자:
        for 메시지 in st.session_state[메시지키]:
            with st.chat_message(메시지["role"]):
                st.markdown(메시지["content"])

    def 실시간_글자흐름(스트림):
        """AI가 보내주는 조각(chunk)에서 글자만 뽑아 하나씩 내보냅니다."""
        for 조각 in 스트림:
            내용 = 조각.choices[0].delta.content
            if 내용:
                yield 내용

    질문 = st.chat_input("메시지를 입력하세요", key=f"입력_{페이지키}")
    if not 질문:
        return

    if not 이름:
        st.warning("사이드바에서 이름을 먼저 입력해 주세요. 이름으로 대화가 저장됩니다.")
        st.stop()

    # AI에게 줄 안내문: 기본 성격 + (있다면) 지금 풀고 있는 문제 내용
    시스템문 = SYSTEM_PROMPT
    if 문제_설명:
        시스템문 += (
            f"\n\n[학생이 지금 풀고 있는 문제]\n{문제_설명}\n"
            "이 문제의 답은 절대 말하지 말고, 생각하는 방법만 도와줘."
        )

    with 대화상자:
        st.session_state[메시지키].append({"role": "user", "content": 질문})
        with st.chat_message("user"):
            st.markdown(질문)

        with st.chat_message("assistant"):
            try:
                스트림 = 클라이언트().chat.completions.create(
                    model="solar-open2",       # 모델 이름은 반드시 이 글자 그대로!
                    messages=(
                        [{"role": "system", "content": 시스템문}]
                        + st.session_state[메시지키]
                    ),
                    stream=True,               # 스트리밍(글자가 실시간으로 흐름)
                    reasoning_effort="none",   # 추론(생각) 끄기 -> 답이 더 빨리 나옴
                )
                답변 = st.write_stream(실시간_글자흐름(스트림))
            except Exception:
                답변 = None
                st.error(
                    "앗, 답변을 가져오는 데 문제가 생겼어요. 😢\n\n"
                    "잠시 후 다시 시도해 주세요. 문제가 계속되면 인터넷 연결이나 "
                    "API 키(SOLAR_API_KEY) 설정을 확인해 주세요."
                )

    if 답변:
        st.session_state[메시지키].append({"role": "assistant", "content": 답변})
        이름_저장공간_준비(이름, 학년)
        st.session_state["records"][이름]["대화"].append(
            {"페이지": 페이지키, "프롬프트": 질문, "결과물": 답변}
        )


# ---------------------------------------------------------
# 8) 현재 작업 초기화 버튼 (저장된 기록은 그대로 남습니다)
#    - 이름칸 / 아이디어칸 / 정답칸 / AI 대화 / 타이머를 모두 비웁니다.
#    - 입력칸의 key 뒤에 붙는 '버전' 번호를 1 올려서, 새 입력칸으로 바꾸는 방식이에요.
# ---------------------------------------------------------
def 초기화_버튼(페이지키):
    with st.sidebar:
        if st.button("🧹 현재 작업 초기화 (기록은 유지)", key=f"초기화_{페이지키}"):
            # 두 페이지의 AI 대화와 타이머를 모두 비웁니다.
            for 키 in list(st.session_state.keys()):
                if str(키).startswith("messages_") or str(키).startswith("타이머시작_"):
                    st.session_state.pop(키, None)
            st.session_state["_이름"] = ""
            st.session_state["_학년"] = "초등학교 5학년"
            st.session_state["문제번호"] = 0
            st.session_state["_ver"] += 1     # 입력칸을 '새것'으로 바꿔 비웁니다.
            st.rerun()


# ---------------------------------------------------------
# 9) 기록을 보기 좋은 Excel(xlsx)로 만들기
#    - 학생마다 시트를 나누고, [제출한 아이디어] -> [AI 대화] -> [인지과제 정답] 순서로 정리
# ---------------------------------------------------------
def _시트이름(원본, 사용중):
    """엑셀 시트 이름에 쓸 수 없는 글자를 지우고, 31자 제한/중복을 처리합니다."""
    금지 = '[]:*?/\\'
    이름 = "".join(c for c in 원본 if c not in 금지).strip() or "학생"
    이름 = 이름[:28]
    후보, n = 이름, 1
    while 후보 in 사용중:
        n += 1
        후보 = f"{이름}_{n}"[:31]
    사용중.add(후보)
    return 후보


def 기록_excel만들기(대상기록, 문제은행):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    wb.remove(wb.active)   # 기본 시트 제거

    선 = Side(style="thin", color="D9D9D9")
    테두리 = Border(left=선, right=선, top=선, bottom=선)
    가운데 = Alignment(horizontal="center", vertical="center", wrap_text=True)
    왼쪽 = Alignment(horizontal="left", vertical="top", wrap_text=True)
    제목폰트 = Font(bold=True, size=14, color="FFFFFF")
    제목채움 = PatternFill("solid", fgColor="2E7D32")
    구획폰트 = Font(bold=True, size=12, color="1B5E20")
    구획채움 = PatternFill("solid", fgColor="E8F5E9")
    헤더폰트 = Font(bold=True, color="FFFFFF")
    헤더채움 = PatternFill("solid", fgColor="66BB6A")
    라벨폰트 = Font(bold=True)

    사용중 = set()
    for 이름, 정보 in 대상기록.items():
        ws = wb.create_sheet(title=_시트이름(이름, 사용중))
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 45
        ws.column_dimensions["D"].width = 50

        def 구획(제목):
            """구획(소제목) 줄을 그려 줍니다."""
            nonlocal r
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
            c = ws.cell(r, 1, 제목)
            c.font, c.fill, c.alignment = 구획폰트, 구획채움, 왼쪽
            r += 1

        def 헤더(칸들):
            """표의 머리글 줄을 그려 줍니다."""
            nonlocal r
            for i, 글 in enumerate(칸들, start=1):
                cc = ws.cell(r, i, 글)
                cc.font, cc.fill, cc.alignment, cc.border = 헤더폰트, 헤더채움, 가운데, 테두리
            r += 1

        def 없음():
            nonlocal r
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
            ws.cell(r, 1, "(내용이 없습니다)").alignment = 왼쪽
            r += 1

        r = 1
        # 큰 제목
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        c = ws.cell(r, 1, "학생 활동 기록")
        c.font, c.fill, c.alignment = 제목폰트, 제목채움, 가운데
        ws.row_dimensions[r].height = 26
        r += 1

        # 이름 / 학년
        for 라벨, 값 in [("이름", 이름), ("학년", 정보.get("학년", ""))]:
            c = ws.cell(r, 1, 라벨); c.font, c.alignment, c.border = 라벨폰트, 가운데, 테두리
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
            ws.cell(r, 2, 값).alignment = 왼쪽
            for col in (2, 3, 4):
                ws.cell(r, col).border = 테두리
            r += 1
        r += 1

        # ── 1. 제출한 아이디어(창의적 글쓰기) ──
        구획("■ 제출한 아이디어 (창의적 글쓰기)")
        헤더(["번호", "내용", "", ""])
        글목록 = 정보.get("글쓰기", [])
        if 글목록:
            for i, 글 in enumerate(글목록, start=1):
                ws.cell(r, 1, i).alignment = 가운데; ws.cell(r, 1).border = 테두리
                ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
                ws.cell(r, 2, 글).alignment = 왼쪽
                for col in (2, 3, 4):
                    ws.cell(r, col).border = 테두리
                r += 1
        else:
            없음()
        r += 1

        # ── 2. 생성형 AI 대화 기록 ──
        구획("■ 생성형 AI 대화 기록")
        헤더(["번호", "페이지", "학생 프롬프트", "AI 답변"])
        대화목록 = 정보.get("대화", [])
        if 대화목록:
            for i, 쌍 in enumerate(대화목록, start=1):
                ws.cell(r, 1, i).alignment = 가운데
                ws.cell(r, 2, 쌍.get("페이지", "")).alignment = 왼쪽
                ws.cell(r, 3, 쌍.get("프롬프트", "")).alignment = 왼쪽
                ws.cell(r, 4, 쌍.get("결과물", "")).alignment = 왼쪽
                for col in (1, 2, 3, 4):
                    ws.cell(r, col).border = 테두리
                r += 1
        else:
            없음()
        r += 1

        # ── 3. 인지과제 정답 ──
        구획("■ 인지과제 정답")
        헤더(["번호", "", "문제", "학생이 쓴 답"])
        답목록 = 정보.get("인지과제", {})
        문제들 = 문제은행.get(정보.get("학년", ""), [])
        if 답목록:
            for 번호 in sorted(답목록.keys()):
                문제글 = 문제들[번호]["문제"].replace("\n", " ") if 번호 < len(문제들) else ""
                ws.cell(r, 1, 번호 + 1).alignment = 가운데
                ws.cell(r, 3, 문제글).alignment = 왼쪽
                ws.cell(r, 4, 답목록[번호]).alignment = 왼쪽
                for col in (1, 2, 3, 4):
                    ws.cell(r, col).border = 테두리
                r += 1
        else:
            없음()

    저장통 = io.BytesIO()
    wb.save(저장통)
    return 저장통.getvalue()


# ---------------------------------------------------------
# 10) 연구자 패널 (사이드바)
#     - 암호 '0000'을 맞게 입력해야 기록을 보거나 내려받거나 지울 수 있습니다.
# ---------------------------------------------------------
def 연구자_패널(페이지키, 문제은행):
    with st.sidebar:
        st.divider()
        st.subheader("저장된 기록 (연구자용)")

        암호 = st.text_input(
            "기록 확인 암호", type="password",
            placeholder="연구자만 입력", key=f"암호_{페이지키}",
        )
        암호맞음 = (암호 == "0000")

        if not 암호맞음:
            st.caption("🔒 기록을 보려면 암호를 바르게 입력하세요.")
            return False

        if not st.session_state["records"]:
            st.caption("아직 저장된 기록이 없어요.")
            return True

        # 어떤 학생 기록을 내려받을지 선택 ('(전체)'면 모든 학생)
        이름목록 = ["(전체)"] + list(st.session_state["records"].keys())
        선택 = st.selectbox("학생 선택", 이름목록, key=f"선택_{페이지키}")

        if 선택 == "(전체)":
            대상 = st.session_state["records"]
            파일이름 = "전체기록"
        else:
            대상 = {선택: st.session_state["records"][선택]}
            파일이름 = f"{선택}_기록"

        st.download_button(
            label="📊 Excel 로 내려받기",
            data=기록_excel만들기(대상, 문제은행),
            file_name=f"{파일이름}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"다운_{페이지키}",
        )

        st.divider()
        st.caption("⚠️ 아래는 저장된 모든 기록을 완전히 지웁니다.")
        동의 = st.checkbox("삭제에 동의합니다", key=f"동의_{페이지키}")
        if st.button("🗑 저장된 기록 전체 삭제", disabled=not 동의, key=f"삭제_{페이지키}"):
            st.session_state["records"] = {}
            st.rerun()

        return True


# ---------------------------------------------------------
# 11) 페이지 머리글 (두 페이지가 똑같은 모양으로 보이게 하는 함수)
#     - 맨 위에 오늘 날짜가 자동으로 들어갑니다.
#     - 아이콘 + 제목 + 설명 순서로 그려집니다.
# ---------------------------------------------------------
def 페이지_머리글(아이콘, 제목, 설명):
    오늘 = datetime.date.today().strftime("%Y년 %m월 %d일")
    st.caption(f"📅 {오늘}")          # 오늘 날짜 (자동)
    st.title(f"{아이콘} {제목}")       # 큰 제목
    st.caption(설명)                  # 제목 아래 설명 한 줄
