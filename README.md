# SensitiveScanner

Pastebin 등 공개 텍스트 데이터에서 API Key, Token, Private Key, 이메일,
IP 주소 등의 민감정보를 탐지하기 위한 Python 기반 스캐너 프로젝트입니다.

현재 프로젝트는 **규칙 기반 정규식 탐지 + 문맥 키워드 기반 신뢰도 조정 +
민감정보 마스킹 + JSON/CSV 결과 저장 + Pastebin 단일 검사 + Pastebin
Batch 검사**까지 구현되어 있습니다.

> ⚠️ 본 프로젝트는 보안 연구 및 허가된 데이터 분석을 목적으로
> 사용합니다. 실제 제3자의 자격증명, API Key, Token 등을 수집하거나
> 악용하지 않도록 주의합니다.

------------------------------------------------------------------------

## 1. 프로젝트 목적

수동으로 공개 텍스트를 하나씩 확인하면서 민감정보 존재 여부를 판단하는
데 많은 시간이 소요되는 문제를 해결하기 위해 제작되었습니다.

프로젝트의 기본적인 처리 흐름은 다음과 같습니다.

``` text
검사 대상 텍스트
      ↓
탐지 규칙 로딩
      ↓
정규식 기반 민감정보 탐지
      ↓
문맥(Context) 확인
      ↓
긍정/부정/강한 부정 키워드 분석
      ↓
최종 신뢰도 산정
      ↓
민감정보 마스킹
      ↓
JSON / CSV 저장
```

Pastebin 연동 시:

``` text
Pastebin URL
      ↓
Paste ID 추출
      ↓
Raw 본문 가져오기
      ↓
SensitiveScanner
      ↓
탐지 결과
      ↓
JSON / CSV
```

Batch 검사에서는:

``` text
input/paste_urls.txt
      ↓
여러 Pastebin URL
      ↓
pastebin_batch.py
      ↓
각 Paste 검사
      ↓
전체 상세 결과
      +
Paste별 요약 결과
```

------------------------------------------------------------------------

## 2. 현재 구현 기능

### 기본 탐지

현재 다음과 같은 탐지 규칙이 구현되어 있습니다.

  종류                설명                          기본 위험도
  ------------------- ----------------------------- -------------
  `EMAIL`             이메일 주소 형식 탐지         MEDIUM
  `IP_ADDRESS`        IPv4 주소 형식 탐지           LOW
  `AWS_ACCESS_KEY`    AWS Access Key 형식 탐지      HIGH
  `JWT`               JWT 형식 문자열 탐지          HIGH
  `GENERIC_API_KEY`   일반적인 API Key 형식 탐지    HIGH
  `BEARER_TOKEN`      HTTP Bearer Token 형식 탐지   HIGH
  `PRIVATE_KEY`       Private Key 헤더 형식 탐지    CRITICAL

규칙은 코드에 직접 작성하지 않고 `rules/*.json` 파일로 분리하여
관리합니다.

------------------------------------------------------------------------

## 3. 프로젝트 구조

현재 프로젝트 구조는 다음과 같습니다.

``` text
SensitiveScanner/
│
├── scanner.py
├── pastebin_loader.py
├── pastebin_batch.py
│
├── input/
│   ├── test.txt
│   └── paste_urls.txt
│
├── output/
│   ├── results.json
│   ├── results.csv
│   ├── batch_summary.json
│   └── batch_summary.csv
│
└── rules/
    ├── api_keys.json
    ├── cloud.json
    ├── credentials.json
    ├── pii.json
    └── tokens.json
```

### 주요 파일 설명

#### `scanner.py`

프로젝트의 핵심 탐지 엔진입니다.

주요 기능:

-   JSON 규칙 로딩
-   파일 텍스트 읽기
-   정규식 기반 탐지
-   탐지 위치 확인
-   문맥 추출
-   긍정 키워드 분석
-   부정 키워드 분석
-   강한 부정 키워드 분석
-   최종 신뢰도 계산
-   민감정보 마스킹
-   JSON 저장
-   CSV 저장

------------------------------------------------------------------------

#### `pastebin_loader.py`

Pastebin의 공개 Paste URL 하나를 입력받아 검사합니다.

처리 과정:

