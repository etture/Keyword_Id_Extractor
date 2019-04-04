from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import os
from custom_wait_condition import wait_for_attribute_value_regex


def get_naver_blog_id(driver, blog_url):

    driver.get(blog_url)
    # 처음에 frame 태그가 껴있는 예외 상황 처리
    if len(driver.find_elements_by_id('screenFrame')) != 0:
        driver.switch_to.frame(driver.find_element_by_tag_name("frame"))
    # 원하는 정보가 들어있는 iframe으로 스위칭
    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # print("HTML SOURCE: " + html)

    # 블로그 프로필 정보 (아이디)를 포함하고 있는 부분 전체
    blog_profile = soup.find(id='blog-profile')

    # 닉네임 (아이디)를 포함하고 있는 부분 추출
    nick = blog_profile.find('div', class_='nick')
    # print("children count: " + str(len(nick.findChildren())))

    # 블로그 형태에 따라 아이디를 추출하는 과정이 약간 다르다
    raw_user_id = blog_profile.find('span', class_='itemfont col').text.strip() \
        if len(nick.findChildren()) > 1 \
        else blog_profile.find(id="nickNameArea").text.strip()

    # 괄호 안 아이디 등 추출 과정을 거쳐서 정확한 아이디 추출
    user_id = re.search(r'\((.*?)\)', raw_user_id).group(1) \
        if raw_user_id[0] == '(' \
           and raw_user_id[len(raw_user_id) - 1] == ')' \
        else raw_user_id

    # print("There are {0} comments".format(len(comments)))

    return user_id


def get_commenter_urls(driver, blog_url):

    driver.get(blog_url)
    # 처음에 frame 태그가 껴있는 예외 상황 처리
    if len(driver.find_elements_by_id('screenFrame')) != 0:
        driver.switch_to.frame(driver.find_element_by_tag_name("frame"))
    # 원하는 정보가 들어있는 iframe으로 스위칭
    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))

    # 댓글 버튼 눌러서 댓글 창 펼치기
    driver.find_element_by_class_name('btn_comment').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'u_cbox_info_main')))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 댓글을 담고 있는 부분 전체
    comments_area = soup.find(id='postListBody')
    # print(comments_area)

    # 개별 댓글 칸 추출 (원 댓글 + 대댓글)
    all_commenters = comments_area.find_all('span', class_='u_cbox_info_main')

    commenter_urls = []

    for commenter in all_commenters:
        # 댓글 작성자가 블로그 주인이라면 추가하지 않는다
        if commenter.find('span', class_='u_cbox_ico_editor'):
            continue
        else:
            commenter_urls.append(commenter.find('a', class_='u_cbox_name')['href'])

    return commenter_urls


def get_sympathy_urls(driver, blog_url):

    driver.get(blog_url)

    # 처음에 frame 태그가 껴있는 예외 상황 처리
    if len(driver.find_elements_by_id('screenFrame')) != 0:
        driver.switch_to.frame(driver.find_element_by_tag_name("frame"))
    # 원하는 정보가 들어있는 iframe으로 스위칭
    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))

    # 댓글 버튼 눌러서 댓글 창 펼치기
    driver.find_element_by_class_name('btn_arr').click()
    WebDriverWait(driver, 10).until(wait_for_attribute_value_regex((By.XPATH, "//iframe[@title='엮인글']"), 'style', r'^(display: inline;)'))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    iframe = soup.find('iframe', id=re.compile('^sympathyFrm'))
    # print(iframe['src'])

    driver.get('https://blog.naver.com' + iframe['src'])
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup)

    # 공감을 담고 있는 부분 전체
    sympathy_area = soup.find('ul', class_='list_sympathy')

    # 개별 공감 칸 추출
    all_sympathies = sympathy_area.find_all('strong', class_='nick')

    # 블로그 주소 형태에 맞게 처리해서 리스트에 넣기
    sympathy_urls = []
    sympathy_urls.extend(
        [blog_url_process(sympathy.find('a', class_='pcol2')['href'])
         for sympathy in all_sympathies]
    )

    pagination = soup.find_all('a', class_='page pcol2')

    # 공감이 많을 때 여러 페이지에 나뉘어 있는 경우, 각각 페이지 접속 후 블로그 URL 추출
    for page_btn in pagination:
        element = driver.find_element_by_xpath("//a[@href='{0}']".format(page_btn['href']))
        driver.execute_script("arguments[0].click();", element)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//strong[@class='page pcol3']")))

        page_html = driver.page_source
        page_soup = BeautifulSoup(page_html, 'html.parser')

        # 공감을 담고 있는 부분 전체
        page_sympathy_area = page_soup.find('ul', class_='list_sympathy')

        # 개별 공감 칸 추출
        page_all_sympathies = page_sympathy_area.find_all('strong', class_='nick')

        sympathy_urls.extend(
            [blog_url_process(sympathy.find('a', class_='pcol2')['href'])
             for sympathy in page_all_sympathies]
        )

    return sympathy_urls


def blog_url_process(url):
    if re.match(r'^https://', url):
        return url
    else:
        return 'https://blog.naver.com' + url


if __name__ == "__main__":
    __curloc__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    driver_location = os.path.join(__curloc__, 'bin/chromedriver')

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome(driver_location, options=options)
    # print(get_naver_blog_id(driver, 'https://blog.naver.com/DomainDispatcher.nhn?blogId=seagreen0314&id=mayjeong94&type=log&subName=blog'))
    # print(get_commenter_urls(driver, 'https://blog.naver.com/clauds/221491100858'))
    print(get_sympathy_urls(driver, 'https://blog.naver.com/moimoi1357/221473567252'))
