from pathlib import Path
import re
import json
import csv


INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
RULES_DIR = Path("rules")


# ==============================
# 규칙 파일 불러오기
# ==============================

def load_rules():

    rules = {}

    rule_files = list(RULES_DIR.glob("*.json"))

    if not rule_files:
        print("[!] rules 폴더에 규칙 파일이 없습니다.")
        return rules

    for rule_file in rule_files:

        print(f"[+] 규칙 파일 로딩: {rule_file.name}")

        try:

            with open(
                rule_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                rules.update(data)

        except json.JSONDecodeError:

            print(f"[!] JSON 형식 오류: {rule_file.name}")

    print(f"[+] 총 로딩된 규칙: {len(rules)}개")

    return rules


# ==============================
# 값 마스킹
# ==============================

def mask_value(value):

    if len(value) <= 8:
        return "*" * len(value)

    return value[:4] + "*" * (len(value) - 8) + value[-4:]


# ==============================
# 문맥 추출
# ==============================

def get_context(lines, line_index, match_start, match_end):
    """
    탐지된 문자열의 앞뒤 줄을 포함하여
    문맥을 반환한다.
    """

    context_lines = []

    # 이전 줄
    if line_index > 0:
        context_lines.append(lines[line_index - 1])

    # 현재 줄
    current_line = lines[line_index]

    context_start = max(0, match_start - 40)
    context_end = min(len(current_line), match_end + 40)

    current_context = current_line[
        context_start:context_end
    ]

    context_lines.append(current_context)

    # 다음 줄
    if line_index + 1 < len(lines):
        context_lines.append(lines[line_index + 1])

    return " ".join(
        line.strip()
        for line in context_lines
        if line.strip()
    )


# ==============================
# 신뢰도 점수 변환
# ==============================

def confidence_to_score(confidence):

    levels = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }

    return levels.get(confidence.upper(), 1)


# ==============================
# 점수를 신뢰도로 변환
# ==============================

def score_to_confidence(score):

    if score <= 1:
        return "LOW"

    elif score == 2:
        return "MEDIUM"

    else:
        return "HIGH"


# ==============================
# 문맥 기반 신뢰도 분석
# ==============================

def analyze_context(context, rule):

    context_lower = context.lower()

    base_confidence = rule.get(
        "confidence",
        "LOW"
    )

    positive_keywords = rule.get(
        "positive_keywords",
        {}
    )

    negative_keywords = rule.get(
        "negative_keywords",
        {}
    )

    strong_negative_keywords = rule.get(
        "strong_negative_keywords",
        {}
    )

    # 기본 점수
    score = confidence_to_score(
        base_confidence
    )

    positive_matches = []
    negative_matches = []
    strong_negative_matches = []

    positive_score = 0
    negative_score = 0
    strong_negative_score = 0

    # ==============================
    # 긍정 키워드 검사
    # ==============================

    for keyword, weight in positive_keywords.items():

        if keyword.lower() in context_lower:

            positive_matches.append(
                keyword
            )

            positive_score += weight

    # ==============================
    # 일반 부정 키워드 검사
    # ==============================

    for keyword, weight in negative_keywords.items():

        if keyword.lower() in context_lower:

            negative_matches.append(
                keyword
            )

            negative_score += weight

    # ==============================
    # 강한 부정 키워드 검사
    # ==============================

    for keyword, weight in strong_negative_keywords.items():

        if keyword.lower() in context_lower:

            strong_negative_matches.append(
                keyword
            )

            strong_negative_score += weight

    # ==============================
    # 최종 점수 계산
    # ==============================

    score += positive_score
    score += negative_score
    score += strong_negative_score

    # 점수 범위 제한
    score = max(
        1,
        min(score, 3)
    )

    # 강한 테스트/예제 문맥이 있으면
    # HIGH로 올라가지 않도록 제한
    if strong_negative_matches:

        score = min(score, 2)

    final_confidence = score_to_confidence(
        score
    )

    # ==============================
    # 판정 근거
    # ==============================

    reasons = []

    for keyword in positive_matches:

        weight = positive_keywords[keyword]

        reasons.append(
            f"긍정 키워드 '{keyword}' "
            f"발견 ({weight:+d})"
        )

    for keyword in negative_matches:

        weight = negative_keywords[keyword]

        reasons.append(
            f"부정 키워드 '{keyword}' "
            f"발견 ({weight:+d})"
        )

    for keyword in strong_negative_matches:

        weight = strong_negative_keywords[keyword]

        reasons.append(
            f"강한 부정 키워드 '{keyword}' "
            f"발견 ({weight:+d})"
        )

    if not reasons:

        reasons.append(
            "문맥상 추가적인 판단 키워드가 "
            "확인되지 않음"
        )

    return (
        final_confidence,
        positive_matches,
        negative_matches,
        strong_negative_matches,
        positive_score,
        negative_score,
        strong_negative_score,
        reasons
    )

# ==============================
# 파일 검사
# ==============================

