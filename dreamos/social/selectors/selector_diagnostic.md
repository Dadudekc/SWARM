# Social Media Platform Selectors

This file contains CSS selectors for social media platform elements.
Selectors are organized by platform and element type.

## Twitter

* tweet_input: div[data-testid="tweetTextarea_0"]
* tweet_button: div[data-testid="tweetButton"]
* home_link: a[href="/home"]
* profile_link: a[href*="/profile"]
* compose_button: a[href="/compose/tweet"]

## Reddit

* text_post_button: button[aria-label="Post"]
* title_input: textarea[placeholder="Title"]
* content_input: div[data-testid="post-composer-textarea"]
* submit_button: button[type="submit"]
* subreddit_input: input[placeholder="Choose a community"]

## Instagram

* post_button: button[type="button"]
* caption_input: textarea[aria-label="Write a caption..."]
* image_upload: input[type="file"]
* location_input: input[placeholder="Add location"]
* hashtag_input: textarea[aria-label="Write a caption..."]

## LinkedIn

* post_button: button[aria-label="Start a post"]
* post_input: div[aria-label="What do you want to talk about?"]
* publish_button: button[aria-label="Post"]
* profile_link: a[href*="/in/"]
* home_link: a[href="/feed/"]

## Facebook

* post_button: div[aria-label="Create Post"]
* post_input: div[aria-label="What's on your mind?"]
* publish_button: div[aria-label="Post"]
* profile_link: a[href*="/profile.php"]
* home_link: a[href="/home.php"]

## Stocktwits

* post_button: button[aria-label="Post"]
* message_input: textarea[placeholder="What's happening?"]
* symbol_input: input[placeholder="Add symbols"]
* submit_button: button[type="submit"]
* profile_link: a[href*="/profile"] 