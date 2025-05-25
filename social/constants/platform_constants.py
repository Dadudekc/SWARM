"""
Platform Constants
-----------------
Central location for all platform-specific constants.
"""

# Common Constants
MAX_RETRIES = 3
RETRY_DELAY = 2
DEFAULT_TIMEOUT = 10

# Twitter Constants
TWITTER_MAX_IMAGES = 4
TWITTER_MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512MB
TWITTER_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
TWITTER_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}

# Reddit Constants
REDDIT_MAX_IMAGES = 20
REDDIT_MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
REDDIT_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
REDDIT_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}

# Facebook Constants
FACEBOOK_MAX_IMAGES = 30
FACEBOOK_MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
FACEBOOK_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
FACEBOOK_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}

# Instagram Constants
INSTAGRAM_MAX_IMAGES = 10
INSTAGRAM_MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
INSTAGRAM_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png'}
INSTAGRAM_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov'}

# LinkedIn Constants
LINKEDIN_MAX_IMAGES = 9
LINKEDIN_MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200MB
LINKEDIN_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
LINKEDIN_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}

# StockTwits Constants
STOCKTWITS_MAX_IMAGES = 4
STOCKTWITS_MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
STOCKTWITS_SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
STOCKTWITS_SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}

# Platform-specific XPath selectors
MEDIA_BUTTON_XPATHS = {
    "twitter": "//input[@data-testid='fileInput']",
    "reddit": "//div[@data-testid='fileInput']",
    "facebook": "//input[@type='file']",
    "instagram": "//input[@type='file']",
    "linkedin": "//input[@type='file']",
    "stocktwits": "//input[@type='file']"
}

FILE_INPUT_XPATHS = {
    "twitter": "//input[@data-testid='fileInput']",
    "reddit": "//input[@type='file']",
    "facebook": "//input[@type='file']",
    "instagram": "//input[@type='file']",
    "linkedin": "//input[@type='file']",
    "stocktwits": "//input[@type='file']"
} 