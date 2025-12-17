import pytest
from pydantic import ValidationError
from surfhub.serper.model import SerpRequestOptions, TimeRange


class TestSerpRequestOptions:
    """Test cases for SerpRequestOptions model"""
    
    def test_valid_time_range_values(self):
        """Test that all valid time_range enum values are accepted"""
        for time_range in [TimeRange.DAY, TimeRange.WEEK, TimeRange.MONTH, TimeRange.YEAR]:
            options = SerpRequestOptions(time_range=time_range)
            assert options.time_range == time_range
    
    def test_invalid_time_range_value(self):
        """Test that invalid time_range values are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(time_range="invalid")
        
        assert "time_range" in str(exc_info.value)
    
    def test_valid_date_start_format(self):
        """Test that valid date_start format is accepted"""
        options = SerpRequestOptions(date_start="2024-01-01")
        assert options.date_start == "2024-01-01"
    
    def test_valid_date_end_format(self):
        """Test that valid date_end format is accepted"""
        options = SerpRequestOptions(date_end="2024-12-31")
        assert options.date_end == "2024-12-31"
    
    def test_valid_date_range(self):
        """Test that both date_start and date_end can be set together"""
        options = SerpRequestOptions(
            date_start="2024-01-01",
            date_end="2024-12-31"
        )
        assert options.date_start == "2024-01-01"
        assert options.date_end == "2024-12-31"
    
    def test_invalid_date_start_format_slash(self):
        """Test that date_start with slash format is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(date_start="01/01/2024")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_invalid_date_start_format_dots(self):
        """Test that date_start with dots format is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(date_start="2024.01.01")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_invalid_date_end_format(self):
        """Test that invalid date_end format is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(date_end="12/31/2024")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_invalid_date_format_no_leading_zeros(self):
        """Test that dates without leading zeros are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(date_start="2024-1-1")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_invalid_date_format_short_year(self):
        """Test that dates with 2-digit year are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SerpRequestOptions(date_start="24-01-01")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_none_values_accepted(self):
        """Test that None values are accepted for optional fields"""
        options = SerpRequestOptions()
        assert options.time_range is None
        assert options.date_start is None
        assert options.date_end is None
    
    def test_combining_time_range_and_dates(self):
        """Test that time_range and date_start/date_end can coexist"""
        options = SerpRequestOptions(
            time_range=TimeRange.WEEK,
            date_start="2024-01-01",
            date_end="2024-12-31"
        )
        assert options.time_range == TimeRange.WEEK
        assert options.date_start == "2024-01-01"
        assert options.date_end == "2024-12-31"
    
    def test_all_options_together(self):
        """Test that all options can be set together"""
        options = SerpRequestOptions(
            lang="en",
            country="us",
            location="New York",
            google_domain="google.com",
            time_range=TimeRange.DAY,
            date_start="2024-01-01",
            date_end="2024-12-31",
            extra_options={"custom": "value"}
        )
        assert options.lang == "en"
        assert options.country == "us"
        assert options.location == "New York"
        assert options.google_domain == "google.com"
        assert options.time_range == TimeRange.DAY
        assert options.date_start == "2024-01-01"
        assert options.date_end == "2024-12-31"
        assert options.extra_options == {"custom": "value"}
    
    def test_only_date_start(self):
        """Test that only date_start can be set without date_end"""
        options = SerpRequestOptions(date_start="2024-01-01")
        assert options.date_start == "2024-01-01"
        assert options.date_end is None
    
    def test_only_date_end(self):
        """Test that only date_end can be set without date_start"""
        options = SerpRequestOptions(date_end="2024-12-31")
        assert options.date_start is None
        assert options.date_end == "2024-12-31"
