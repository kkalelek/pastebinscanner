import re
import scanner

from urllib.parse import urlparse
from urllib.request import Request, urlopen


# ==============================
# Paste ID 추출
# ==============================

def extract_paste_id(url):
    """
    Pastebin 공개 URL에서 Paste ID를 추출한다.
    """

    parsed = urlparse(url)

    if parsed.netloc.lower() not in (
        "pastebin.com",
        "www.pastebin.com"
    ):
        raise ValueError(
            "Pastebin URL만 사용할 수 있습니다."
        )

    path = parsed.path.strip("/")

    if not path:
        raise ValueError(
            "Paste ID를 찾을 수 없습니다."
        )

    paste_id = path.split("/")[0]

    if not re.fullmatch(
        r"[A-Za-z0-9]+",
        paste_id
    ):
        raise ValueError(
            "올바르지 않은 Paste ID입니다."
        )

    return paste_id


# ==============================
# Paste 본문 가져오기
# ==============================

def fetch_paste_content(paste_id):
    """
    Pastebin 공개 Paste의 raw 텍스트를 가져온다.
    """

    raw_url = (
        f"https://pastebin.com/raw/{paste_id}"
    )

    print(
        f"[+] Paste 본문 요청: {paste_id}"
    )

    request = Request(
        raw_url,
        headers={
            "User-Agent":
            "SensitiveScanner/1.0"
        }
    )

    try:

        with urlopen(
            request,
            timeout=10
        ) as response:

            content = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        print(
            "[+] 본문 가져오기 성공"
        )

        print(
            f"[+] 본문 크기: "
            f"{len(content)} characters"
        )

        # ==============================
        # API_KEY 포함 여부 확인
        # ==============================

        found_api_key = False

        for line_number, line in enumerate(
            content.splitlines(),
            start=1
        ):

            if "api_key" in line.lower():

                found_api_key = True

                print(
                    f"[+] API_KEY 포함 줄 발견: "
                    f"{line_number}"
                )

                # API_KEY 뒤의 값만 마스킹
                masked_line = re.sub(
                    r"""(?i)(api[_-]?key\s*[:=]\s*['"]?)[^\s'"]+""",
                    r"\1********",
                    line
                )

                print(
                    f"    내용(마스킹): "
                    f"{masked_line}"
                )

        if not found_api_key:

            print(
                "[-] 본문에서 API_KEY 문자열을 "
                "찾지 못함"
            )

        return content

    except Exception as error:

        print(
            f"[!] Paste 본문 가져오기 실패: "
            f"{error}"
        )

        return None


# ==============================
# 프로그램 시작
# ==============================

def main():

    url = input(
        "검사할 Pastebin URL을 입력하세요: "
    ).strip()

    try:

        paste_id = extract_paste_id(
            url
        )

        print(
            f"[+] Paste ID: {paste_id}"
        )

        content = fetch_paste_content(
            paste_id
        )

        if content is None:
            return

        # ==============================
        # Scanner 규칙 로딩
        # ==============================

        rules = scanner.load_rules()

        if not rules:

            print(
                "[!] 사용할 수 있는 "
                "탐지 규칙이 없습니다."
            )

            return

        # ==============================
        # Pastebin 본문 검사
        # ==============================

        results = scanner.scan_text(
            content,
            url,
            rules
        )

        # ==============================
        # 결과 출력
        # ==============================

        print(
            "\n=============================="
        )

        print(
            f"[+] 총 탐지 건수: "
            f"{len(results)}"
        )

        print(
            "=============================="
        )

        # ==============================
        # 결과 저장
        # ==============================

        scanner.OUTPUT_DIR.mkdir(
            exist_ok=True
        )

        scanner.save_json(
            results
        )

        scanner.save_csv(
            results
        )

        print(
            "[+] Paste 텍스트 검사가 "
            "정상적으로 완료되었습니다."
        )

    except ValueError as error:

        print(
            f"[!] 오류: {error}"
        )


if __name__ == "__main__":
    main()