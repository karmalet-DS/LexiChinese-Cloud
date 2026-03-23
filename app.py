"""
LexiChinese — LLM 기반 인터랙티브 중국어 관용어 학습 플랫폼
박민준 교수 (덕성여자대학교) × 김박사

핵심 기능:
  ① 관용어 의미 탐색기 (Idiom Explorer)
  ② 예문 생성기 (Example Generator)
  ③ 퀴즈 자동 생성기 (Quiz Generator)

모드 차이:
  🎓 학습자 모드 — 기본 기능 + 다운로드
  👨‍🏫 교사 모드  — 기본 기능 + 다운로드 + "학생들이 틀리기 쉬운 함정" 보충 교안
"""

import os
import streamlit as st
from dotenv import load_dotenv
from utils.llm import call_llm
from utils.prompts import (
    EXPLORER_SYSTEM, EXPLORER_USER, EXPLORER_DEEP_USER,
    EXAMPLE_SYSTEM, EXAMPLE_USER,
    QUIZ_SYSTEM, QUIZ_MEANING_USER, QUIZ_CONTEXT_USER, QUIZ_KOREAN_USER,
    CONTEXTUAL_CHECK_SYSTEM, CONTEXTUAL_CHECK_USER,
)
from utils.hsk_vocab import sample_vocab_text, vocab_count

load_dotenv()

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LexiChinese 🀄",
    page_icon="🀄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Session State 초기화
