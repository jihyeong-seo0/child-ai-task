# =========================================================
# 환경오염 해결 아이디어 + 생성형 AI 대화 앱 (Streamlit)
# - Solar API(모델: solar-open2)를 openai 라이브러리로 사용
# - 초보자를 위해 한국어 주석을 최대한 자세히 달았어요.
# =========================================================

# 1) 필요한 라이브러리 불러오기 ----------------------------
import io                                  # 엑셀 파일을 메모리에서 만들 때 사용
import time                                # 타이머(경과 시간 계산)에 사용
import datetime                            # 활동지에 오늘 날짜를 넣을 때 사용
import streamlit as st                     # 화면(웹앱)을 만들어 주는 라이브러리
import streamlit.components.v1 as components  # 실시간 타이머(HTML/JS) 넣을 때 사용
from openai import OpenAI                  # Solar API를 호출할 때 쓰는 라이브러리


# 2) 페이지 기본 설정 --------------------------------------
st.set_page_config(page_title="환경오염 해결 아이디어", page_icon="🌍")


# 3) AI에게 줄 '성격' (시스템 프롬프트) --------------------
SYSTEM_PROMPT = "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해"


# 4) Solar API 연결 클라이언트 만들기 ----------------------
client = OpenAI(
    api_key=st.secrets["SOLAR_API_KEY"],   # 코드에 쓰지 않고 비밀 금고에서 불러옴
    base_url="https://api.upstage.ai/v1",  # Solar API 접속 주소
)


# 5) 사이드바(왼쪽 메뉴) - 이름 / 학년 / 기록 확인 암호 ----
with st.sidebar:
    st.header("학생 정보")

    # 이름: 이 이름이 '하나의 코드(구분자)'가 되어
    #      아이디어/프롬프트/결과물을 이 이름에 묶어 저장합니다.
    name = st.text_input("이름을 입력하세요")

    # 나이(학년): 초등학교 5학년 / 6학년 중에서 선택
    grade = st.radio("나이(학년)를 선택하세요", ["초등학교 5학년", "초등학교 6학년"])

    st.divider()
    # 기록 확인 암호: '4087'을 맞게 입력한 사람만 저장된 기록을 볼 수 있어요.
    암호 = st.text_input("기록 확인 암호", type="password", placeholder="선생님만 입력")
    암호맞음 = (암호 == "4087")


# 6) 화면 맨 위 제목 - 시험지(활동지)처럼, 제목은 정중앙 두 줄
오늘 = datetime.date.today().strftime("%Y년 %m월 %d일")
이름_표시 = name if name else "&nbsp;" * 10  # 이름이 없으면 빈 칸처럼 보이게

