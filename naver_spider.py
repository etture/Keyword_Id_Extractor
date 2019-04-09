import os
import re
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse
from scrapy.exceptions import DropItem, CloseSpider
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import naver_crawler
from bs4 import BeautifulSoup
import urllib.parse as urlparse
import time
from stopit import ThreadingTimeout, TimeoutException
from mutt_module import send_mail
import platform


class NaverSpider(scrapy.Spider):
    name = 'naver_spider'

    def __init__(self, keywords=[''], target_id_count=100):
        scrapy.Spider.__init__(self)

        # 네이버 크롤링에 사용할 기본 URL 구조 (query 등 포함)
        self.url_head = 'https://search.naver.com/search.naver'
        self.search_query = '?query={0}&where=post&sm=tab_nmr&nso='
        self.search_url = self.url_head + self.search_query

        # Selenium 웹 드라이버 설정 (headless)
        __curloc__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        driver_location = os.path.join(__curloc__, 'bin/chromedriver')
        self.options = webdriver.ChromeOptions()

        # Headless 옵션 (브라우저 창 안 띄우기)
        self.options.add_argument('headless')
        self.options.add_argument('window-size=1920x1080')
        self.options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome(driver_location, options=self.options)

        # 크롤러를 종료할 때 True로 만들어줘야 하는 flag
        self.close_down = False

        # 크롤링 할 검색어
        self.start_urls = []
        for keyword in keywords:
            self.start_urls.append(self.search_url.format(keyword))

        # 검색어로 크롤링한 검색 결과 페이지 개수
        self.page_count = 1
        # 목표 아이디 개수 (긁어온 아이디 개수)
        self.target_id_count = target_id_count

    def parse(self, response):
        # 키워드 입력 시 블로그 글 검색 결과 (목록)
        BLOG_ITEM_SELECTOR = '#wrap #container .pack_group #main_pack .blog ul li dl dt'

        self.driver.get(response.url)

        resp = TextResponse(url='', body=self.driver.page_source, encoding='utf-8')
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        next_page = soup.find('a', class_='next')
        print('next page: ' + next_page.text.strip() + ", link: " + next_page['href'])

        # 개별 블로그 글
        for blog_item in resp.css(BLOG_ITEM_SELECTOR):
            # 목표한 아이디 개수가 채워졌으면 크롤러 종료
            if self.close_down:
                raise CloseSpider(reason='목표 아이디 개수 달성')

            TITLE_SELECTOR = 'a::attr(title)'
            URL_SELECTOR = 'a::attr(href)'

            title = blog_item.css(TITLE_SELECTOR).get()
            blog_url = blog_item.css(URL_SELECTOR).get()
            print("URL: " + blog_url)

            # 개별 블로그에서 아이디 추출, 글 게시자=True
            try:
                with ThreadingTimeout(5.0) as timeout_ctx:
                    assert timeout_ctx.state == timeout_ctx.EXECUTING
                    yield self.get_id_from_blog(blog_url=blog_url, original_poster=True)
            # except ThreadingTimeout:
            #     print('ThreadingTimeout')
            except AttributeError:
                print('AttributeError')
            except NoSuchElementException:
                print('NoSuchElementException')
            except BaseException:
                print('BaseException')

            commenter_urls = []

            # 댓글 작성자 블로그 URL 추출
            try:
                with ThreadingTimeout(5.0) as timeout_ctx:
                    assert timeout_ctx.state == timeout_ctx.EXECUTING
                    commenter_urls = self.get_commenter_urls_from_post(blog_url=blog_url)
            # except ThreadingTimeout:
            #     print('ThreadingTimeout')
            except AttributeError:
                print('AttributeError')
            except NoSuchElementException:
                print('NoSuchElementException')
            except BaseException:
                print('BaseException')

            print("comment urls: " + str(commenter_urls))

            sympathy_urls = []

            # 공감 누른 사람 블로그 URL 추출
            try:
                with ThreadingTimeout(5.0) as timeout_ctx:
                    assert timeout_ctx.state == timeout_ctx.EXECUTING
                    sympathy_urls = self.get_sympathy_urls_from_post(blog_url=blog_url)
            # except ThreadingTimeout:
            #     print('ThreadingTimeout')
            except AttributeError:
                print('AttributeError')
            except NoSuchElementException:
                print('NoSuchElementException')
            except BaseException:
                print('BaseException')

            print("sympathy urls: " + str(sympathy_urls))

            # 개별 댓글 작성자마다 블로그로 들어가서 아이디 추출
            for commenter_url in commenter_urls:
                # 목표한 아이디 개수가 채워졌으면 크롤러 종료
                if self.close_down:
                    raise CloseSpider(reason='목표 아이디 개수 달성')

                # 개별 블로그에서 아이디 추출, 글 게시자=False (댓글 작성자이기 때문)
                try:
                    with ThreadingTimeout(5.0) as timeout_ctx:
                        assert timeout_ctx.state == timeout_ctx.EXECUTING
                        yield self.get_id_from_blog(blog_url=commenter_url, original_poster=False)
                # except ThreadingTimeout:
                #     print('ThreadingTimeout')
                #     continue
                except AttributeError:
                    print('AttributeError')
                    continue
                except NoSuchElementException:
                    print('NoSuchElementException')
                    continue
                except BaseException:
                    print('BaseException')
                    continue

            # 개별 공감 누른 사람마다 블로그로 들어가서 아이디 추출
            for sympathy_url in sympathy_urls:
                # 목표한 아이디 개수가 채워졌으면 크롤러 종료
                if self.close_down:
                    raise CloseSpider(reason='목표 아이디 개수 달성')

                # 개별 블로그에서 아이디 추출, 글 게시자=False (댓글 작성자이기 때문)
                try:
                    with ThreadingTimeout(5.0) as timeout_ctx:
                        assert timeout_ctx.state == timeout_ctx.EXECUTING
                        yield self.get_id_from_blog(blog_url=sympathy_url, original_poster=False)
                # except ThreadingTimeout:
                #     print('ThreadingTimeout')
                #     continue
                except AttributeError:
                    print('AttributeError')
                    continue
                except NoSuchElementException:
                    print('NoSuchElementException')
                    continue
                except BaseException:
                    print('BaseException')
                    continue

        # 크롤링 할 블로그 검색 결과 페이지 수
        # if self.page_count < 1:
        if True:
            self.page_count += 1
            yield scrapy.Request(
                urlparse.urljoin(self.url_head, next_page['href']),
                callback=self.parse
            )

    def get_id_from_blog(self, blog_url, original_poster=True):
        # 네이버 모듈에서 개별 블로그에서 유저 아이디 찾기 호출
        try:
            with ThreadingTimeout(5.0) as timeout_ctx:
                assert timeout_ctx.state == timeout_ctx.EXECUTING
                user_id = naver_crawler.get_naver_blog_id(driver=self.driver, blog_url=blog_url)
        # except ThreadingTimeout:
        #     print('ThreadingTimeout')
        #     raise ThreadingTimeout
        except AttributeError:
            print('AttributeError')
            raise AttributeError
        except NoSuchElementException:
            print('NoSuchElementException')
            raise NoSuchElementException
        except BaseException:
            print('BaseException')
            raise BaseException

        return {
            'user_id': user_id,
            'original_poster': original_poster
        }

    def get_commenter_urls_from_post(self, blog_url):
        try:
            with ThreadingTimeout(5.0) as timeout_ctx:
                assert timeout_ctx.state == timeout_ctx.EXECUTING
                commenter_urls = naver_crawler.get_commenter_urls(driver=self.driver, blog_url=blog_url)
        # except ThreadingTimeout:
        #     print('ThreadingTimeout')
        #     raise ThreadingTimeout
        except AttributeError:
            print('AttributeError')
            raise AttributeError
        except NoSuchElementException:
            print('NoSuchElementException')
            raise NoSuchElementException
        except BaseException:
            print('BaseException')
            raise BaseException

        return commenter_urls

    def get_sympathy_urls_from_post(self, blog_url):
        try:
            with ThreadingTimeout(5.0) as timeout_ctx:
                assert timeout_ctx.state == timeout_ctx.EXECUTING
                sympathy_urls = naver_crawler.get_sympathy_urls(driver=self.driver, blog_url=blog_url)
        # except ThreadingTimeout:
        #     print('ThreadingTimeout')
        #     raise ThreadingTimeout
        except AttributeError:
            print('AttributeError')
            raise AttributeError
        except NoSuchElementException:
            print('NoSuchElementException')
            raise NoSuchElementException
        except BaseException:
            print('BaseException')
            raise BaseException

        return sympathy_urls


