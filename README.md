1. 개요

1.1 목적

모바일 환경에서 사용자가 쉽게 단어를 수집·저장·복습할 수 있도록 지원하는 개인 맞춤형 단어장 서비스 제공. 사진·드래그·음성 입력을 통해 얻은 영단어를 자동으로 텍스트화하고 DB에 저장하여, 카드·목록 형태로 언제든지 확인·학습할 수 있게 함.


1.2 핵심 가치 제안


언제·어디서든 단어 캡처 – 사진 OCR, 드래그‑공유, 음성인식 3가지 입력 방식 지원

자동 정의·예문 제공 – 외부 사전 API 연동으로 단어 의미·예문을 바로 저장

플래시카드·목록 뷰 – 학습 효율을 높이는 카드 플립·리스트 UI 제공

오프라인 학습 – 로컬 DB에 저장된 단어는 인터넷 연결이 없어도 복습 가능



2. 기술 스택

Frontend


React Native (Expo)

UI 라이브러리: React Native Paper / Styled‑Components

상태 관리: Redux Toolkit + RTK Query

이미지·음성 처리: Expo‑Camera, Expo‑Audio, react‑native‑vision‑camera, react‑native‑speech‑to‑text


Backend


Node.js + Express (서버리스 함수 형태)

이미지 OCR: Google Cloud Vision API

사전 정의 조회: Oxford Dictionaries API / Merriam‑Webster API

음성 → 텍스트: Google Speech‑to‑Text API


Hosting


Firebase Hosting (정적 파일)

Firebase Cloud Functions (Express API 엔드포인트)

Firebase Authentication (이메일/구글 로그인)


DB


Firebase Firestore – 사용자·단어 메타데이터 동기화

SQLite (expo‑sqlite) – 오프라인 복습용 로컬 저장소 (주기적 동기화)



3. 화면별 UI 구성

Home (대시보드)


Header: 현재 로그인 사용자 표시·설정 아이콘

WordStatCard: 오늘 저장된 단어 수·누적 단어 수 시각화

AddWordButton: ‘+’ 아이콘 → 캡처/드래그/음성 입력 선택 모달 오픈

WordListPreview: 최근 저장 5개 단어 미리보기 (카드 형태)


동작(Behavior)


화면 로드 시 Firestore → 사용자의 단어 통계 fetch.

AddWordButton 클릭 → AddWordModal 열림 → 3가지 입력 방식 중 선택.

단어 저장 후 WordStatCard와 WordListPreview 실시간 업데이트.


상태(States)


Loading – 통계·리스트 로드 중 스피너 표시.

Empty – 저장된 단어가 없을 경우 “아직 단어가 없어요” 안내 메시지.



AddWordModal (단어 추가 선택 모달)


OptionButton(Capture Image): 카메라 화면으로 이동

OptionButton(Drag & Share): 시스템 공유 수신 화면으로 이동

OptionButton(Voice Search): 음성 입력 화면으로 이동


동작


사용자가 선택한 옵션에 따라 해당 서브 화면으로 네비게이션.


상태


Idle – 옵션 선택 대기.

Processing – 이미지·음성 전송 중 로딩 표시.



CaptureScreen (사진 촬영 → OCR)


CameraView: 실시간 미리보기 + 촬영 버튼

CropOverlay: 사용자가 직접 영역 지정 가능

ResultPreview: OCR 결과 텍스트 리스트, 선택/수정 가능


동작


촬영 → 사진 전송 → Cloud Vision OCR 호출.

OCR 결과 반환 → 사용자가 원하는 단어 선택 후 SaveWordFlow 진행.


상태


Scanning – 사진 전송·분석 중.

ResultReady – OCR 결과 표시.



DragShareScreen (공유받은 텍스트 처리)


SharedTextView: 시스템 공유로 받은 원문 텍스트 표시

WordExtractor: 자동으로 영어 단어 추출(정규식) + 체크박스 리스트

ConfirmButton: 선택 단어 저장 트리거


동작


공유받은 텍스트 자동 파싱 → 리스트 표시.

사용자가 체크한 단어만 저장.


상태


Parsing – 텍스트 분석 중.

Ready – 추출 결과 확인 가능.



VoiceSearchScreen (음성 인식 → 단어 선택)


MicButton: 음성 녹음 시작/종료

TranscribedText: 실시간 텍스트 변환 결과 표시

CandidateList: 인식된 단어 후보 리스트


동작


사용자가 음성 입력 → Speech‑to‑Text → 후보 단어 리스트 생성.

후보 선택 → SaveWordFlow 로 이동.


상태


Listening – 마이크 활성화 중.

Transcribing – 음성→텍스트 변환 중.



WordListScreen (단어 목록)


SearchBar: 키워드 검색

WordItem: 단어·뜻·예문 요약 표시, 클릭 시 상세 카드 화면 이동

SortToggle: 최근 저장 / 알파벳 순 정렬


동작


리스트 로드 → Firestore/SQLite 동기화.

검색어 입력 → 실시간 필터링.


상태


Loading – 데이터 로드 중.

Empty – 검색 결과 없음 안내.



WordCardScreen (플래시카드 형태 상세)


FrontSide: 단어와 이미지(있을 경우)

BackSide: 의미·예문·제작일·태그

FlipButton: 앞↔뒤 전환 애니메이션

