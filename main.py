import os
import asyncio
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from notification.send_telegram import send_msg

load_dotenv(override=True)


def get_default_headers(referer):
    """
    기본 HTTP 요청 헤더를 반환하는 함수입니다.
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ko,en;q=0.9,en-US;q=0.8",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "User-Agent": "Yeti/1.1 (+http://naver.me/bot)",  # Yeti 크롤러의 User-Agent
        "referer": referer,  # Referer 헤더를 여기에서 처리
    }
    return headers


def fetch_page_content(url, referer):
    """
    주어진 URL의 HTML 콘텐츠를 가져옵니다.
    """
    headers = get_default_headers(referer=referer)

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생
        if response.status_code == 200:
            return response.text
        else:
            return f"요청 실패: 상태 코드 {response.status_code}"
    except requests.exceptions.Timeout:
        return "요청 실패: 요청이 시간 초과되었습니다."
    except requests.exceptions.TooManyRedirects:
        return "요청 실패: 너무 많은 리디렉션이 발생했습니다."
    except requests.exceptions.RequestException as e:
        return f"요청 실패: {e}"


def extract_text_from_html(html_content, selector):
    """
    HTML 콘텐츠에서 특정 클래스를 가진 요소의 텍스트를 추출합니다.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    elements = soup.select(selector)
    if len(elements) == 0:
        return []
    else:
        return [e.get_text(strip=True) for e in elements]


def main():
    search_keyword = (os.getenv("SEARCH_KEYWORD") or "").strip()

    if not search_keyword:
        print("no search keyword")
        return
    encoded_keyword = quote(search_keyword)  # 키워드를 URL 인코딩

    # URL을 여러 줄로 나누어 가독성을 높임
    library_url = (
        "https://www.ydplib.or.kr/intro/menu/10003/program/30001/plusSearchResultList.do?"
        "searchType=SIMPLE&searchMenuCollectionCategory=&searchCategory=ALL&searchKey1=&searchKey2="
        "&searchKey3=&searchKey4=&searchKey5=&searchKeyword1=&searchKeyword2=&searchKeyword3="
        "&searchKeyword4=&searchKeyword5=&searchOperator1=&searchOperator2=&searchOperator3="
        "&searchOperator4=&searchOperator5=&searchPublishStartYear=&searchPublishEndYear="
        "&searchRoom=&searchKdc=&searchIsbn=&currentPageNo=1&viewStatus=IMAGE&preSearchKey=ALL&"
        f"preSearchKeyword={encoded_keyword}&searchKey=ALL&searchKeyword={encoded_keyword}&"
        "searchLibraryArr=CA&searchSort=SIMILAR&searchOrder=DESC&searchRecordCount=10"
    )

    referrer = (
        "https://www.ydplib.or.kr/intro/menu/10003/program/30001/plusSearchResultList.do?"
        "searchType=SIMPLE&searchMenuCollectionCategory=&searchCategory=ALL&searchKey1=&searchKey2="
        "&searchKey3=&searchKey4=&searchKey5=&searchKeyword1=&searchKeyword2=&searchKeyword3="
        "&searchKeyword4=&searchKeyword5=&searchOperator1=&searchOperator2=&searchOperator3="
        "&searchOperator4=&searchOperator5=&searchPublishStartYear=&searchPublishEndYear="
        "&searchRoom=&searchKdc=&searchIsbn=&currentPageNo=1&viewStatus=IMAGE&preSearchKey=ALL&"
        f"preSearchKeyword={encoded_keyword}&searchKey=ALL&searchKeyword={encoded_keyword}&"
        "searchLibraryArr=CA&searchSort=SIMILAR&searchOrder=DESC&searchRecordCount=10"
    )

    html_content = fetch_page_content(library_url, referer=referrer)

    if "요청 실패" in html_content:
        return

    text_list = extract_text_from_html(
        html_content=html_content, selector=".state.typeA"
    )
    if len(text_list) > 0:
        for text in text_list:
            if text == "도서예약신청":
                asyncio.run(
                    send_msg(
                        text=f"도서예약가능: {search_keyword}, URL: https://www.ydplib.or.kr/"
                    )
                )


if __name__ == "__main__":
    main()