st.markdown(
    f"""
    <div style="border:2px solid #2b2b2b; border-radius:10px; padding:18px 22px;
                background:#fafafa; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center;
                  font-size:13px; color:#555; letter-spacing:1px;">
        <span>🌱 환경 · 데이터 수업 활동지</span>
        <span>{오늘}</span>
      </div>
      <div style="border-top:1px dashed #bbb; margin:10px 0;"></div>
      <!-- 제목: 정중앙 정렬 + 매끄럽게 두 줄 (word-break:keep-all 로 단어가 잘리지 않게) -->
      <div style="text-align:center; font-size:27px; font-weight:800; color:#1a1a1a;
                  line-height:1.55; word-break:keep-all;">
        환경오염을 해결하기 위한<br>아이디어를 작성해 주세요
      </div>
      <div style="border-top:1px dashed #bbb; margin:12px 0 10px 0;"></div>
      <div style="display:flex; gap:26px; font-size:15px; color:#333;">
        <span>이름 : <b>{이름_표시}</b></span>
        <span>학년 : <b>{grade}</b></span>
        <span>점수 : ______</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# 7) 세션 상태 준비하기 ------------------------------------
# 세션 상태(session_state)는 새로고침해도 값이 유지되는 '기억 장치'예요.
if "messages" not in st.session_state:      # 진행 중인 대화 (AI가 이전 대화를 기억)
    st.session_state.messages = []
if "records" not in st.session_state:       # 이름별 저장 기록 (이름이 '코드' 역할)
    st.session_state.records = {}
if "timer_start" not in st.session_state:   # 타이머를 시작한 시각 (없으면 None)
    st.session_state.timer_start = None


# 8) 상단 타이머 (10분 카운트다운) -------------------------
TIMER_초 = 600  # 10분 = 600초

# 시작 / 리셋 버튼
버튼1, 버튼2, _ = st.columns([1, 1, 3])
with 버튼1:
    if st.button("⏱ 시작"):
        st.session_state.timer_start = time.time()  # 지금 시각을 기록 -> 카운트다운 시작
with 버튼2:
    if st.button("리셋"):
        st.session_state.timer_start = None          # 다시 10:00 으로

# 남은 시간 계산: 시작했으면 (600 - 흐른 시간), 아니면 그대로 600초
if st.session_state.timer_start is not None:
    흐른시간 = time.time() - st.session_state.timer_start
    남은초 = max(0, int(round(TIMER_초 - 흐른시간)))
    실행중 = 남은초 > 0
else:
    남은초 = TIMER_초
    실행중 = False

# 실제 화면에 보이는 시계는 브라우저(JS)가 1초마다 스스로 줄여서 보여 줍니다.
# -> 채팅을 하는 동안에도 앱이 멈추지 않고 시계가 계속 흐릅니다.
타이머_HTML = f"""
<div style="font-family:-apple-system,'Segoe UI',sans-serif; text-align:center;">
  <div id="disp" style="font-size:46px; font-weight:800; letter-spacing:2px; color:#1a1a1a;">10:00</div>
  <div id="msg" style="font-size:13px; color:#888; margin-top:2px;">남은 시간 (10분)</div>
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
    if(remaining<=0){{ disp.style.color='#c0392b'; msg.textContent='시간 종료!'; }}
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
components.html(타이머_HTML, height=110)


# 9) 이름별 저장 공간을 만들어 주는 도우미 함수 ------------
def 이름_저장공간_준비(학생이름):
    """해당 이름의 저장 공간이 없으면 새로 만들어 줍니다."""
    if 학생이름 not in st.session_state.records:
        st.session_state.records[학생이름] = {
            "학년": grade,   # 선택한 학년
            "아이디어": [],   # 학생이 제출한 아이디어들
            "대화": [],      # (프롬프트, 결과물) 쌍으로 저장되는 AI 대화
        }
    st.session_state.records[학생이름]["학년"] = grade  # 항상 최신 학년으로 갱신


# =========================================================
# 10) [첫 번째 칸] 아이디어 작성 칸
# =========================================================
st.header("✏️ 아이디어 작성 칸")
st.caption("환경오염을 해결할 나만의 아이디어를 자유롭게 적어 보세요.")

아이디어_내용 = st.text_area(
    "나의 아이디어", height=140, placeholder="예) 학교에서 분리수거 게임을 만들어요!"
)

# '아이디어 제출하기' 버튼
if st.button("아이디어 제출하기"):
    if not name:
        st.warning("먼저 사이드바에서 이름을 입력해 주세요.")
    elif not 아이디어_내용.strip():
        st.warning("아이디어 내용을 입력해 주세요.")
    else:
        이름_저장공간_준비(name)
        st.session_state.records[name]["아이디어"].append(아이디어_내용)
        st.success(f"'{name}' 학생의 아이디어가 제출되었어요! 👍")

# 제출한 아이디어는 '암호를 맞게 입력한 사람'만 볼 수 있어요.
if name and name in st.session_state.records and st.session_state.records[name]["아이디어"]:
    if 암호맞음:
        제출된 = st.session_state.records[name]["아이디어"]
        with st.expander(f"📌 '{name}' 학생이 제출한 아이디어 보기 ({len(제출된)}개)"):
            for 번호, 글 in enumerate(제출된, start=1):
                st.write(f"{번호}. {글}")
    else:
        st.info("🔒 제출한 아이디어는 사이드바에 암호를 입력해야 볼 수 있어요.")


st.divider()  # 두 칸을 구분하는 선


# =========================================================
# 11) [두 번째 칸] 생성형 AI 대화 칸
# =========================================================
st.header("🤖 생성형 AI 대화 칸")
st.caption("아이디어에 대해 AI 선생님과 이야기해 보세요.")

# 대화가 길어져도 위쪽 '아이디어 작성 칸'이 사라지지 않도록,
# 대화 내용은 높이가 고정된 '스크롤 상자' 안에서만 흐르게 만듭니다.
대화상자 = st.container(height=420)

with 대화상자:
    for 메시지 in st.session_state.messages:
        with st.chat_message(메시지["role"]):
            st.markdown(메시지["content"])


def 실시간_글자흐름(스트림):
    """AI가 보내주는 조각(chunk)에서 글자만 뽑아 하나씩 내보냅니다."""
    for 조각 in 스트림:
        내용 = 조각.choices[0].delta.content
        if 내용:
            yield 내용


질문 = st.chat_input("메시지를 입력하세요")

if 질문:
    if not name:
        st.warning("사이드바에서 이름을 먼저 입력해 주세요. 이름으로 대화가 저장됩니다.")
        st.stop()

    with 대화상자:
        # 학생 메시지 표시 및 기억
        st.session_state.messages.append({"role": "user", "content": 질문})
        with st.chat_message("user"):
            st.markdown(질문)

        # AI 답변 (말풍선으로 이어서)
        with st.chat_message("assistant"):
            try:
                스트림 = client.chat.completions.create(
                    model="solar-open2",       # 모델 이름은 반드시 이 글자 그대로!
                    messages=(
                        [{"role": "system", "content": SYSTEM_PROMPT}]
                        + st.session_state.messages
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
        st.session_state.messages.append({"role": "assistant", "content": 답변})
        이름_저장공간_준비(name)
        st.session_state.records[name]["대화"].append(
            {"프롬프트": 질문, "결과물": 답변}
        )


# =========================================================
# 12) 기록을 txt / excel 로 만들어 주는 도우미 함수들
# =========================================================
def 기록_txt만들기(대상기록):
    """이름별로 [제출한 아이디어]와 [Solar와의 대화]를 함께 담은 글자를 만듭니다."""
    줄 = []
    for 이름, 정보 in 대상기록.items():
        줄.append(f"이름 : {이름}")
        줄.append(f"학년 : {정보['학년']}")
        줄.append("")
        줄.append("[제출한 아이디어]")
        if 정보["아이디어"]:
            for i, 글 in enumerate(정보["아이디어"], start=1):
                줄.append(f"  {i}. {글}")
        else:
            줄.append("  (없음)")
        줄.append("")
        줄.append("[Solar와의 대화]")
        if 정보["대화"]:
            for i, 쌍 in enumerate(정보["대화"], start=1):
                줄.append(f"  {i}) 학생: {쌍['프롬프트']}")
                줄.append(f"     AI  : {쌍['결과물']}")
        else:
            줄.append("  (없음)")
        줄.append("")
        줄.append("=" * 45)
        줄.append("")
    return "\n".join(줄)


def 기록_excel만들기(대상기록):
    """이름별 아이디어와 대화를 한 표(엑셀 시트)로 정리해서 파일 데이터를 만듭니다."""
    import pandas as pd  # 판다스는 스트림릿 클라우드에 기본 설치되어 있어요.

    행목록 = []
    for 이름, 정보 in 대상기록.items():
        # 아이디어 행
        for i, 글 in enumerate(정보["아이디어"], start=1):
            행목록.append({
                "이름": 이름, "학년": 정보["학년"], "유형": "아이디어",
                "번호": i, "학생 입력(프롬프트)": 글, "AI 답변(결과물)": "",
            })
        # 대화 행
        for i, 쌍 in enumerate(정보["대화"], start=1):
            행목록.append({
                "이름": 이름, "학년": 정보["학년"], "유형": "대화",
                "번호": i, "학생 입력(프롬프트)": 쌍["프롬프트"], "AI 답변(결과물)": 쌍["결과물"],
            })

    표 = pd.DataFrame(
        행목록,
        columns=["이름", "학년", "유형", "번호", "학생 입력(프롬프트)", "AI 답변(결과물)"],
    )
    저장통 = io.BytesIO()                       # 파일을 메모리에 만들기
    표.to_excel(저장통, index=False, engine="openpyxl")
    return 저장통.getvalue()


# =========================================================
# 13) 사이드바 아래쪽 - 암호를 맞힌 사람만 기록 내려받기
# =========================================================
with st.sidebar:
    st.divider()
    st.subheader("저장된 기록 (선생님용)")

    if not 암호맞음:
        st.caption("🔒 기록을 보려면 위의 '기록 확인 암호'를 바르게 입력하세요.")
    elif not st.session_state.records:
        st.caption("아직 저장된 기록이 없어요.")
    else:
        # 어떤 학생 기록을 내려받을지 선택 ('(전체)'면 모든 학생)
        이름목록 = ["(전체)"] + list(st.session_state.records.keys())
        선택 = st.selectbox("학생 선택", 이름목록)

        if 선택 == "(전체)":
            대상 = st.session_state.records
            파일이름 = "환경수업_전체기록"
        else:
            대상 = {선택: st.session_state.records[선택]}
            파일이름 = f"{선택}_기록"

        # txt 로 내려받기
        st.download_button(
            label="📄 TXT 로 내려받기",
            data=기록_txt만들기(대상),
            file_name=f"{파일이름}.txt",
            mime="text/plain",
        )
        # excel(xlsx) 로 내려받기
        st.download_button(
            label="📊 Excel 로 내려받기",
            data=기록_excel만들기(대상),
            file_name=f"{파일이름}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
