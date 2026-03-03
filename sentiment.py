import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from src.utils.logger import get_logger

logger = get_logger("sentiment")

def analyze_news_sentiment(news_df: pd.DataFrame) -> dict:
    """
    Analyzes sentiment of news headlines.
    Returns aggregate score and label.
    """
    if news_df.empty or 'title' not in news_df.columns:
        return {"score": 0.0, "label": "NEUTRAL", "count": 0}
    
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    
    for title in news_df['title']:
        vs = analyzer.polarity_scores(str(title))
        scores.append(vs['compound'])
        
    avg_score = sum(scores) / len(scores)
    
    label = "NEUTRAL"
    if avg_score >= 0.05:
        label = "POSITIVE"
    elif avg_score <= -0.05:
        label = "NEGATIVE"
        
    logger.info(f"Sentiment Analysis: {label} ({avg_score:.2f})")
    
    return {
        "score": avg_score,
        "label": label,
        "count": len(scores)
    }