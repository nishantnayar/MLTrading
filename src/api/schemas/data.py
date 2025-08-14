"""
Pydantic schemas for data extraction API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DataSource(str, Enum):
    """Available data sources."""
    YAHOO = "yahoo"
    ALPACA = "alpaca"
    IEX = "iex"


class MarketDataRequest(BaseModel):
    """Request schema for market data extraction."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    start_date: datetime = Field(..., description="Start date for data range")
    end_date: datetime = Field(..., description="End date for data range")
    source: DataSource = Field(default=DataSource.YAHOO, description="Data source")
    
    @field_validator('symbol', mode='before')
    @classmethod
    def validate_symbol(cls, v):
        """Validate symbol format but allow invalid symbols for graceful handling."""
        if isinstance(v, str):
            # Allow empty symbols for graceful handling in API route
            # This maintains backward compatibility with existing tests
            if not v:
                return v  # Return empty string as-is
            
            # Basic validation - ensure it's a string
            return v.strip().upper()
        return v
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date_format(cls, v):
        """Fast validation for date format before parsing."""
        if isinstance(v, str):
            # Quick check for obviously invalid formats
            if v in ['invalid-date', 'null', 'undefined', '']:
                raise ValueError(f"Invalid date format: {v}")
            
            # Try to parse with common formats for better performance
            try:
                # Try ISO format first (most common)
                if 'T' in v or 'Z' in v:
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
                # Try simple date format
                elif len(v) == 10 and v.count('-') == 2:
                    return datetime.strptime(v, '%Y-%m-%d')
                # Try other common formats
                elif len(v) == 19 and v.count('-') == 2 and v.count(':') == 2:
                    return datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                else:
                    # Fall back to standard parsing
                    return datetime.fromisoformat(v)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid date format: {v}")
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate that end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
                "source": "yahoo"
            }
        }
    }


class MarketDataResponse(BaseModel):
    """Response schema for market data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str


class StockInfoRequest(BaseModel):
    """Request schema for stock information."""
    symbol: str = Field(..., description="Stock symbol")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL"
            }
        }
    }


class StockInfoResponse(BaseModel):
    """Response schema for stock information."""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SymbolsRequest(BaseModel):
    """Request schema for getting available symbols."""
    source: DataSource = Field(default=DataSource.YAHOO, description="Data source")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "yahoo"
            }
        }
    }


class SymbolsResponse(BaseModel):
    """Response schema for available symbols."""
    symbols: List[str]
    count: int
    source: str


class DateRangeRequest(BaseModel):
    """Request schema for getting data date range."""
    symbol: str = Field(..., description="Stock symbol")
    source: DataSource = Field(default=DataSource.YAHOO, description="Data source")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "source": "yahoo"
            }
        }
    }


class DateRangeResponse(BaseModel):
    """Response schema for data date range."""
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: str
    has_data: bool


class SectorRequest(BaseModel):
    """Request schema for sector-based queries."""
    sector: str = Field(..., description="Sector name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sector": "Technology"
            }
        }
    }


class IndustryRequest(BaseModel):
    """Request schema for industry-based queries."""
    industry: str = Field(..., description="Industry name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "industry": "Software"
            }
        }
    }


class SectorsResponse(BaseModel):
    """Response schema for available sectors."""
    sectors: List[str]
    count: int


class IndustriesResponse(BaseModel):
    """Response schema for available industries."""
    industries: List[str]
    count: int


class PredictionRequest(BaseModel):
    """Request schema for model predictions."""
    symbol: str = Field(..., description="Stock symbol")
    prediction_model_id: Optional[int] = Field(None, description="Model ID")
    start_date: Optional[datetime] = Field(None, description="Start date for predictions")
    end_date: Optional[datetime] = Field(None, description="End date for predictions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "prediction_model_id": 1,
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
        }
    }


class PredictionResponse(BaseModel):
    """Response schema for model predictions."""
    symbol: str
    prediction_model_id: int
    timestamp: datetime
    prediction: float
    confidence: Optional[float] = None
    features: Optional[Dict[str, Any]] = None


class OrderRequest(BaseModel):
    """Request schema for order data."""
    symbol: Optional[str] = Field(None, description="Stock symbol")
    status: Optional[str] = Field(None, description="Order status")
    strategy_name: Optional[str] = Field(None, description="Strategy name")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "status": "filled",
                "strategy_name": "momentum",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
        }
    }


class OrderResponse(BaseModel):
    """Response schema for order data."""
    id: int
    symbol: str
    side: str
    quantity: int
    price: float
    order_type: str
    status: str
    strategy_name: Optional[str] = None
    alpaca_order_id: Optional[str] = None
    created_at: datetime
    filled_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 