items = []


# 코드 내부에서 크롤링 데이터 받기 위한 파이프라인
class ItemCollectorPipeline(object):
    def __init__(self):
        self.ids_seen = set()
        self.np_items_cnt = 0

    def process_item(self, item, spider):
        scraped_obj_container = list()

        scraped_obj_container.append(item)

        for scraped_obj in scraped_obj_container:
            if scraped_obj['user_id'] in self.ids_seen:
                raise DropItem("Duplicate item found: {0}".format(item['user_id']))
            else:
                self.ids_seen.add(scraped_obj['user_id'])
                items.append(scraped_obj)
                if not scraped_obj['original_poster']:
                    self.np_items_cnt += 1

        print('scraped object: ' + str(scraped_obj_container) + ' ==> count: ' + str(len(items)))

        # 목표한 (유효) 아이디 개수가 채워졌으면 크롤러 종료
        if self.np_items_cnt >= spider.target_id_count:
            spider.close_down = True


# 메인 함수
if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'LOG_LEVEL': 'INFO',
        'ITEM_PIPELINES': {'__main__.ItemCollectorPipeline': 100}
    })

    # 커맨드라인 프롬프트에서 목표 아이디 개수, 검색 키워드를 입력
    while True:
        id_count = 0
        try:
            id_count = int(input("목표 아이디 개수: "))
        except ValueError:
            print("올바른 입력이 아닙니다. 정확한 숫자를 입력해주세요.")
            continue
        break

    while True:
        keywords_list = []
        try:
            keywords_list = input("키워드 (큰 따옴표 사이 입력, 복수 키워드는 쉼표+공백으로 띄워서 입력): ").split(", ")
            keywords_list = [re.search(r'\"(.*?)\"', keyword).group(1) for keyword in keywords_list]
        except AttributeError:
            print("올바른 입력이 아닙니다. 키워드를 정확한 양식에 따라 입력해주세요.")
            continue
        break

    start = time.time()
    now = time.localtime()
    hour_str = now.tm_hour if now.tm_hour > 9 else '0{0}'.format(str(now.tm_hour))
    min_str = now.tm_min if now.tm_min > 9 else '0{0}'.format(str(now.tm_min))

    process.crawl(NaverSpider, keywords=keywords_list, target_id_count=id_count)
    process.start()

    end = time.time()
    time_taken_str = '총 걸린 시간: {0} 초'.format(str(end - start))

    all_ids = [item['user_id'] for item in items]
    np_ids = [item['user_id'] for item in items if not item['original_poster']]

    print("Aggregate: " + str(items) + ", length: " + str(len(items)))
    print("Distinct: " + str(all_ids) + ", length: " + str(len(all_ids)))
    print("Non-Poster: " + str(np_ids) + ", length: " + str(len(np_ids)))

    print(time_taken_str)

    search_keyword = '_'.join(keywords_list[0].split(" "))

    total_file_name = './results/{2}-{3}-{4}-{5}-{6}_{0}_{1}_total.txt'\
        .format(search_keyword, id_count, now.tm_year, now.tm_mon, now.tm_mday, hour_str, min_str)
    np_file_name = './results/{2}-{3}-{4}-{5}-{6}_{0}_{1}_np.txt'\
        .format(search_keyword, id_count, now.tm_year, now.tm_mon, now.tm_mday, hour_str, min_str)

    with open(total_file_name, 'w') as f:
        for all_id in all_ids:
            f.write('{0}\n'.format(all_id))

    with open(np_file_name, 'w') as f:
        for np_id in np_ids:
            f.write('{0}\n'.format(np_id))

    pltfrm = platform.uname()
    email_msg = """
    {0}
    
    --- 아이디 추출 현황 ---
    원글 게시자 포함 개수: {7}
    원글 게시자 제외 개수: {8}
    
    --- 시스템 환경 ---
    System: {1}
    Node: {2}
    Release: {3}
    Version: {4}
    Machine: {5}
    Processor: {6}
    """.format(
        time_taken_str, pltfrm[0], pltfrm[1], pltfrm[2], pltfrm[3], pltfrm[4], pltfrm[5],
        len(all_ids), len(np_ids)
    )

    # 결과 파일들 이메일로 전송
    send_mail(
        recipient_list=['etture@gmail.com'],
        subject_line='블로그 아이디 크롤링 - 키워드: "{0}", 타겟: {1}, {2}/{3}/{4} {5}:{6}'.format(search_keyword, id_count, now.tm_year, now.tm_mon, now.tm_mday, hour_str, min_str),
        message=email_msg,
        attachment_files=[total_file_name, np_file_name]
    )
