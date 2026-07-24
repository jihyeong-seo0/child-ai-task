# =========================================================
# main.py : 인지과제 페이지 (첫 화면)
# - 학년별 인지과제 10문제를 한 문제씩 풀어 갑니다.
# - 10분 타이머가 끝나면 더 이상 답을 쓸 수 없습니다.
# - 막히면 아래 AI 대화 칸에서 힌트를 물어볼 수 있어요. (정답은 알려주지 않아요)
# =========================================================

import streamlit as st
import common                    # 두 페이지가 함께 쓰는 공통 기능
import supabase_db               # Supabase 저장 기능
from tasks import 문제은행, 영상주소   # 학년별 인지과제 문제 모음 / 영상 주소


# 1) 페이지 기본 설정 --------------------------------------
st.set_page_config(page_title="인지과제", page_icon="🧠")

페이지키 = "인지과제"

# 2) 세션(기억 장치) 준비 + 사이드바에 학생 정보 그리기 ----
#    - 이름과 학년은 한 번만 입력하면 다른 페이지에도 그대로 이어집니다.
common.세션_준비()
이름, 학년 = common.학생정보_사이드바(페이지키)

버전 = st.session_state["_ver"]   # 초기화하면 올라가는 번호 (입력칸 비우기에 사용)


# 3) 화면 머리글 (날짜 + 제목) -----------------------------
#    - 창의적 글쓰기 페이지와 똑같은 모양으로 나옵니다.
common.페이지_머리글(
    "🧠", "인지과제",
    "한 문제씩 차근차근 풀어 보세요. 어려우면 아래 AI 선생님에게 힌트를 물어봐도 좋아요.",
)


# 4) 10분 타이머 -------------------------------------------
#    - '시작'을 누르면 10분이 흘러갑니다.
#    - 시간이 끝나면 종료=True 가 되어 답을 쓸 수 없게 됩니다.
남은초, 종료 = common.타이머(페이지키, 분=10)


# 5) 학년을 바꾸면 1번 문제부터 다시 시작 ------------------
if "문제번호" not in st.session_state:
    st.session_state["문제번호"] = 0
if st.session_state.get("이전학년") != 학년:
    st.session_state["이전학년"] = 학년
    st.session_state["문제번호"] = 0


st.divider()


# =========================================================
# 6) [첫 번째 칸] 인지과제 - 문제와 정답 작성
# =========================================================
st.header("📝 정답 작성 칸")

문제목록 = 문제은행[학년]
총문제수 = len(문제목록)
번호 = st.session_state["문제번호"]
현재문제 = 문제목록[번호]

# 진행 상황 표시 (예: 3 / 10)
st.caption(f"{학년} · 문제 {번호 + 1} / {총문제수}")
st.progress((번호 + 1) / 총문제수)

# 문제 보여 주기 (유형에 따라 다르게 그립니다)
유형 = 현재문제.get("유형", "글")

# (1) 영상 문제라면 영상을 먼저 보여 줍니다.
if 유형 == "영상":
    주소 = 영상주소.get(현재문제.get("영상키", ""), "")
    if 주소:
        st.video(주소)
    else:
        st.warning(
            "🎬 아직 영상이 등록되지 않았어요.\n\n"
            "(연구자용 안내: tasks.py 파일 위쪽 '영상주소'에 유튜브 주소를 넣어 주세요.)"
        )

# (2) 문제 글
st.info(f"**Q{번호 + 1}.**  〔{유형} 문제〕\n\n{현재문제['문제']}")

