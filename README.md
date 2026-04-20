# 🇨🇳 LexiChinese — LLM 기반 인터랙티브 중국어 관용어 학습 플랫폼

> **논문**: "LLM 기반 인터랙티브 중국어 관용어 학습 플랫폼 LexiChinese의 설계와 활용"  
> **저자**: OOO

한국어를 모국어로 하는 중국어 학습자를 위한 **관용어(성어·헐후어·속담·개념적 은유)** 인터랙티브 학습 플랫폼입니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **① 관용어 의미 탐색기** | 5단계 구조 분석 (문자적 의미 → 비유적 의미 → 유래 → 현대 용법 → 한국어 대응) |
| **② 예문 생성기** | HSK 수준별 맞춤 예문 생성 + 한국어 브릿지 표현 |
| **③ 퀴즈 자동 생성기** | 의미 선택형(T1) · 용례 판단형(T2) · 한국어 유사 표현형(T3) |

### 모드
- 🎓 **학습자 모드** — 기본 학습 기능
- 👨‍🏫 **교사 모드** — 수업 자료 다운로드 + Claude 보충 분석 + AI 함정 분석

---

## 🚀 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/karmalet-DS/LexiChinese.git
cd LexiChinese
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. API 키 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고, **본인의 API 키**를 입력하세요.

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
OPENAI_API_KEY=sk-proj-여기에_본인의_OpenAI_API_키를_입력
ANTHROPIC_API_KEY=sk-ant-api03-여기에_본인의_Anthropic_API_키를_입력
```

> **⚠️ API 키 발급 안내**
> - OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
> - Anthropic: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
> 
> 두 API 중 하나만 있어도 사용 가능합니다. 앱 사이드바에서 사용할 모델을 선택하세요.

### 4. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`이 자동으로 열립니다.

---

## 📁 프로젝트 구조

```
LexiChinese/
├── app.py              # Streamlit 메인 앱
├── utils/
│   ├── llm.py          # LLM 호출 유틸리티 (OpenAI / Anthropic)
│   └── prompts.py      # 프롬프트 템플릿 (T1·T2·T3 기반)
├── requirements.txt    # Python 의존성
├── .env.example        # API 키 설정 템플릿
└── README.md
```


---

## 📄 라이선스

본 프로젝트는 학술 연구 목적으로 공개되었습니다.

---

## 📬 문의

- **박민준** — 덕성여자대학교 중어중문학전공
