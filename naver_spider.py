import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse
from selenium import webdriver
from naver import get_naver_blog_id


class NaverSpider(scrapy.Spider):

    name = 'naver_spider'

    def __init__(self, keywords=['']):
        scrapy.Spider.__init__(self)
        template_url = 'https://search.naver.com/search.naver?query={0}&where=post&sm=tab_nmr&nso='

        self.options = webdriver.ChromeOptions()
        self.options.add_argument('headless')
        self.options.add_argument('window-size=1920x1080')
        self.options.add_argument("disable-gpu")
        self.driver = webdriver.Chrome('./chromedriver', options=self.options)

        self.start_urls = []
        for keyword in keywords:
            self.start_urls.append(template_url.format(keyword))

    def parse(self, response):
        # 키워드 입력 시 블로그 글 검색 결과 (목록)
        BLOG_ITEM_SELECTOR = '#wrap #container .pack_group #main_pack .blog ul li dl dt'

        self.driver.get(response.url)

        resp = TextResponse(url='', body=self.driver.page_source, encoding='utf-8')

        # 개별 블로그 글
        for blog_item in resp.css(BLOG_ITEM_SELECTOR):
            TITLE_SELECTOR = 'a::attr(title)'
            URL_SELECTOR = 'a::attr(href)'

            title = blog_item.css(TITLE_SELECTOR).get()
            blog_url = blog_item.css(URL_SELECTOR).get()
            print("URL: " + blog_url)

            # 블로그 글 제목, 글 URL
            # yield scrapy.Request(
            #     blog_url,
            #     callback=self.parse_blog
            # )
            yield {
                'user_id': get_naver_blog_id(blog_url),
            }


    def parse_blog(self, blog_url):
        # 블로그 주인 아이디
        BLOG_OWNER_SELECTOR = '#blog-profile .border .bg-body .con .name .nick span ::text'
        COMMENT_SELECTOR = 'span.u_cbox_contents ::text'
        USER_SELECTOR = 'span.name.align ::text'

        # self.driver.get(response.url)
        # resp = TextResponse(url='', body=self.driver.page_source, encoding='utf-8')

        yield {
            # 'blog_owner': response.css(BLOG_OWNER_SELECTOR).get(),
            # 'comment': response.css(COMMENT_SELECTOR).getall(),
            # 'user': resp.css(USER_SELECTOR).getall(),
            # 'user': self.driver.find_element_by_css_selector('span.itemfont.col')
            'user_id': get_naver_blog_id(blog_url)
        }


items = []


# 코드 내부에서 크롤링 데이터 받기 위한 파이프라인
class ItemCollectorPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        items.append(item)


process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
    'LOG_LEVEL': 'INFO',
    'ITEM_PIPELINES': {'__main__.ItemCollectorPipeline': 100}
})
process.crawl(NaverSpider(), keywords=['갤럭시S10'])
process.start()


for item in items:
    # print('Blog title: ' + item['title'] + ', URL: ' + item['url'])
    # print('Blog owner: ' + item['blog_owner'])
    print(item)