``` text
Pastebin URL
    ↓
Paste ID 추출
    ↓
https://pastebin.com/raw/{PasteID}
    ↓
본문 가져오기
    ↓
scanner.scan_text()
    ↓
탐지 결과 저장
```

------------------------------------------------------------------------

#### `pastebin_batch.py`

여러 개의 Pastebin URL을 순차적으로 검사합니다.

URL 목록은 다음 파일에서 읽습니다.

``` text
input/paste_urls.txt
```

예:

``` text
https://pastebin.com/AAAAAAA
https://pastebin.com/BBBBBBB
https://pastebin.com/CCCCCCC
```

중복 URL은 자동으로 제거됩니다.

------------------------------------------------------------------------

## 4. 탐지 규칙 구조

규칙은 JSON 파일로 관리됩니다.

예를 들어 `GENERIC_API_KEY` 규칙은 API Key 형태를 정규식으로 탐지하고,
주변 문맥에 나타나는 키워드를 이용해 신뢰도를 조정합니다.

개념적인 구조:

``` json
{
    "GENERIC_API_KEY": {
        "pattern": "...",
        "severity": "HIGH",
        "confidence": "MEDIUM",
        "description": "일반적인 API Key 형식의 문자열 탐지",

        "positive_keywords": {
            "api_key": 2,
            "apikey": 2,
            "secret": 2,
            "credential": 2,
            "token": 1
        },

        "negative_keywords": {
            "test": -1,
            "demo": -1
        },

        "strong_negative_keywords": {
            "example": -2,
            "sample": -2,
            "dummy": -2,
            "fake": -2,
            "placeholder": -2
        }
    }
}
```

이를 통해 단순히 문자열이 정규식과 일치하는 것뿐 아니라 주변 문맥도 함께
판단합니다.

------------------------------------------------------------------------

## 5. 신뢰도 분석

현재 스캐너는 기본 신뢰도와 문맥 분석 결과를 이용해 최종 신뢰도를
계산합니다.

예를 들어 테스트용 데이터:

``` text
Example AWS Key:
AKIA...
```

에서는 `example`과 같은 부정 문맥이 발견될 수 있습니다.

반대로:

``` text
AWS_ACCESS_KEY_ID = AKIA...
```

와 같이 실제 자격증명으로 사용될 가능성이 높은 문맥에서는 긍정적인
키워드가 발견될 수 있습니다.

결과에는 다음과 같은 정보가 표시됩니다.

``` text
기본 신뢰도  : HIGH
최종 신뢰도  : MEDIUM

상승 키워드   : aws
강한 하락 키워드 : example

긍정 점수    : +1
부정 점수    : 0
강한 부정 점수 : -2

상태         : REVIEW_REQUIRED
```

자동 탐지 결과를 최종 확정으로 사용하지 않고, `REVIEW_REQUIRED` 상태를
통해 사람이 검토할 수 있도록 설계했습니다.

------------------------------------------------------------------------

## 6. 민감정보 마스킹

탐지된 원본 민감정보는 결과 화면이나 결과 파일에 그대로 저장하지 않고
마스킹합니다.

예:

``` text
원본:
AKIA1234567890ABCDEF

결과:
AKIA************CDEF
```

또한 문맥에 포함된 탐지값도 마스킹하여 출력합니다.

이 방식은 탐지 결과를 확인하면서 실제 비밀값이 불필요하게 노출되는 것을
줄이기 위한 것입니다.

------------------------------------------------------------------------

## 7. 로컬 파일 검사

### 테스트 파일

검사할 파일을:

``` text
input/test.txt
```

에 넣습니다.

예:

``` text
This is a sensitive information scanner test.

Email:
test@example.com

IP:
192.168.1.100

Example AWS Key:
AKIA1234567890ABCDEF

JWT:
token = eyJ...

API Key Test:
api_key=TEST_API_KEY_1234567890

Authorization Test:
Bearer TEST_BEARER_TOKEN_1234567890

Private Key:
-----BEGIN PRIVATE KEY-----
TEST DATA
-----END PRIVATE KEY-----
```

### 실행

PowerShell에서 프로젝트 폴더로 이동한 후:

``` powershell
python scanner.py
```

실행합니다.

### 결과

