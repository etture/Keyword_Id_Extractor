import scrapy


class BrickSetSpider(scrapy.Spider):
    name = "brickset_spider"
    # start_urls = ['http://brickset.com/sets/year-2016']
    start_urls = ['https://blog.naver.com/PostView.nhn?blogId=wayfater&logNo=221497246902&from=search&redirect=Log&widgetTypeCall=true&topReferer=https%3A%2F%2Fsearch.naver.com%2Fsearch.naver%3Fsm%3Dtop_hty%26fbm%3D1%26ie%3Dutf8%26query%3D%25EC%2595%2584%25EC%259D%25B4%25ED%258C%25A8%25EB%2593%259C&directAccess=false']

    ACTUAL_URL = 'body iframe ::attr(scr)'
    '//*[@id="blog-profile"]/div/div[2]/div/div[2]/div/span'
    
    def parse(self, response):
        yield {
            # 'name': brickset.css(NAME_SELECTOR).extract_first(),
            # 'pieces': brickset.xpath(PIECES_SELECTOR).extract_first(),
            # 'minifigs': brickset.xpath(MINIFIGS_SELECTOR).extract_first(),
            # 'image': brickset.css(IMAGE_SELECTOR).extract_first(),
            # 'owner': response.css('span.itemfont.col ::text').get()
            'owner': response.css(".title.pcol2").get()
        }
        # SET_SELECTOR = ".set"
        # for brickset in response.css(SET_SELECTOR):
        #     NAME_SELECTOR = "h1 ::text"
        #     PIECES_SELECTOR = './/dl[dt/text() = "Pieces"]/dd/a/text()'
        #     MINIFIGS_SELECTOR = './/dl[dt/text() = "Minifigs"]/dd/a/text()'
        #     IMAGE_SELECTOR = 'img ::attr(src)'
        #     yield {
        #         # 'name': brickset.css(NAME_SELECTOR).extract_first(),
        #         # 'pieces': brickset.xpath(PIECES_SELECTOR).extract_first(),
        #         # 'minifigs': brickset.xpath(MINIFIGS_SELECTOR).extract_first(),
        #         # 'image': brickset.css(IMAGE_SELECTOR).extract_first(),
        #     }

        # NEXT_PAGE_SELECTOR = '.next a ::attr(href)'
        # next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()
        # if next_page:
        #     yield scrapy.Request(
        #         response.urljoin(next_page),
        #         callback=self.parse
        #     )
