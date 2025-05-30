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

# Rate Limiting Constants
RATE_LIMIT_WINDOW = 3600  # 1 hour window
DEFAULT_COOLDOWN = 300    # 5 minutes cooldown

# Platform-specific rate limits (per hour)
PLATFORM_RATE_LIMITS = {
    "twitter": {
        "post": 50,           # 50 tweets per hour
        "media_upload": 100,  # 100 media uploads per hour
        "like": 100,          # 100 likes per hour
        "retweet": 50,        # 50 retweets per hour
        "follow": 50,         # 50 follows per hour
        "comment": 100        # 100 comments per hour
    },
    "facebook": {
        "post": 30,           # 30 posts per hour
        "media_upload": 50,   # 50 media uploads per hour
        "like": 100,          # 100 likes per hour
        "comment": 100,       # 100 comments per hour
        "share": 30           # 30 shares per hour
    },
    "reddit": {
        "post": 20,           # 20 posts per hour
        "media_upload": 30,   # 30 media uploads per hour
        "comment": 50,        # 50 comments per hour
        "upvote": 100,        # 100 upvotes per hour
        "downvote": 100       # 100 downvotes per hour
    },
    "instagram": {
        "post": 20,           # 20 posts per hour
        "media_upload": 30,   # 30 media uploads per hour
        "like": 100,          # 100 likes per hour
        "comment": 50,        # 50 comments per hour
        "follow": 50          # 50 follows per hour
    },
    "linkedin": {
        "post": 20,           # 20 posts per hour
        "media_upload": 30,   # 30 media uploads per hour
        "like": 100,          # 100 likes per hour
        "comment": 50,        # 50 comments per hour
        "connect": 50         # 50 connection requests per hour
    },
    "stocktwits": {
        "post": 50,           # 50 posts per hour
        "media_upload": 50,   # 50 media uploads per hour
        "like": 100,          # 100 likes per hour
        "comment": 100,       # 100 comments per hour
        "follow": 50          # 50 follows per hour
    }
} 