탐지 결과는 터미널에 표시되며 다음 파일에 저장됩니다.

``` text
output/results.json
output/results.csv
```

------------------------------------------------------------------------

## 8. Pastebin 단일 검사

Pastebin의 공개 Paste URL을 직접 입력하여 검사할 수 있습니다.

실행:

``` powershell
python pastebin_loader.py
```

URL 입력:

``` text
https://pastebin.com/qcxJ587x
```

처리 과정:

``` text
[+] Paste ID: qcxJ587x
[+] Paste 본문 요청
[+] 본문 가져오기 성공
[+] 규칙 파일 로딩
[+] 검사 시작
[DETECTED]
...
```

탐지 결과는 기존 Scanner와 동일한 방식으로 처리됩니다.

------------------------------------------------------------------------

## 9. Pastebin Batch 검사

여러 Pastebin URL을 한 번에 검사할 수 있습니다.

### URL 목록 작성

다음 파일을 사용합니다.

``` text
input/paste_urls.txt
```

예:

``` text
https://pastebin.com/AAAAAAA
https://pastebin.com/BBBBBBB
https://pastebin.com/CCCCCCC
```

빈 줄과 `#`으로 시작하는 주석은 무시됩니다.

### 실행

``` powershell
python pastebin_batch.py
```

예상 흐름:

``` text
[+] Pastebin Batch Scanner
[+] 검사 대상: 3개

[1/3] 검사 시작
...
[+] 탐지 건수: 1

[2/3] 검사 시작
...
[+] 탐지 건수: 0

[3/3] 검사 시작
...
[+] 탐지 건수: 2

[+] Batch 검사 완료
[+] 검사한 Paste: 3개
[+] 전체 탐지 건수: 3
```

------------------------------------------------------------------------

## 10. Batch 결과

Batch 검사가 완료되면 두 종류의 결과가 저장됩니다.

### 상세 결과

``` text
output/results.json
output/results.csv
```

각 탐지 결과의 상세 정보가 저장됩니다.

예:

``` text
type
severity
confidence
file
line
masked_value
context
```

### Paste별 요약 결과

``` text
output/batch_summary.json
output/batch_summary.csv
```

예:

``` json
[
    {
        "paste_id": "qcxJ587x",
        "url": "https://pastebin.com/qcxJ587x",
        "detection_count": 1,
        "highest_severity": "HIGH",
        "status": "REVIEW_REQUIRED"
    }
]
```

이를 이용하면 여러 Paste를 검사한 후 어떤 Paste를 우선적으로 검토해야
하는지 빠르게 파악할 수 있습니다.

------------------------------------------------------------------------

## 11. 위험도와 상태

### 위험도

현재 기본 위험도는 다음과 같이 구분합니다.

``` text
LOW
MEDIUM
HIGH
CRITICAL
```

예:

``` text
IP_ADDRESS       → LOW
EMAIL            → MEDIUM
AWS_ACCESS_KEY   → HIGH
JWT              → HIGH
PRIVATE_KEY      → CRITICAL
```

단, 위험도와 실제 유출 여부는 동일한 의미가 아닙니다.

예를 들어 테스트용 AWS Key 형식 문자열이 탐지되었다고 해서 실제 AWS
자격증명이 유출되었다고 확정할 수 없습니다.

------------------------------------------------------------------------

### 상태

현재 결과는 주로:

``` text
REVIEW_REQUIRED
CLEAN
```

으로 구분됩니다.

`REVIEW_REQUIRED`는 자동 탐지 결과에 대해 사람의 추가 검토가 필요하다는
의미입니다.

------------------------------------------------------------------------

## 12. 현재까지의 개발 단계

현재까지 다음 기능을 구현했습니다.

``` text
STEP 1
기본 파일 검사
        ↓
STEP 2
정규식 기반 탐지
        ↓
STEP 3
민감정보 마스킹
        ↓
STEP 4
JSON / CSV 결과 저장
        ↓
STEP 5
탐지 규칙 JSON 분리
        ↓
STEP 6
위험도 / 기본 신뢰도
        ↓
STEP 7
문맥 분석
        ↓
STEP 8
API Key / Token 규칙 확장
        ↓
STEP 9
긍정 / 부정 키워드 기반 신뢰도 조정
        ↓
STEP 10
강한 부정 키워드 및 판정 근거 추가
        ↓
STEP 11
Pastebin 단일 Paste 검사
        ↓
STEP 12
Pastebin Batch 검사
        ↓
STEP 12-2
Paste별 결과 요약
```

