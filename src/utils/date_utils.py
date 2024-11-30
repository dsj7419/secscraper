"""
Date handling utilities for the SEC Earnings Scraper.
"""
from datetime import datetime, date, timedelta
from typing import Generator, Optional
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


class TradingCalendar:
    """Handles trading calendar related operations."""
    
    def __init__(self):
        self.calendar = USFederalHolidayCalendar()
    
    def is_trading_day(self, date_: date) -> bool:
        """
        Check if a given date is a trading day.
        
        Args:
            date_: Date to check
            
        Returns:
            bool: True if it's a trading day, False otherwise
        """
        # Check if it's a weekend
        if date_.weekday() >= 5:
            return False
        
        # Check if it's a holiday
        holidays = self.calendar.holidays(
            start=date_,
            end=date_
        )
        return len(holidays) == 0
    
    def next_trading_day(self, date_: date) -> date:
        """
        Get the next trading day after the given date.
        
        Args:
            date_: Starting date
            
        Returns:
            date: Next trading day
        """
        next_day = date_ + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def get_trading_days(
        self,
        start_date: date,
        end_date: date
    ) -> Generator[date, None, None]:
        """
        Generate all trading days between start_date and end_date.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Yields:
            date: Each trading day in the range
        """
        current_date = start_date
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                yield current_date
            current_date += timedelta(days=1)


def parse_date(date_str: str) -> Optional[date]:
    """
    Safely parse a date string into a date object.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Optional[date]: Parsed date or None if parsing fails
    """
    try:
        return pd.to_datetime(date_str).date()
    except (ValueError, TypeError):
        return None


def get_date_range(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    days_back: int = 0
) -> tuple[date, date]:
    """
    Get a date range based on input parameters.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        days_back: Number of days to look back if start_date not provided
        
    Returns:
        tuple[date, date]: Start and end dates
    """
    if end_date is None:
        end_date = datetime.now().date()
    
    if start_date is None:
        start_date = end_date - timedelta(days=days_back)
    
    return start_date, end_date