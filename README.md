# Twitter Automation AI

This repository contains a Python script designed to automate interacting with Twitter using scraped data and generating insightful replies using OpenAI's language model. The script searches for tweets containing specific keywords and replies to them with contextually relevant comments.

## Table of Contents

- [Twitter Automation AI](#twitter-automation-ai)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [Tips](#tips)
  - [Disclaimer](#disclaimer)

## Features

- **Automated Tweet Search**: Searches for tweets containing configurable keywords.
- **OpenAI Integration**: Generates insightful replies using OpenAI's GPT-4 model.
- **Engagement-Based Sorting**: Sorts tweets based on engagement metrics such as likes, retweets, and replies.
- **Configurable Frequency**: Controls the frequency of tweet responses to avoid rate limits and spam detection.

## Requirements

- Python 3.7 or higher
- `twscrape` library for scraping tweets
- `openai` library for interacting with OpenAI's API
- A Twitter account with accessible cookie data
- OpenAI API key

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/ihuzaifashoukat/twitter-automation-ai.git
    cd twitter-automation-ai
    ```

2. **Create a virtual environment** (optional but recommended)

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. **OpenAI API Key**
    - Replace the placeholder value in the script:
    ```python
    openai_api_key = "your-openai-api-key"
    ```

2. **Twitter Cookie Data**
    - Replace the placeholder value in the script with your Twitter account cookies:
    ```python
    twitter_cookie_data = '{"ct0": "your-ct0-value", "auth_token": "your-auth-token"}'
    ```

3. **Target Keywords**
    - You can customize the keywords to search for:
    ```python
    target_keywords = ["Linkedin", "Content", "Marketing", "Copywriting", "Ghostwriting"]
    ```

4. **Response Interval**
    - Adjust the base interval to control how frequently replies are sent:
    ```python
    response_interval = 300  # 5 minutes
    ```

5. **Maximum Tweets Per Keyword**
    - Set the maximum number of tweets to fetch per keyword to prioritize top accounts:
    ```python
    max_tweets_per_keyword = 15
    ```

## Usage

To run the script:

```bash
python app.py
```

The script will:
1. Initialize the Twitter and OpenAI clients.
2. Search for tweets containing the specified keywords.
3. Filter and sort tweets based on engagement metrics.
4. Generate replies using OpenAI and post them to Twitter.
5. Repeat the process at intervals defined by `response_interval`.

## Tips

- **Rate Limits**: Be cautious with the number of requests to avoid hitting Twitter's rate limits. The script includes handling for rate limits and waits for 15 minutes if limits are exceeded.
- **Engagement Metrics**: Adjust the `filter_and_sort_tweets` function if you need a different sorting algorithm or additional filtering criteria.
- **Logging**: Enhance the `print` statements with proper logging if you're planning to run this script in a production environment.

## Disclaimer

- **Respect Twitter's Terms of Service**: Ensure that your usage complies with Twitter's rules and guidelines, especially regarding automation.
- **OpenAI's Use Case Policy**: Make sure your application adheres to OpenAI's use case policy.
- **Ethical Considerations**: Use this script responsibly. Avoid using it for spamming, trolling, or any other unethical activity.

---

**Note**: This script is a basic implementation and might require adjustments and refinements based on your specific use case and requirements. Always test thoroughly in a controlled environment before deploying it in production.