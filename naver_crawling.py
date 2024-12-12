# 이름, 위도, 경도, 카테고리, 평점, 리뷰

import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

# Chromedriver 경로 설정
driver = webdriver.Chrome()

driver.get("https://map.naver.com/v5/")  # 네이버 지도 접속

# 검색어 목록 및 파일명 정의
search_keywords = ["서울 카페", "서울 한식", "서울 양식", "서울 일식", "서울 중식"]
file_names = {"서울 카페": "카페.csv", "서울 한식": "한식.csv", "서울 양식": "양식.csv", "서울 일식": "일식.csv", "서울 중식": "중식.csv"}

# CSS 요소 대기 함수
def wait_for_element(css_selector, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )

# 프레임 전환 함수
def switch_to_frame(frame_id):
    driver.switch_to.default_content()
    iframe = wait_for_element(f'iframe#{frame_id}')
    driver.switch_to.frame(iframe)

# 페이지 다운 함수
def page_down(times):
    body = driver.find_element(By.CSS_SELECTOR, '.Ryr1F')
    for _ in range(times):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)

# 데이터 크롤링 및 CSV 저장 진행

max_page = 2

for search_keyword in search_keywords:
    page = 0
    # 검색어 입력 및 검색
    search_box = wait_for_element(".input_search")
    search_box.click()  # 클릭하여 포커스 이동
    search_box.send_keys(Keys.CONTROL + "a")  # 이전 검색어 전체 선택 -> Mac OS : COMMAND
    search_box.send_keys(Keys.DELETE)  # 선택된 검색어 삭제
    search_box.send_keys(search_keyword)  # 새로운 검색어 입력
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)  # 검색 결과 로드 대기

    # 검색 결과 iframe으로 전환. iframe, id = searchIframe
    frame=driver.find_element(By.CSS_SELECTOR, "iframe#searchIframe")

    driver.switch_to.frame(frame)

    time.sleep(2)

    # CSV 파일 생성 및 헤더 작성
    file_name = file_names[search_keyword]
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["매장명", "카테고리", "평점", "리뷰"])

        # 데이터 수집 반복
        while True:
            print("Scrolling down")
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            # 페이지 스크롤 안될 때 까지
            page_down(100)
            print("Scrolling down done")
            time.sleep(1)

            # 매장 정보 추출
            place_elements = driver.find_elements(By.CSS_SELECTOR, ".UEzoS")  # 매장 리스트의 주요 CSS 셀렉터 확인 필요
            print(f"{len(place_elements)}개의 매장 정보를 찾았습니다.")
            for place in place_elements:
                try:
                    name = place.find_element(By.CSS_SELECTOR, ".TYaxT").text  # 이름
                    name = name.replace('\"', '')  # CSV 쉼표 이슈 방지
                    category = place.find_element(By.CSS_SELECTOR, ".KCMnt").text  # 카테고리

                    # "서울 카페" 검색 시 애견카페와 만화카페 제외
                    if search_keyword == "서울 카페" and ("애견카페" in category or "만화방" in category):
                        continue

                    # 평점과 리뷰는 선택적으로 존재할 수 있으므로 예외처리
                    rating = place.find_element(By.CSS_SELECTOR, ".orXYY").text if place.find_elements(By.CSS_SELECTOR, ".orXYY") else "N/A"  # 평점
                    rating = rating.replace("별점", "")  # 평점 앞의 "평점" 문자열 제거
                    rating = rating.replace(" ", "")  # 평점 뒤의 "점" 문자열 제거
                    rating = rating.replace("\n", "")  # 평점 뒤의 "점" 문자열 제거
                    #리뷰는 div u4vcQ 밑의 span의 text임
                    reviews = place.find_elements(By.CSS_SELECTOR, ".u4vcQ")[0].text if place.find_elements(By.CSS_SELECTOR, ".u4vcQ") else "N/A"  # 리뷰
                    
                    # lat = place.get_attribute("data-latitude")  # 위도
                    # lng = place.get_attribute("data-longitude")  # 경도

                    # CSV 파일에 데이터 추가
                    # writer.writerow([name, lat, lng, category, rating, reviews])
                    writer.writerow([name, category, rating, reviews])
                except Exception as e:
                    print(f"정보를 추출하는 중 오류 발생: {e}")
                    
            print("한 페이지 추출 완료, 예시: ", name, category, rating, reviews)
                    
            # 다음 페이지 버튼 클릭
            try:
                next_button = driver.find_elements(By.CSS_SELECTOR, ".eUTV2")[1]
                print("Find next button", next_button)
                if next_button.get_attribute("aria-disabled") == "true":
                    break

                next_button.click()
                time.sleep(1)
                print("Click next button")
                
                page += 1
            except Exception as e:
                print(f"다음 페이지로 이동할 수 없음: {e}")
                break

    # 검색 결과 iframe에서 탈출
    driver.switch_to.default_content()
    time.sleep(1)

print("크롤링 완료. 모든 데이터 수집이 종료되었습니다.")
driver.quit()
