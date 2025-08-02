# ML Trading Data API Documentation

## Overview

The ML Trading System provides a comprehensive FastAPI-based data extraction API that enables reusable access to market data, stock information, and other trading-related data across different parts of the application.

## Architecture Benefits

### Why Use APIs for Data Extraction?

1. **Reusability**: The same data endpoints can be used by:
   - Dashboard components
   - Trading strategies
   - Data analysis scripts
   - External integrations
   - Mobile applications

2. **Consistency**: All data access goes through the same validated endpoints with consistent error handling and response formats.

3. **Scalability**: The API layer can be scaled independently of the database, and caching can be implemented at the API level.

4. **Type Safety**: Using Pydantic schemas ensures type validation and automatic documentation.

5. **Separation of Concerns**: Data access logic is centralized, making it easier to maintain and modify.

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check
```http
GET /health
GET /data/health
```

### Market Data

#### Get Market Data
```http
POST /data/market-data
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "source": "yahoo"
}
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "timestamp": "2024-01-01T09:30:00Z",
    "open": 150.25,
    "high": 152.10,
    "low": 149.80,
    "close": 151.50,
    "volume": 1000000,
    "source": "yahoo"
  }
]
```

#### Get Latest Market Data
```http
GET /data/market-data/{symbol}/latest?source=yahoo
```

### Stock Information

#### Get Stock Info
```http
POST /data/stock-info
```

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

#### Get Available Symbols
```http
POST /data/symbols
```

**Request Body:**
```json
{
  "source": "yahoo"
}
```

#### Get Data Date Range
```http
POST /data/date-range
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "source": "yahoo"
}
```

### Sector and Industry Data

#### Get All Sectors
```http
POST /data/sectors
```

#### Get All Industries
```http
POST /data/industries
```

#### Get Stocks by Sector
```http
POST /data/sectors/{sector}/stocks
```

#### Get Stocks by Industry
```http
POST /data/industries/{industry}/stocks
```

### Data Summary
```http
GET /data/data-summary
```

## Using the Data Service

The `DataService` class provides a clean interface for consuming the APIs:

```python
from src.api.services.data_service import get_data_service
from datetime import datetime, timedelta

# Initialize service
data_service = get_data_service()

# Get market data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
df = data_service.get_market_data("AAPL", start_date, end_date)

# Get available symbols
symbols = data_service.get_symbols()

# Get stock information
stock_info = data_service.get_stock_info("AAPL")

# Get sectors
sectors = data_service.get_sectors()
```

## Integration Examples

### Dashboard Integration

```python
# In a Dash callback
@app.callback(
    Output('price-chart', 'figure'),
    Input('symbol-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_chart(symbol, start_date, end_date):
    if not symbol:
        return {}
    
    data_service = get_data_service()
    df = data_service.get_market_data(symbol, start_date, end_date)
    
    # Create chart with the data
    fig = px.line(df, x='timestamp', y='close', title=f'{symbol} Price')
    return fig
```

### Trading Strategy Integration

```python
# In a trading strategy
def momentum_strategy(symbol):
    data_service = get_data_service()
    
    # Get recent market data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=20)
    df = data_service.get_market_data(symbol, start_date, end_date)
    
    # Calculate momentum indicators
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    
    # Generate signals
    latest = df.iloc[-1]
    if latest['sma_10'] > latest['sma_20']:
        return "BUY"
    elif latest['sma_10'] < latest['sma_20']:
        return "SELL"
    else:
        return "HOLD"
```

### Data Analysis Script

```python
# In a data analysis script
def analyze_sector_performance(sector):
    data_service = get_data_service()
    
    # Get all stocks in sector
    symbols = data_service.get_stocks_by_sector(sector)
    
    results = []
    for symbol in symbols[:10]:  # Analyze first 10 stocks
        latest = data_service.get_latest_market_data(symbol)
        if latest:
            results.append({
                'symbol': symbol,
                'price': latest['close'],
                'volume': latest['volume']
            })
    
    return pd.DataFrame(results)
```

## Error Handling

The API provides consistent error responses:

```json
{
  "error": "Failed to fetch market data",
  "detail": "Database connection error",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (symbol not found)
- `500`: Internal Server Error

## Running the API

### Start the FastAPI Server

```bash
# From the project root
python src/api/main.py
```

Or using uvicorn directly:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing the API

Run the example script to test the APIs:

```bash
python examples/api_usage_example.py
```

## Performance Considerations

1. **Connection Pooling**: The database manager uses connection pooling for efficient database access.

2. **Caching**: Consider implementing Redis caching for frequently accessed data.

3. **Pagination**: For large datasets, implement pagination in the API responses.

4. **Rate Limiting**: Consider implementing rate limiting for external API consumers.

## Future Enhancements

1. **Authentication**: Add JWT-based authentication for secure API access.

2. **Caching**: Implement Redis caching for frequently accessed data.

3. **Real-time Updates**: Add WebSocket support for real-time data streaming.

4. **Batch Operations**: Add endpoints for batch data retrieval.

5. **Data Validation**: Add more comprehensive data validation and cleaning.

## Dependencies

The API requires the following additional dependencies:
- `requests>=2.31.0` - For the data service HTTP client

These are already included in the `requirements.txt` file. 