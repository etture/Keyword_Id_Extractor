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
from stopit import ThreadingTimeout as Timeout, TimeoutException


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
                with Timeout(15.0) as timeout_ctx:
                    yield self.get_id_from_blog(blog_url=blog_url, original_poster=True)
            except TimeoutException:
                print('TimeoutException')
            except AttributeError:
                print('AttributeError')
            except NoSuchElementException:
                print('NoSuchElementException')
            except BaseException:
                print('BaseException')

            commenter_urls = []

            # 댓글 작성자 블로그 URL 추출
            try:
                with Timeout(15.0) as timeout_ctx:
                    commenter_urls = self.get_commenter_urls_from_post(blog_url=blog_url)
            except TimeoutException:
                print('TimeoutException')
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
                with Timeout(15.0) as timeout_ctx:
                    sympathy_urls = self.get_sympathy_urls_from_post(blog_url=blog_url)
            except TimeoutException:
                print('TimeoutException')
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
                    with Timeout(15.0) as timeout_ctx:
                        yield self.get_id_from_blog(blog_url=commenter_url, original_poster=False)
                except TimeoutException:
                    print('TimeoutException')
                    continue
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
                    with Timeout(15.0) as timeout_ctx:
                        yield self.get_id_from_blog(blog_url=sympathy_url, original_poster=False)
                except TimeoutException:
                    print('TimeoutException')
                    continue
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

    def parse_comments(self, commenter_urls):
        # 개별 댓글 작성자마다 블로그로 들어가서 아아디 추출
        for commenter_url in commenter_urls:
            # 목표한 아이디 개수가 채워졌으면 크롤러 종료
            if self.close_down:
                raise CloseSpider(reason='목표 아이디 개수 달성')

            ids_list = []

            # 개별 블로그에서 아이디 추출, 글 게시자=False (댓글 작성자이기 때문)
            try:
                with Timeout(15.0) as timeout_ctx:
                    ids_list.append(self.get_id_from_blog(blog_url=commenter_url, original_poster=False))
            except TimeoutException:
                print('TimeoutException')
                continue
            except AttributeError:
                print('AttributeError')
                continue
            except NoSuchElementException:
                print('NoSuchElementException')
                continue
            except BaseException:
                print('BaseException')
                continue

            return {
                'is_list': True,
                'ids_list': ids_list
            }

    def get_id_from_blog(self, blog_url, original_poster=True):
        # 네이버 모듈에서 개별 블로그에서 유저 아이디 찾기 호출
        try:
            with Timeout(15.0) as timeout_ctx:
                user_id = naver_crawler.get_naver_blog_id(driver=self.driver, blog_url=blog_url)
        except TimeoutException:
            print('TimeoutException')
            raise Timeout
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
            'is_list': False,
            'user_id': user_id,
            'original_poster': original_poster
        }

    def get_commenter_urls_from_post(self, blog_url):
        try:
            with Timeout(15.0) as timeout_ctx:
                commenter_urls = naver_crawler.get_commenter_urls(driver=self.driver, blog_url=blog_url)
        except TimeoutException:
            print('TimeoutException')
            raise Timeout
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
            with Timeout(15.0) as timeout_ctx:
                sympathy_urls = naver_crawler.get_sympathy_urls(driver=self.driver, blog_url=blog_url)
        except TimeoutException:
            print('TimeoutException')
            raise Timeout
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

    def process_item(self, item, spider):
        scraped_obj_container = []

        if item['is_list']:
            scraped_obj_container = item['ids_list']
        else:
            scraped_obj_container.append(item)

        for scraped_obj in scraped_obj_container:
            if scraped_obj['user_id'] in self.ids_seen:
                raise DropItem("Duplicate item found: {0}".format(item['user_id']))
            else:
                self.ids_seen.add(scraped_obj['user_id'])
                items.append(scraped_obj)

        print('scraped object: ' + str(scraped_obj_container) + ' ==> count: ' + str(len(items)))

        # 목표한 아이디 개수가 채워졌으면 크롤러 종료
        if len(items) >= spider.target_id_count:
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
    process.crawl(NaverSpider, keywords=keywords_list, target_id_count=id_count)
    process.start()

    end = time.time()
    print("Aggregate: " + str(items) + ", length: " + str(len(items)))
    print("Distinct: " + str(list(set([item['user_id'] for item in items]))) + ", length: " + str(len(set([item['user_id'] for item in items]))))
    print("Non-Poster: " + str(list(set(([item['user_id'] for item in items if item['original_poster'] == False]))) + ", length: " + str(len(set([item['user_id'] for item in items])))))

    print("Total time taken: " + str(end-start) + " seconds")
