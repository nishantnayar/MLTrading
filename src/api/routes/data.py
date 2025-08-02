"""
Data extraction API routes for ML Trading System.
Provides reusable endpoints for accessing market data, stock information, and other data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

# Add the project root to Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage.database import get_db_manager
from src.api.schemas.data import (
    MarketDataRequest, MarketDataResponse, StockInfoRequest, StockInfoResponse,
    SymbolsRequest, SymbolsResponse, DateRangeRequest, DateRangeResponse,
    SectorRequest, IndustryRequest, SectorsResponse, IndustriesResponse,
    PredictionRequest, PredictionResponse, OrderRequest, OrderResponse,
    ErrorResponse, DataSource
)

# Initialize router
router = APIRouter(prefix="/data", tags=["data"])

# Initialize logger
logger = logging.getLogger(__name__)


def get_db():
    """Dependency to get database manager."""
    return get_db_manager()


@router.get("/health", summary="Data API Health Check")
async def data_health_check():
    """Health check for data API."""
    return {"status": "healthy", "service": "data-api"}


@router.post("/market-data", response_model=List[MarketDataResponse], summary="Get Market Data")
async def get_market_data(
    request: MarketDataRequest,
    db=Depends(get_db)
):
    """
    Get market data for a symbol within a date range.
    
    - **symbol**: Stock symbol (e.g., AAPL, MSFT)
    - **start_date**: Start date for data range
    - **end_date**: End date for data range
    - **source**: Data source (yahoo, alpaca, iex)
    """
    try:
        logger.info(f"Fetching market data for {request.symbol} from {request.start_date} to {request.end_date}")
        
        # Get data from database
        df = db.get_market_data(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            source=request.source.value
        )
        
        if df.empty:
            return []
        
        # Convert DataFrame to list of dictionaries
        data = []
        for _, row in df.iterrows():
            data.append(MarketDataResponse(
                symbol=row['symbol'],
                timestamp=row['timestamp'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                source=row['source']
            ))
        
        logger.info(f"Retrieved {len(data)} market data records for {request.symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")


@router.get("/market-data/{symbol}/latest", response_model=MarketDataResponse, summary="Get Latest Market Data")
async def get_latest_market_data(
    symbol: str,
    source: DataSource = Query(default=DataSource.YAHOO, description="Data source"),
    db=Depends(get_db)
):
    """
    Get the latest market data for a symbol.
    
    - **symbol**: Stock symbol
    - **source**: Data source (yahoo, alpaca, iex)
    """
    try:
        logger.info(f"Fetching latest market data for {symbol}")
        
        data = db.get_latest_market_data(symbol=symbol, source=source.value)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        return MarketDataResponse(
            symbol=data['symbol'],
            timestamp=data['timestamp'],
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=int(data['volume']),
            source=data['source']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest market data: {str(e)}")


@router.post("/stock-info", response_model=StockInfoResponse, summary="Get Stock Information")
async def get_stock_info(
    request: StockInfoRequest,
    db=Depends(get_db)
):
    """
    Get stock information for a symbol.
    
    - **symbol**: Stock symbol
    """
    try:
        logger.info(f"Fetching stock info for {request.symbol}")
        
        data = db.get_stock_info(symbol=request.symbol)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No stock info found for symbol {request.symbol}")
        
        return StockInfoResponse(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock info: {str(e)}")


@router.post("/symbols", response_model=SymbolsResponse, summary="Get Available Symbols")
async def get_symbols(
    request: SymbolsRequest,
    db=Depends(get_db)
):
    """
    Get list of available symbols with market data.
    
    - **source**: Data source (yahoo, alpaca, iex)
    """
    try:
        logger.info(f"Fetching symbols for source {request.source.value}")
        
        symbols = db.get_symbols_with_data(source=request.source.value)
        
        return SymbolsResponse(
            symbols=symbols,
            count=len(symbols),
            source=request.source.value
        )
        
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


@router.post("/date-range", response_model=DateRangeResponse, summary="Get Data Date Range")
async def get_date_range(
    request: DateRangeRequest,
    db=Depends(get_db)
):
    """
    Get the date range of available data for a symbol.
    
    - **symbol**: Stock symbol
    - **source**: Data source (yahoo, alpaca, iex)
    """
    try:
        logger.info(f"Fetching date range for {request.symbol}")
        
        start_date, end_date = db.get_data_date_range(
            symbol=request.symbol,
            source=request.source.value
        )
        
        has_data = start_date is not None and end_date is not None
        
        return DateRangeResponse(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            source=request.source.value,
            has_data=has_data
        )
        
    except Exception as e:
        logger.error(f"Error fetching date range: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch date range: {str(e)}")


@router.post("/sectors", response_model=SectorsResponse, summary="Get All Sectors")
async def get_sectors(db=Depends(get_db)):
    """
    Get all available sectors.
    """
    try:
        logger.info("Fetching all sectors")
        
        sectors = db.get_all_sectors()
        
        return SectorsResponse(
            sectors=sectors,
            count=len(sectors)
        )
        
    except Exception as e:
        logger.error(f"Error fetching sectors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sectors: {str(e)}")


@router.post("/industries", response_model=IndustriesResponse, summary="Get All Industries")
async def get_industries(db=Depends(get_db)):
    """
    Get all available industries.
    """
    try:
        logger.info("Fetching all industries")
        
        industries = db.get_all_industries()
        
        return IndustriesResponse(
            industries=industries,
            count=len(industries)
        )
        
    except Exception as e:
        logger.error(f"Error fetching industries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch industries: {str(e)}")


@router.post("/sectors/{sector}/stocks", response_model=List[str], summary="Get Stocks by Sector")
async def get_stocks_by_sector(
    sector: str,
    db=Depends(get_db)
):
    """
    Get all symbols in a specific sector.
    
    - **sector**: Sector name
    """
    try:
        logger.info(f"Fetching stocks for sector: {sector}")
        
        symbols = db.get_stocks_by_sector(sector=sector)
        
        return symbols
        
    except Exception as e:
        logger.error(f"Error fetching stocks by sector: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stocks by sector: {str(e)}")


@router.post("/industries/{industry}/stocks", response_model=List[str], summary="Get Stocks by Industry")
async def get_stocks_by_industry(
    industry: str,
    db=Depends(get_db)
):
    """
    Get all symbols in a specific industry.
    
    - **industry**: Industry name
    """
    try:
        logger.info(f"Fetching stocks for industry: {industry}")
        
        symbols = db.get_stocks_by_industry(industry=industry)
        
        return symbols
        
    except Exception as e:
        logger.error(f"Error fetching stocks by industry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stocks by industry: {str(e)}")


@router.get("/predictions/{symbol}", response_model=List[PredictionResponse], summary="Get Model Predictions")
async def get_predictions(
    symbol: str,
    model_id: Optional[int] = Query(None, description="Model ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db=Depends(get_db)
):
    """
    Get model predictions for a symbol.
    
    - **symbol**: Stock symbol
    - **model_id**: Optional model ID filter
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    try:
        logger.info(f"Fetching predictions for {symbol}")
        
        # This would need to be implemented in the database manager
        # For now, return empty list as placeholder
        logger.warning("Predictions endpoint not yet implemented in database manager")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions: {str(e)}")


