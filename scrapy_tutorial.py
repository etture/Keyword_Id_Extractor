import scrapy


class ScrapySpider(scrapy.Spider):
    name = 'scrapy_spider'
    start_urls = ['https://docs.scrapy.org/en/latest/_static/selectors-sample1.html']

    def parse(self, response):
        pass
