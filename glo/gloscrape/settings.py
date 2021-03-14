"""
Scrapy settings for tutorial project

For simplicity, this file contains only settings considered important or
commonly used. You can find more settings consulting the documentation:

     https://docs.scrapy.org/en/latest/topics/settings.html
     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
"""

BOT_NAME = "gloscrape"

SPIDER_MODULES = ["gloscrape.spiders"]
NEWSPIDER_MODULE = "gloscrape.spiders"


# Crawl responsibly by identifying yourself
# (and your website) on the user-agent
# USER_AGENT = 'glo (+https://github.com/learnitall/glo)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 5
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,'
#             'application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {"scrapy_splash.SplashDeduplicateArgsMiddleware": 100}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "gloscrape.middlewares.WindscribeMiddleware": 560,
    "scrapy_splash.SplashCookiesMiddleware": 723,
    "scrapy_splash.SplashMiddleware": 725,
    "gloscrape.middlewares.SplashRequestMiddleware": 722,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}
# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 3
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 30
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 3.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

RETRY_ENABLED = True
RETRY_TIMES = 4  # initial response + 4 retries = 5 requests
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403]

# Enable and configure HTTP caching (disabled by default)
HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = RETRY_HTTP_CODES
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

SPLASH_URL = "http://127.0.0.1:8050"
DUPEFILTER_CLASS = "scrapy_splash.SplashAwareDupeFilter"
DUPEFILTER_DEBUG = True
HTTPCACHE_STORAGE = "scrapy_splash.SplashAwareFSCacheStorage"
REFERER_ENABLED = False

# Parsed from https://github.com/tamimibrahim17/List-of-user-agents
USER_AGENT_FILE = "gloscrape/extra/uas-small.txt"
WS_VPN_LIST_FILE = "gloscrape/extra/windscribe-akamai.txt"
