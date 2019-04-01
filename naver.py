from selenium import webdriver
from bs4 import BeautifulSoup
import re


def get_naver_blog_id(blog_url):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome('./chromedriver', options=options)

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


if __name__ == "__main__":
    print(get_naver_blog_id('https://kas2724.blog.me/221431886129'))
