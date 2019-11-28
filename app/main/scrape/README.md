## Crawling Smart Credit (Consumer Direct)

The credit report file is rendered via Javascript and so requires a browser environment that will support
the Javascript execution so the HTML content will be available to Scrapy.

Dynamic content works by using [Splash](https://github.com/scrapy-plugins/scrapy-splash)

Run the following command before executing the crawler:

`docker run -p 8050:8050 scrapinghub/splash`

Then, you can run the `credit_report_crawler` with the following command 
(while in `app/main/scrape` dir): 

`scrapy crawl creditreport -o output.json`


This will generate a JSON file with the contents of the scraped credit report.