EditButton: 단어·뜻·예문 수정 모달

DeleteButton: 삭제 확인 팝업


동작


카드를 탭 → 플립.

편집/삭제 시 로컬 DB와 Firestore 동기화.


상태


Viewing – 플립 전/후 상태.

Editing – 편집 모드.



4. API 설계

OCR 이미지 분석 API

로직


클라이언트가 이미지 파일(베이스64) 전송.

Cloud Vision API 호출 → 텍스트 추출.

추출된 텍스트 문자열을 JSON 형태로 반환.


Request JSON

{
  "imageBase64": "<BASE64_ENCODED_IMAGE>"
}

Response JSON

{
  "text": "Extracted raw text from image",
  "words": ["example", "capture", "react"],
  "confidence": 0.94
}


단어 정의 조회 API

로직


단어 문자열을 받아 외부 사전 API(Oxford) 호출.

의미·예문·발음 URL을 파싱.

필요한 필드만 정제하여 반환.


Request JSON

{
  "word": "serendipity"
}

Response JSON

{
  "word": "serendipity",
  "definition": "the occurrence and development of events by chance in a happy or beneficial way",
  "example": "A fortunate serendipity",
  "pronunciationUrl": "https://audio.oxforddictionaries.com/en/mp3/serendipity_us_1.mp3"
}


단어 저장 API

로직


클라이언트가 단어 객체(텍스트·정의·예문·이미지URL·태그 등) 전송.

인증된 사용자 UID 확인 후 Firestore words 컬렉션에 문서 생성.

성공 시 저장된 문서 ID 반환.


Request JSON

{
  "word": "ephemeral",
  "definition": "lasting for a very short time",
  "example": "Fame in the entertainment industry can be ephemeral.",
  "imageUrl": "https://storage.googleapis.com/.../ephemeral.jpg",
  "tags": ["adjective", "vocabulary"],
  "source": "ocr"   // ocr | drag | voice
}

Response JSON

{
  "status": "success",
  "docId": "a1B2c3D4e5F6"
}


5. 데이터베이스 설계

users 테이블 (Firestore 컬렉션)

{
  "uid": "string (Firebase Auth UID)",
  "email": "string",
  "displayName": "string",
  "createdAt": "timestamp",
  "lastLogin": "timestamp"
}

words 테이블 (Firestore 컬렉션)

CREATE TABLE words (
    id STRING PRIMARY KEY,          -- Firestore document ID
    uid STRING NOT NULL,            -- 소유자 UID (users.uid)
    word STRING NOT NULL,
    definition STRING,
    example STRING,
    imageUrl STRING,
    tags ARRAY<STRING>,
    source STRING,                  -- 'ocr' | 'drag' | 'voice'
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP
);

local_words (SQLite) – 오프라인 복제

CREATE TABLE local_words (
    id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT,
    example TEXT,
    imagePath TEXT,
    tags TEXT,          -- 콤마 구분 문자열
    source TEXT,
    created_at INTEGER,
    updated_at INTEGER
);


6. 파일 구조

/my-vocab-app
│
├─ /assets                # 아이콘·이미지·폰트
│
├─ /components
│   ├─ Header.js
│   ├─ WordStatCard.js
│   ├─ WordItem.js
│   ├─ WordCard.js
│   └─ ... (공통 UI 컴포넌트)
│
├─ /screens
│   ├─ HomeScreen.js
│   ├─ CaptureScreen.js
│   ├─ DragShareScreen.js
│   ├─ VoiceSearchScreen.js
│   ├─ WordListScreen.js
│   └─ WordCardScreen.js
│
├─ /services
│   ├─ api.js               # RTK Query 설정 / Firebase Functions 호출
│   ├─ ocrService.js        # Cloud Vision 래퍼
│   ├─ dictService.js       # 사전 API 래퍼
│   └─ speechService.js    # Speech‑to‑Text 래퍼
│
├─ /store
│   ├─ index.js
│   ├─ userSlice.js
│   └─ wordsSlice.js
│
├─ /utils
│   ├─ validators.js
│   ├─ formatters.js
│   └─ constants.js
│
├─ App.js
├─ app.json
└─ package.json


7. 비즈니스 정책 및 성공 지표

비즈니스 정책


개인정보 최소 수집 – 사용자의 이메일·UID만 저장, 이미지·음성 데이터는 일회성 처리 후 폐기.

데이터 보관 기간 – 저장된 단어는 사용자가 직접 삭제할 때까지 영구 보관, 비활성 사용자(12개월 미접속) 데이터 자동 삭제.

광고·수익 모델 – 프리미엄 구독 제공 (무제한 저장, 커스텀 테마, 광고 제거).

접근성 – 다크모드, 화면 확대, 텍스트‑음성 변환(TTS) 지원.


성공 지표 (KPIs)

지표	목표 (1년)	측정 방법
월간 활성 사용자 (MAU)	30,000명	Firebase Analytics
일일 저장 단어 수 (DW)	5,000개	Firestore words 컬렉션 write count
사용자당 평균 단어 저장 수	120개	Firestore aggregation
프리미엄 전환율	4%	결제 API 로그
사용자 유지율 (30일)	45%	Cohort 분석
OCR·음성 인식 정확도	≥ 92%	내부 테스트 스크립트 (precision/recall)
평균 단어 복습 세션 시간	5분	화면 체류 시간 로그
