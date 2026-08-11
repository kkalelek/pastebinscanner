import scanner
import json
import csv
from pathlib import Path
from pastebin_loader import (
    extract_paste_id,
    fetch_paste_content
)


# ==============================
# 경로 설정
# ==============================

URL_FILE = Path(
    "input/paste_urls.txt"
)


# ==============================
# URL 목록 불러오기
# ==============================

def load_urls():

    if not URL_FILE.exists():

        print(
            f"[!] URL 목록 파일이 없습니다: "
            f"{URL_FILE}"
        )

        return []

    urls = []

    with open(
        URL_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            url = line.strip()

            # 빈 줄 무시
            if not url:
                continue

            # 주석 무시
            if url.startswith("#"):
                continue

            urls.append(url)

    # 중복 제거
    urls = list(
        dict.fromkeys(urls)
    )

    return urls


# ==============================
# 여러 Paste 검사
# ==============================

def main():

    print(
        "================================"
    )

    print(
        "[+] Pastebin Batch Scanner"
    )

    print(
        "================================"
    )

    urls = load_urls()

    if not urls:

        print(
            "[!] 검사할 URL이 없습니다."
        )

        return

    print(
        f"[+] 검사 대상: "
        f"{len(urls)}개"
    )

    # 규칙 로딩
    rules = scanner.load_rules()

    if not rules:

        print(
            "[!] 사용할 수 있는 "
            "탐지 규칙이 없습니다."
        )

        return

    all_results = []
    summary_results = []

    # ==============================
    # URL 순차 검사
    # ==============================

    for index, url in enumerate(
        urls,
        start=1
    ):

        print(
            "\n================================"
        )

        print(
            f"[{index}/{len(urls)}] 검사 시작"
        )

        print(
            f"URL: {url}"
        )

        print(
            "================================"
        )

        try:

            paste_id = extract_paste_id(
                url
            )

            print(
                f"[+] Paste ID: "
                f"{paste_id}"
            )

            content = fetch_paste_content(
                paste_id
            )

            if content is None:

                print(
                    "[!] 본문을 가져오지 못했습니다."
                )

                continue

            # Scanner 실행
            results = scanner.scan_text(
                content,
                url,
                rules
            )

            detection_count = len(results)

            print(
                f"[+] 탐지 건수: "
                f"{detection_count}"
            )

            all_results.extend(
                results
            )


            # ==============================
            # Paste별 요약
            # ==============================

            if results:

                severity_order = {
                    "LOW": 1,
                    "MEDIUM": 2,
                    "HIGH": 3,
                    "CRITICAL": 4
                }

                highest_severity = max(
                    results,
                    key=lambda result:
                    severity_order.get(
                        result.get(
                            "severity",
                            "LOW"
                        ),
                        0
                    )
                )

                summary_results.append({
                    "paste_id": paste_id,
                    "url": url,
                    "detection_count": detection_count,
                    "highest_severity":
                        highest_severity.get(
                            "severity",
                            "UNKNOWN"
                        ),
                    "status": "REVIEW_REQUIRED"
                })

            else:

                summary_results.append({
                    "paste_id": paste_id,
                    "url": url,
                    "detection_count": 0,
                    "highest_severity": "NONE",
                    "status": "CLEAN"
                })

        except ValueError as error:

            print(
                f"[!] URL 오류: {error}"
            )

        except Exception as error:

            print(
                f"[!] 검사 중 오류: "
                f"{error}"
            )

    # ==============================
    # 전체 결과
    # ==============================

    print(
        "\n================================"
    )

    print(
        "[+] Batch 검사 완료"
    )

    print(
        f"[+] 검사한 Paste: "
        f"{len(urls)}개"
    )

    print(
        f"[+] 전체 탐지 건수: "
        f"{len(all_results)}"
    )

    print(
        "================================"
    )

    # ==============================
    # 결과 저장
    # ==============================

    scanner.OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    scanner.save_json(
        all_results
    )

    scanner.save_csv(
        all_results
    )

    print(
        "[+] 전체 결과 저장 완료"
    )

    # ==============================
    # Batch 요약 JSON 저장
    # ==============================

    summary_json = (
        scanner.OUTPUT_DIR /
        "batch_summary.json"
    )

    with open(
        summary_json,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary_results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"[+] Batch 요약 JSON 저장 완료: "
        f"{summary_json}"
    )


    # ==============================
    # Batch 요약 CSV 저장
    # ==============================

    summary_csv = (
        scanner.OUTPUT_DIR /
        "batch_summary.csv"
    )

    fieldnames = [
        "paste_id",
        "url",
        "detection_count",
        "highest_severity",
        "status"
    ]

    with open(
        summary_csv,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            summary_results
        )

    print(
        f"[+] Batch 요약 CSV 저장 완료: "
        f"{summary_csv}"
    )


if __name__ == "__main__":
    main()