# (3) 블록 문제라면 그림을 크게 보여 줍니다.
if 현재문제.get("그림"):
    그림_html = 현재문제["그림"].replace("\n", "<br>")
    st.markdown(
        f"""
        <div style="background:#f7f7f9; border:1px solid #e3e3e8; border-radius:10px;
                    padding:16px; margin:6px 0 12px 0; text-align:center;
                    font-family:'D2Coding','Courier New',monospace;
                    font-size:22px; line-height:1.6; white-space:nowrap;
                    overflow-x:auto;">
        {그림_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# 이전에 저장한 답이 있으면 불러와서 보여 줍니다.
이전답 = ""
if 이름 and 이름 in st.session_state["records"]:
    이전답 = st.session_state["records"][이름]["인지과제"].get(번호, "")

# 정답 입력칸 (시간이 끝나면 disabled=True 로 잠깁니다)
내답 = st.text_area(
    "정답을 입력하세요",
    value=이전답,
    height=110,
    key=f"답_{학년}_{번호}_{버전}",
    placeholder="답과 함께, 어떻게 생각했는지도 적어 보세요.",
    disabled=종료,
)
st.caption("💡 답을 모르겠으면 **'모르겠다'** 라고 적어 주세요. "
           "문제를 넘기면 답은 **자동으로 저장**돼요.")

# 시간이 끝났는데 아직 저장하지 않은 답이 있으면, 사라지지 않도록 자동으로 저장합니다.
답키 = f"답_{학년}_{번호}_{버전}"
현재값 = st.session_state.get(답키, 내답) or ""
자동키 = f"_자동저장_{학년}_{번호}"
if 종료 and 이름 and 현재값.strip() and 현재값 != 이전답 and not st.session_state.get(자동키):
    common.이름_저장공간_준비(이름, 학년)
    st.session_state["records"][이름]["인지과제"][번호] = 현재값
    st.session_state[자동키] = True
    이전답 = 현재값
    # 시간이 끝났을 때도 AI 1차 채점을 자동으로 한 번 실행합니다.
    if not st.session_state.get("_종료채점됨"):
        st.session_state["_종료채점됨"] = True
        try:
            common.AI_1차채점(이름, 문제은행, 표시문구="정리하는 중이에요...")
        except TypeError:      # common.py 가 옛 버전일 때 대비
            common.AI_1차채점(이름, 문제은행)
    supabase_db.자동저장(이름)      # Supabase에도 저장
    st.info("⏰ 시간이 끝나서, 지금까지 쓴 답을 자동으로 저장했어요.")


# 답을 저장해 주는 도우미 함수
def 답_저장하기(안내=False):
    """지금 쓴 답을 저장하고 Supabase에도 올립니다. (버튼을 누르지 않아도 자동 실행)"""
    if 종료 or not 이름 or not 내답.strip():
        return False
    common.이름_저장공간_준비(이름, 학년)
    st.session_state["records"][이름]["인지과제"][번호] = 내답
    supabase_db.자동저장(이름)      # Supabase에도 바로 저장
    if 안내:
        st.success(f"{번호 + 1}번 문제의 답이 저장되었어요! 👍")
    return True


# 7) 왼쪽 / 오른쪽 이동 버튼 -------------------------------
#    - 문제를 넘길 때 답이 '자동으로' 저장됩니다. (따로 저장 버튼을 누르지 않아도 돼요)
왼쪽칸, 가운데칸, 오른쪽칸 = st.columns([1, 2, 1])

with 왼쪽칸:
    # 첫 문제에서는 '이전' 버튼을 누를 수 없습니다.
    if st.button("⬅️ 이전 문제", disabled=(번호 == 0), use_container_width=True):
        답_저장하기()                      # 쓰던 답을 자동 저장
        st.session_state["문제번호"] -= 1
        st.rerun()

with 가운데칸:
    if 이름 and 이름 in st.session_state["records"]:
        푼개수 = len(st.session_state["records"][이름]["인지과제"])
        st.caption(f"✅ 저장된 답: {푼개수} / {총문제수}")

with 오른쪽칸:
    # 마지막 문제에서는 '다음' 버튼을 누를 수 없습니다.
    if st.button("다음 문제 ➡️", disabled=(번호 == 총문제수 - 1), use_container_width=True):
        if not 내답.strip():
            st.warning("⚠️ 답을 적어야 다음 문제로 넘어갈 수 있어요. 모르겠으면 '모르겠다'라고 적어 주세요.")
        else:
            답_저장하기()                  # 넘어가면서 자동 저장
            st.session_state["문제번호"] += 1
            st.rerun()


# 8) 마지막 문제에서 '최종 제출' ---------------------------
제출키 = "_최종제출_인지과제"

if 번호 == 총문제수 - 1:
    st.write("")
    if st.button("✅ 최종 제출하기", type="primary", use_container_width=True, disabled=종료):
        if not 이름:
            st.warning("먼저 사이드바에서 이름을 입력해 주세요.")
        elif not 내답.strip():
            st.warning("마지막 문제의 답을 적어 주세요. 모르겠으면 '모르겠다'라고 적어도 괜찮아요.")
        else:
            답_저장하기()                  # 마지막 답까지 저장
            푼개수 = len(st.session_state["records"][이름]["인지과제"])
            # AI 1차 채점을 자동으로 실행합니다.
            # (채점 결과는 학생에게 보이지 않고 데이터베이스에만 저장돼요)
            try:
                common.AI_1차채점(이름, 문제은행, 표시문구="제출하는 중이에요...")
            except TypeError:  # common.py 가 옛 버전일 때 대비
                common.AI_1차채점(이름, 문제은행)
            성공, 메시지 = supabase_db.학생저장(이름, 조용히=True)
            st.session_state[제출키] = True
            if 성공:
                st.success(f"🎉 제출 완료! 모두 {푼개수}문항이 저장되었어요. 수고했어요!")
                st.balloons()
            else:
                st.warning(
                    f"답은 저장했지만 온라인 저장에 문제가 있었어요.\n\n{메시지}\n\n"
                    "선생님(연구자)께 알려 주세요."
                )

if st.session_state.get(제출키):
    st.info("✅ 이미 최종 제출했어요. 답을 고치면 다시 제출해 주세요.")


st.divider()


# =========================================================
# 8) [두 번째 칸] 생성형 AI 대화 칸
#    - 지금 풀고 있는 문제를 AI가 알고 힌트를 줍니다. (정답은 절대 알려주지 않아요)
# =========================================================
st.header("🤖 생성형 AI 대화 칸")
st.caption("정답을 물어봐도 알려주지 않아요. 대신 어떻게 생각하면 좋을지 도와줍니다.")

common.AI대화칸(
    페이지키=페이지키,
    이름=이름,
    학년=학년,
    문제_설명=f"Q{번호 + 1}. {현재문제['문제']}",
)


# 9) 사이드바 - 연구자 패널 --------------------------------
#    - 암호 '0000'을 입력해야 기록을 엑셀로 내려받거나 지울 수 있습니다.
common.연구자_패널(페이지키, 문제은행)