def scan_text(content, source, rules):

    print(f"\n[+] 검사 시작: {source}")
    print(f"[+] 텍스트 크기: {len(content)} characters")

    results = []

    lines = content.splitlines()

    for line_number, line in enumerate(
        lines,
        start=1
    ):

        for name, rule in rules.items():

            pattern = rule["pattern"]

            severity = rule.get(
                "severity",
                "UNKNOWN"
            )

            base_confidence = rule.get(
                "confidence",
                "UNKNOWN"
            )

            try:

                matches = re.finditer(
                    pattern,
                    line
                )

                for match in matches:

                    value = match.group()

                    context = get_context(
                        lines,
                        line_number - 1,
                        match.start(),
                        match.end()
                    )

                    masked_context = context.replace(
                        value,
                        mask_value(value)
                    )

                    (
                        final_confidence,
                        positive_matches,
                        negative_matches,
                        strong_negative_matches,
                        positive_score,
                        negative_score,
                        strong_negative_score,
                        reasons
                    ) = analyze_context(
                        context,
                        rule
                    )

                    result = {
                        "type": name,

                        "severity": severity,

                        "base_confidence":
                            base_confidence,

                        "confidence":
                            final_confidence,

                        "file": source,

                        "line": line_number,

                        "masked_value":
                            mask_value(value),

                        "context":
                            masked_context,

                        "positive_context_keywords":
                            positive_matches,

                        "negative_context_keywords":
                            negative_matches,

                        "strong_negative_context_keywords":
                            strong_negative_matches,

                        "positive_score":
                            positive_score,

                        "negative_score":
                            negative_score,

                        "strong_negative_score":
                            strong_negative_score,

                        "reasons":
                            reasons,

                        "description":
                            rule.get(
                                "description",
                                "설명 없음"
                            ),

                        "status":
                            "REVIEW_REQUIRED"
                    }

                    results.append(result)

                    # ==============================
                    # 탐지 결과 출력
                    # ==============================

                    print("\n[DETECTED]")

                    print(
                        f"  종류         : {name}"
                    )

                    print(
                        f"  위험도       : {severity}"
                    )

                    print(
                        f"  기본 신뢰도  : "
                        f"{base_confidence}"
                    )

                    print(
                        f"  최종 신뢰도  : "
                        f"{final_confidence}"
                    )

                    print(
                        f"  위치         : "
                        f"{source}:{line_number}"
                    )

                    print(
                        f"  값           : "
                        f"{mask_value(value)}"
                    )

                    print(
                        f"  문맥         : "
                        f"{masked_context}"
                    )

                    if positive_matches:

                        print(
                            f"  상승 키워드   : "
                            f"{', '.join(positive_matches)}"
                        )

                    if negative_matches:

                        print(
                            f"  하락 키워드   : "
                            f"{', '.join(negative_matches)}"
                        )

                    if strong_negative_matches:

                        print(
                            f"  강한 하락 키워드 : "
                            f"{', '.join(strong_negative_matches)}"
                        )

                    print(
                        f"  긍정 점수    : "
                        f"+{positive_score}"
                    )

                    print(
                        f"  부정 점수    : "
                        f"{negative_score}"
                    )

                    print(
                        f"  강한 부정 점수 : "
                        f"{strong_negative_score}"
                    )

                    print(
                        f"  설명         : "
                        f"{rule.get('description', '설명 없음')}"
                    )

                    print(
                        "  판정 근거    :"
                    )

                    for reason in reasons:

                        print(
                            f"    - {reason}"
                        )

                    print(
                        f"  상태         : "
                        f"REVIEW_REQUIRED"
                    )

            except re.error:

                print(
                    f"[!] 잘못된 정규표현식: "
                    f"{name}"
                )

    return results

def scan_file(file_path, rules):

    print(
        f"\n[+] 파일 읽기: {file_path}"
    )

    content = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    return scan_text(
        content,
        str(file_path),
        rules
    )

# ==============================
# JSON 저장
# ==============================

def save_json(results):

    output_file = OUTPUT_DIR / "results.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\n[+] JSON 결과 저장 완료: "
        f"{output_file}"
    )


# ==============================
# CSV 저장
# ==============================

def save_csv(results):

    output_file = OUTPUT_DIR / "results.csv"

    fieldnames = [
        "type",
        "severity",
        "base_confidence",
        "confidence",
        "file",
        "line",
        "masked_value",
        "context",
        "positive_context_keywords",
        "negative_context_keywords",
        "strong_negative_context_keywords",
        "positive_score",
        "negative_score",
        "strong_negative_score",
        "reasons",
        "description",
        "status"
    ]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for result in results:

            csv_result = result.copy()

            # 리스트 → CSV에서 읽기 쉬운 문자열로 변환
            csv_result[
                "positive_context_keywords"
            ] = ", ".join(
                result["positive_context_keywords"]
            )

            csv_result[
                "negative_context_keywords"
            ] = ", ".join(
                result["negative_context_keywords"]
            )

            csv_result[
                "strong_negative_context_keywords"
            ] = ", ".join(
                result["strong_negative_context_keywords"]
            )

            csv_result[
                "reasons"
            ] = " | ".join(
                result["reasons"]
            )

            writer.writerow(
                csv_result
            )

    print(
        f"[+] CSV 결과 저장 완료: "
        f"{output_file}"
    )

# ==============================
# 프로그램 시작
# ==============================

def main():

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    # 1. 규칙 로딩

    rules = load_rules()

    if not rules:

        print(
            "[!] 사용할 수 있는 "
            "탐지 규칙이 없습니다."
        )

        return

    # 2. 검사할 파일 확인

    files = list(
        INPUT_DIR.glob("*")
    )

    if not files:

        print(
            "[!] input 폴더에 "
            "검사할 파일이 없습니다."
        )

        return

    # 3. 파일 검사

    all_results = []

    for file_path in files:

        if file_path.is_file():

            results = scan_file(
                file_path,
                rules
            )

            all_results.extend(
                results
            )

    # 4. 결과 출력

    print(
        "\n=============================="
    )

    print(
        f"[+] 총 탐지 건수: "
        f"{len(all_results)}"
    )

    print(
        "=============================="
    )

    # 5. 결과 저장

    save_json(all_results)

    save_csv(all_results)


if __name__ == "__main__":
    main()