@router.get("/orders", response_model=List[OrderResponse], summary="Get Orders")
async def get_orders(
    symbol: Optional[str] = Query(None, description="Stock symbol"),
    status: Optional[str] = Query(None, description="Order status"),
    strategy_name: Optional[str] = Query(None, description="Strategy name"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db=Depends(get_db)
):
    """
    Get orders with optional filters.
    
    - **symbol**: Optional stock symbol filter
    - **status**: Optional order status filter
    - **strategy_name**: Optional strategy name filter
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    try:
        logger.info("Fetching orders with filters")
        
        # This would need to be implemented in the database manager
        # For now, return empty list as placeholder
        logger.warning("Orders endpoint not yet implemented in database manager")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/data-summary", summary="Get Data Summary")
async def get_data_summary(db=Depends(get_db)):
    """
    Get a summary of available data in the system.
    """
    try:
        logger.info("Fetching data summary")
        
        # Get basic statistics
        symbols = db.get_symbols_with_data()
        sectors = db.get_all_sectors()
        industries = db.get_all_industries()
        
        summary = {
            "total_symbols": len(symbols),
            "total_sectors": len(sectors),
            "total_industries": len(industries),
            "sectors": sectors,
            "industries": industries[:10],  # Show first 10 industries
            "sample_symbols": symbols[:10] if symbols else []  # Show first 10 symbols
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching data summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data summary: {str(e)}") 