------------------------------------------------------------------------

## 13. 현재 프로젝트의 한계

현재 프로젝트는 다음과 같은 제한이 있습니다.

### 1. 자동 검색 기능은 아직 구현되지 않음

현재는:

``` text
Pastebin URL
```

을 직접 제공하거나,

``` text
input/paste_urls.txt
```

에 URL을 미리 입력해야 합니다.

Google 검색 결과에서 자동으로 Paste URL을 수집하는 기능은 현재 구현되어
있지 않습니다.

### 2. 탐지는 자동화되지만 최종 판정은 사람의 검토가 필요함

정규식과 문맥 키워드는 오탐/미탐 가능성이 있습니다.

따라서:

``` text
탐지됨 = 실제 비밀정보 유출 확정
```

으로 판단해서는 안 됩니다.

### 3. 실제 자격증명 검증 기능은 없음

현재 Scanner는 문자열의 형식과 문맥을 분석합니다.

실제 API Key가 유효한지 확인하거나 해당 계정에 접근하는 기능은 구현하지
않습니다.

이는 안전한 분석을 위해 의도적으로 분리한 부분입니다.

------------------------------------------------------------------------

## 14. 향후 개발 방향

현재 구조를 기반으로 다음 기능을 추가할 수 있습니다.

``` text
현재
Paste URL 목록
      ↓
Batch Scanner
      ↓
민감정보 탐지
```

향후:

``` text
공개 검색 결과에서 후보 URL 발견
      ↓
URL 중복 제거
      ↓
Batch Scanner
      ↓
민감정보 탐지
      ↓
위험도 기준 분류
      ↓
Paste별 요약
      ↓
분석자가 REVIEW_REQUIRED 항목 검토
```

추가적으로 고려할 수 있는 기능:

-   탐지 규칙 확장
-   더 세분화된 API Key 패턴
-   Secret/Password 패턴 탐지
-   탐지 결과 통계
-   위험도별 결과 필터링
-   Paste별 탐지 유형 요약
-   HTML/Markdown 보고서 생성
-   오탐 관리
-   테스트 데이터셋 기반 탐지 정확도 평가
-   검색 결과의 후보 URL 처리 자동화

------------------------------------------------------------------------

## 15. 보안 및 윤리적 사용

이 프로젝트는 보안 연구 및 방어 목적의 도구입니다.

다음 원칙을 준수하는 것을 권장합니다.

-   실제 제3자의 민감정보를 불필요하게 저장하지 않습니다.
-   API Key, Token, Password 등의 원문을 공유하지 않습니다.
-   탐지 결과에는 마스킹된 값만 사용합니다.
-   자동 탐지 결과를 유출 확정으로 판단하지 않습니다.
-   분석 권한이 있는 데이터 또는 공개된 테스트 데이터를 사용합니다.
-   탐지한 자격증명을 사용하여 서비스에 접근하거나 악용하지 않습니다.
-   필요 이상의 데이터 수집을 피합니다.

------------------------------------------------------------------------

## 16. 요약

SensitiveScanner는 현재 다음과 같은 기능을 갖춘 **규칙 기반 민감정보
탐지 프로토타입**입니다.

``` text
┌──────────────────────────────┐
│       SensitiveScanner       │
├──────────────────────────────┤
│ Regex Detection              │
│ Context Analysis             │
│ Confidence Scoring           │
│ Severity Classification      │
│ Sensitive Data Masking       │
│ JSON / CSV Export            │
├──────────────────────────────┤
│ Pastebin Single Scan         │
│ Pastebin Batch Scan          │
│ Paste-level Summary          │
└──────────────────────────────┘
```

현재 가장 중요한 목표는 **자동 탐지 결과의 정확도와 분석 편의성을 높이는
것**이며, 향후에는 공개 검색에서 발견된 후보 URL을 안전하게 분석
파이프라인에 연결하는 방향으로 확장할 수 있습니다.