# ─────────────────────────────────────────────
_state_keys = [
    "explorer_result", "explorer_result_deep",
    "explorer_result_c", "explorer_result_g",
    "explorer_expr", "explorer_view_mode",
    "ctx_result",
    "example_result", "example_expr", "example_hsk",
    "quiz_result", "quiz_expr",
    "trap_explorer", "trap_example", "trap_quiz",
    "quiz_show_answer",
]
for key in _state_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', 'Noto Sans SC', sans-serif; }
.main-title {
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #C0392B, #E74C3C, #F39C12);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -1px; margin-bottom: 0;
}
.sub-title { font-size: 1rem; color: #7f8c8d; margin-top: -8px; margin-bottom: 24px; }
.model-badge-gpt { background-color: #10a37f; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.model-badge-claude { background-color: #d97706; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.korean-bridge { background-color: #eef2ff; border-left: 3px solid #4f46e5; padding: 10px 14px; border-radius: 0 8px 8px 0; margin: 8px 0; }
.trap-box { background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 14px 16px; border-radius: 0 8px 8px 0; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    mode = st.radio("🎭 모드", ["🎓 학습자 모드", "👨‍🏫 교사 모드"], index=0)

    if "교사" in mode:
        st.info("📌 교사 모드: 각 탭에서 **학생들이 틀리기 쉬운 함정** 보충 교안이 추가됩니다.")

    st.divider()
    # API 키는 Streamlit Secrets 또는 환경변수에서 서버사이드로만 로드 (UI 노출 금지)
    openai_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    anthropic_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

    st.markdown("### 🤖 모델 설정")
    st.caption("Claude(기본) + GPT(심화)")
    claude_model = st.selectbox("Claude 모델", ["claude-4-sonnet-20250514", "claude-3-haiku-20240307"], index=0)
    gpt_model = st.selectbox("GPT 모델", ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"], index=0)
    st.divider()
    st.markdown(
        "<div style='text-align:center; color:#aaa; font-size:0.8rem;'>"
        "LexiChinese v1.3</div>",
        unsafe_allow_html=True,
    )

is_teacher = "교사" in mode

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">🀄 LexiChinese</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">LLM 기반 인터랙티브 중국어 관용어 학습 플랫폼 — 성어 · 헐후어 · 속담 · 개념적 은유</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# LLM 호출 헬퍼
# ─────────────────────────────────────────────
def call_gpt(system: str, user: str) -> str:
    if not openai_key:
        return "⚠️ OpenAI API 키가 서버에 설정되지 않았습니다. 관리자에게 문의하세요."
    return call_llm(system, user, "OpenAI", openai_key, gpt_model)

def call_claude_fn(system: str, user: str) -> str:
    if not anthropic_key:
        return "⚠️ Anthropic API 키가 서버에 설정되지 않았습니다. 관리자에게 문의하세요."
    return call_llm(system, user, "Anthropic", anthropic_key, claude_model)

# ─────────────────────────────────────────────
# 공통: 학생 함정 분석 (교사 모드 전용)
# ─────────────────────────────────────────────
TRAP_SYSTEM = (
    "당신은 중국어 비유 표현 교육 전문가입니다. "
    "학생들이 이 표현을 학습할 때 틀리기 쉬운 함정을 분석하고, "
    "교사가 수업에서 활용할 수 있는 보충 교안을 작성해 주세요. "
    "반드시 한국어로 응답하세요."
)

def generate_trap_analysis(expression: str) -> str:
    return call_claude_fn(
        TRAP_SYSTEM,
        f"다음 중국어 비유 표현에 대해 **학생들이 틀리기 쉬운 함정**을 분석하고 보충 교안을 작성하세요.\n\n"
        f"**표현**: {expression}\n\n"
        f"## 작성 구조:\n"
        f"### ⚠️ 학생들이 틀리기 쉬운 함정\n"
        f"1. **문자적 의미 함정**: 글자 그대로 해석하여 비유적 의미를 놓치는 경우\n"
        f"2. **유사 표현 혼동**: 비슷하지만 다른 의미의 성어/관용어와 혼동하는 경우\n"
        f"3. **한국어 대응 오류**: 잘못된 한국어 표현으로 대응하기 쉬운 경우\n"
        f"4. **사용 맥락 오류**: 부적절한 상황에서 사용하기 쉬운 경우\n\n"
        f"### 📋 보충 교안 제안\n"
        f"- 이 함정들을 수업에서 어떻게 다루면 좋을지 구체적 활동 제안 (2~3개)",
    )

def show_trap_section(expression: str, state_key: str):
    """교사 모드 전용: 학생 함정 분석 표시"""
    st.divider()
    st.markdown("#### 👨‍🏫 보충 교안: 학생들이 틀리기 쉬운 함정")
    trap_btn = st.button("⚠️ 함정 분석 생성", key=f"trap_btn_{state_key}")

    if trap_btn and expression:
        with st.spinner("학생 함정 분석 중 (Claude)..."):
            st.session_state[state_key] = generate_trap_analysis(expression)

    if st.session_state.get(state_key):
        st.markdown(
            f'<div class="trap-box">{""}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state[state_key])

# ─────────────────────────────────────────────
# 메인 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🔍 관용어 의미 탐색기",
    "📝 예문 생성기",
    "🧩 퀴즈 생성기",
])

# ═════════════════════════════════════════════
# TAB 1: 관용어 의미 탐색기 (Idiom Explorer)
# ═════════════════════════════════════════════
with tab1:
    st.markdown("### 🔍 관용어 의미 탐색기")
    st.caption("중국어 비유 표현을 입력하면 문자적 의미 → 비유적 의미 → 유래 → 용법 → 한국어 대응의 5단계 분석을 제공합니다.")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        expr_input = st.text_input(
            "중국어 표현 입력",
            placeholder="예: 守株待兔, 画蛇添足, 龙船装狗屎—又臭又长, 人生是旅途",
            label_visibility="collapsed",
            key="explorer_input",
        )
    with col_btn:
        explore_btn = st.button("🔍 탐색", use_container_width=True, type="primary")

    view_mode = st.radio(
        "보기 모드",
        ["📋 기본 (Claude)", "🔬 심화 (GPT)", "⚔️ 나란히 비교"],
        horizontal=True,
        key="explorer_view",
    )

    if explore_btn and expr_input:
        st.session_state["explorer_expr"] = expr_input
        st.session_state["explorer_view_mode"] = view_mode
        st.session_state["ctx_result"] = None
        st.session_state["trap_explorer"] = None

        if view_mode == "📋 기본 (Claude)":
            with st.spinner("Claude가 분석 중..."):
                st.session_state["explorer_result"] = call_claude_fn(
                    EXPLORER_SYSTEM, EXPLORER_USER.format(expression=expr_input))
        elif view_mode == "🔬 심화 (GPT)":
            with st.spinner("GPT가 심화 분석 중..."):
                st.session_state["explorer_result"] = call_gpt(
                    EXPLORER_SYSTEM, EXPLORER_USER.format(expression=expr_input))
                st.session_state["explorer_result_deep"] = call_gpt(
                    EXPLORER_SYSTEM, EXPLORER_DEEP_USER.format(expression=expr_input))
        else:
            with st.spinner("Claude & GPT 분석 중..."):
                st.session_state["explorer_result_c"] = call_claude_fn(
                    EXPLORER_SYSTEM, EXPLORER_USER.format(expression=expr_input))
                st.session_state["explorer_result_g"] = call_gpt(
                    EXPLORER_SYSTEM, EXPLORER_USER.format(expression=expr_input))

    # 결과 표시
    saved_expr = st.session_state.get("explorer_expr")
    saved_view = st.session_state.get("explorer_view_mode")

    if saved_expr:
        if saved_view == "📋 기본 (Claude)" and st.session_state.get("explorer_result"):
            st.markdown(st.session_state["explorer_result"])
        elif saved_view == "🔬 심화 (GPT)" and st.session_state.get("explorer_result"):
            st.markdown("#### 📋 기본 분석")
            st.markdown(st.session_state["explorer_result"])
            if st.session_state.get("explorer_result_deep"):
                st.divider()
                st.markdown("#### 🔬 심화 분석")
                st.markdown(st.session_state["explorer_result_deep"])
        elif saved_view == "⚔️ 나란히 비교":
            col_c, col_g = st.columns(2)
            with col_c:
                st.markdown('<span class="model-badge-claude">Claude</span>', unsafe_allow_html=True)
                if st.session_state.get("explorer_result_c"):
                    st.markdown(st.session_state["explorer_result_c"])
            with col_g:
                st.markdown('<span class="model-badge-gpt">GPT</span>', unsafe_allow_html=True)
                if st.session_state.get("explorer_result_g"):
                    st.markdown(st.session_state["explorer_result_g"])

        # 용례 판단 연습
        st.divider()
        with st.expander("🎯 용례 판단 연습 (Contextual Check)", expanded=False):
            st.caption("이 표현이 포함된 문장의 적절성을 판단해 보세요.")
            ctx_sentence = st.text_area(
                "분석할 문장을 입력하세요",
                placeholder=f"예: 这个项目不能{saved_expr}。",
                key="ctx_sentence",
            )
            if st.button("📊 용례 분석", key="ctx_btn"):
                if ctx_sentence:
                    with st.spinner("용례 분석 중..."):
                        st.session_state["ctx_result"] = call_claude_fn(
                            CONTEXTUAL_CHECK_SYSTEM,
                            CONTEXTUAL_CHECK_USER.format(expression=saved_expr, sentence=ctx_sentence))
            if st.session_state.get("ctx_result"):
                st.markdown(st.session_state["ctx_result"])

        # 다운로드 (두 모드 모두)
        st.divider()
        download_text = f"# LexiChinese — {saved_expr}\n\n"
        if saved_view == "📋 기본 (Claude)":
            download_text += st.session_state.get("explorer_result", "")
        elif saved_view == "🔬 심화 (GPT)":
            download_text += f"## 기본 분석\n{st.session_state.get('explorer_result', '')}\n\n"
            download_text += f"## 심화 분석\n{st.session_state.get('explorer_result_deep', '')}"
        else:
            download_text += f"## Claude 분석\n{st.session_state.get('explorer_result_c', '')}\n\n"
            download_text += f"## GPT 분석\n{st.session_state.get('explorer_result_g', '')}"

        st.download_button(
            "📥 분석 결과 다운로드 (.md)",
            data=download_text,
            file_name=f"LexiChinese_{saved_expr}.md",
            mime="text/markdown",
        )

        # 교사 모드: 학생 함정 분석
        if is_teacher:
            show_trap_section(saved_expr, "trap_explorer")

# ═════════════════════════════════════════════
# TAB 2: 예문 생성기 (Example Generator)
# ═════════════════════════════════════════════
with tab2:
    st.markdown("### 📝 예문 생성기")
    st.caption("HSK 수준에 맞는 예문을 생성하고, 한국어 대응 표현을 자동 연결합니다.")

    col_ex1, col_ex2, col_ex3 = st.columns([3, 1, 1])
    with col_ex1:
        expr_example = st.text_input(
            "중국어 표현 입력", placeholder="예: 半途而废, 亡羊补牢",
            label_visibility="collapsed", key="example_input")
    with col_ex2:
        hsk_level = st.selectbox("HSK 수준", [3, 4, 5, 6], index=1, key="hsk_level")
    with col_ex3:
        example_model = st.selectbox("모델", ["GPT", "Claude"], index=0, key="example_model")

    if st.button("📝 예문 생성", type="primary", key="example_btn"):
        if expr_example:
            st.session_state["example_expr"] = expr_example
            st.session_state["example_hsk"] = hsk_level
            st.session_state["trap_example"] = None
            model_label = "GPT" if example_model == "GPT" else "Claude"
            call_fn = call_gpt if example_model == "GPT" else call_claude_fn
            with st.spinner(f"HSK {hsk_level}급 수준 예문 생성 중 ({model_label})..."):
                st.session_state["example_result"] = call_fn(
                    EXAMPLE_SYSTEM,
                    EXAMPLE_USER.format(
                        expression=expr_example,
                        hsk_level=hsk_level,
                        vocab_sample=sample_vocab_text(hsk_level, 40),
                        vocab_count=vocab_count(hsk_level)))

    if st.session_state.get("example_result"):
        st.markdown(st.session_state["example_result"])
        bridge_model = st.session_state.get("example_model", "GPT")
        st.markdown(
            '<div class="korean-bridge">'
            '🇰🇷 <strong>한국어 대응 연결 (Korean Bridge)</strong><br>'
            f'위 예문에 포함된 한국어 대응 표현은 {bridge_model}가 자동 생성한 것입니다.'
            '</div>',
            unsafe_allow_html=True,
        )

        # 다운로드 (두 모드 모두)
        st.divider()
        ex_expr = st.session_state.get("example_expr", "")
        ex_hsk = st.session_state.get("example_hsk", 4)
        st.download_button(
            "📥 예문 자료 다운로드 (.md)",
            data=f"# LexiChinese 예문 — {ex_expr} (HSK {ex_hsk}급)\n\n{st.session_state['example_result']}",
            file_name=f"LexiChinese_예문_{ex_expr}_HSK{ex_hsk}.md",
            mime="text/markdown",
        )

        # 교사 모드: 학생 함정 분석
        if is_teacher and ex_expr:
            show_trap_section(ex_expr, "trap_example")

# ═════════════════════════════════════════════
# TAB 3: 퀴즈 자동 생성기 (Quiz Generator)
# ═════════════════════════════════════════════
with tab3:
    st.markdown("### 🧩 퀴즈 자동 생성기")
    st.caption("의미 선택형 · 용례 판단형 · 한국어 유사 표현 선택형 퀴즈를 자동 생성합니다.")

    quiz_type = st.radio(
        "퀴즈 유형",
        ["📖 의미 선택형 (T1)", "📋 용례 판단형 (T2)", "🇰🇷 한국어 유사 표현 선택형 (T3)"],
        horizontal=True, key="quiz_type",
    )
    col_q1, col_q2 = st.columns([4, 1])
    with col_q1:
        expr_quiz = st.text_input(
            "중국어 표현 입력", placeholder="예: 守株待兔",
            label_visibility="collapsed", key="quiz_input",
        )
    with col_q2:
        quiz_model = st.selectbox("모델", ["GPT", "Claude"], index=0, key="quiz_model")

    if st.button("🧩 퀴즈 생성", type="primary", key="quiz_btn"):
        if expr_quiz:
            st.session_state["quiz_expr"] = expr_quiz
            st.session_state["trap_quiz"] = None
            if "의미" in quiz_type:
                prompt = QUIZ_MEANING_USER.format(expression=expr_quiz)
            elif "용례" in quiz_type:
                prompt = QUIZ_CONTEXT_USER.format(expression=expr_quiz)
            else:
                prompt = QUIZ_KOREAN_USER.format(expression=expr_quiz)
            st.session_state["quiz_show_answer"] = False
            call_fn = call_gpt if quiz_model == "GPT" else call_claude_fn
            with st.spinner(f"퀴즈 생성 중 ({quiz_model})..."):
                st.session_state["quiz_result"] = call_fn(QUIZ_SYSTEM, prompt)

    if st.session_state.get("quiz_result"):
        raw = st.session_state["quiz_result"]
        separator = "---ANSWER---"

        if separator in raw:
            question_part, answer_part = raw.split(separator, 1)
        else:
            # fallback: show everything
            question_part = raw
            answer_part = ""

        # 문제 표시
        st.markdown(question_part)

        # 정답 표시
        if is_teacher:
            # 교사 모드: 정답 바로 표시
            if answer_part:
                st.divider()
                st.markdown(answer_part)
        else:
            # 학습자 모드: 버튼으로 정답 확인
            if answer_part:
                st.divider()
                if st.button("🔓 정답 확인", key="quiz_answer_btn"):
                    st.session_state["quiz_show_answer"] = True
                if st.session_state.get("quiz_show_answer"):
                    st.markdown(answer_part)

        # 다운로드 (두 모드 모두, 전체 내용 포함)
        st.divider()
        st.download_button(
            "📥 퀴즈 다운로드 (.md)",
            data=f"# LexiChinese 퀴즈\n\n{raw}",
            file_name=f"LexiChinese_퀴즈.md",
            mime="text/markdown",
        )

        # 교사 모드: 학생 함정 분석
        q_expr = st.session_state.get("quiz_expr", "")
        if is_teacher and q_expr:
            show_trap_section(q_expr, "trap_quiz")
