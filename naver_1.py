import scrapy
from scrapy.crawler import CrawlerProcess


class NaverSpider(scrapy.Spider):

    name = 'naver_spider'

    def __init__(self, keyword=''):
        scrapy.Spider.__init__(self)
        template_url = 'https://search.naver.com/search.naver?query={0}&where=post&sm=tab_nmr&nso='
        self.start_urls = [template_url.format(keyword)]

    def parse(self, response):
        # 키워드 입력 시 블로그 글 검색 결과 (목록)
        BLOG_ITEM_SELECTOR = '#wrap #container .pack_group #main_pack .blog ul li dl dt'

        # 개별 블로그 글
        for blog_item in response.css(BLOG_ITEM_SELECTOR):
            TITLE_SELECTOR = 'a::attr(title)'
            URL_SELECTOR = 'a::attr(href)'

            # 블로그 글 제목, 글 URL
            yield {
                'title': blog_item.css(TITLE_SELECTOR).get(),
                'url': blog_item.css(URL_SELECTOR).get(),
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
process.crawl(NaverSpider(), keyword='매직트랙패드2')
process.start()


for item in items:
    print('Blog title: ' + item['title'] + ', URL: ' + item['url'])
