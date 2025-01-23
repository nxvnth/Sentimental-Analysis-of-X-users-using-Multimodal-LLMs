import asyncio
import json
from typing import List, Dict, Any
from twscrape import API, gather

class XDataScraper:
    def __init__(self, users: List[str] = None, limit: int = 50):
        """
        Initialize the X Data Scraper with configurable parameters.
        
        Args:
            users (List[str]): List of X usernames to scrape
            limit (int): Maximum number of tweets to collect per user
        """
        self.users = users or []
        self.limit = limit
        self.all_tweets: List[Dict[str, Any]] = []

    async def fetch_tweets(self, username: str) -> List[Dict[str, Any]]:
        """
        Asynchronously fetch tweets for a given username.
        
        Args:
            username (str): X username to scrape tweets from
        
        Returns:
            List of tweet dictionaries with detailed metadata
        """
        # Construct advanced search query to exclude retweets
        search_query = f"from:{username} exclude:retweets"
        
        try:
            # Initialize Twitter API
            api = API()
            await api.pool.login_all()  # Ensure all accounts are logged in

            # Fetch tweets with comprehensive metadata
            tweets = await gather(api.search(search_query, limit=self.limit))
            
            # Transform tweet data into a structured format
            results = [
                {
                    "username": username,
                    "content": tweet.rawContent,
                    "created_at": tweet.createdAt.isoformat(),
                    "likes": tweet.likeCount,
                    "retweets": tweet.retweetCount,
                    "quote_count": tweet.quoteCount,
                    "reply_count": tweet.replyCount,
                    "language": tweet.lang
                } 
                for tweet in tweets
            ]
            
            return results
        
        except Exception as e:
            print(f"Error scraping tweets for {username}: {e}")
            return []

    async def scrape_users_tweets(self, users: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape tweets for multiple users concurrently.
        
        Args:
            users (List[str], optional): List of usernames to scrape. 
                                         Uses instance users if not provided.
        
        Returns:
            Comprehensive list of tweets across all specified users
        """
        # Use provided users or fall back to instance users
        target_users = users or self.users
        
        # Use asyncio to scrape tweets concurrently
        tasks = [self.fetch_tweets(username) for username in target_users]
        user_tweets = await asyncio.gather(*tasks)
        
        # Flatten the list of tweet lists
        self.all_tweets = [tweet for user_tweets_list in user_tweets for tweet in user_tweets_list]
        
        return self.all_tweets

def create_x_data_collector_task(users: List[str]) -> Dict[str, Any]:
    """
    CrewAI-compatible function to collect X data and return as a dictionary.
    
    Args:
        users (List[str]): List of X usernames to scrape
    
    Returns:
        Dictionary containing scraped tweet data
    """
    # Use a separate async function to handle the scraping
    async def async_scrape():
        scraper = XDataScraper(users)
        tweets = await scraper.scrape_users_tweets()
        scraper.save_to_json()  # Optional: save to JSON
        return tweets

    # Check if an event loop is already running
    try:
        # Try to get the current running event loop
        loop = asyncio.get_running_loop()
        
        # If we're already in an event loop, use ensure_future
        future = asyncio.ensure_future(async_scrape())
        return {
            "data_source": "X (Twitter)",
            "users_analyzed": users,
            "total_tweets_collected": 0,  # Placeholder, will be updated when the future is done
            "tweets": []  # Placeholder
        }
    except RuntimeError:
        # No event loop running, use run_until_complete or run
        tweets = asyncio.get_event_loop().run_until_complete(async_scrape())
        
        return {
            "data_source": "X (Twitter)",
            "users_analyzed": users,
            "total_tweets_collected": len(tweets),
            "tweets": tweets
        }

def save_to_json(tweets: List[Dict[str, Any]], filename: str = 'tweets.json') -> None:
    """
    Save collected tweets to a JSON file with proper formatting.
    
    Args:
        tweets (List[Dict[str, Any]]): List of tweet dictionaries
        filename (str): Output JSON filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(tweets, file, ensure_ascii=False, indent=4)
        
        print(f"Successfully saved {len(tweets)} tweets to {filename}")
    
    except IOError as e:
        print(f"Error saving JSON file: {e}")

# Main execution for testing
if __name__ == "__main__":
    users = ["elonmusk", "naval", "sama"]
    result = create_x_data_collector_task(users)
    print(f"Collected {result['total_tweets_collected']} tweets")