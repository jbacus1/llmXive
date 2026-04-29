# API Reference

## External API Integrations

### OpenWeatherMap API

**Base URL**: `https://api.openweathermap.org/data/2.5/`

**Authentication**: API key via query parameter `appid`

**Endpoints Used**:
- `/weather` - Current weather data
- `/forecast` - Weather forecast data
- `/climate` - Historical climate data

**Rate Limits**:
- Free tier: 60 calls/minute
- Cache responses for 1 hour

**Error Handling**:
- 401: Invalid API key
- 404: Location not found
- 429: Rate limit exceeded

### USGS EarthExplorer API

**Base URL**: `https://earthexplorer.usgs.gov/`

**Authentication**: API key via header

**Endpoints Used**:
- `/datasets` - Available datasets
- `/download` - Data download requests
- `/scene` - Scene search and metadata

**Rate Limits**:
- 100 requests/hour
- Implement exponential backoff for retries

**Data Formats**:
- GeoTIFF for raster data
- JSON for metadata

## Internal APIs

### Validation API

**Module**: `src.cli.validate.py`

**Functions**:
- `validate_api_keys()` - Check all required API keys
- `validate_disk_space(min_gb=10)` - Verify available storage
- `validate_file_paths()` - Check required files exist

### Configuration API

**Module**: `src/config/constants.py`

**Constants**:
- `CACHE_DIR` - Cache storage location
- `DATA_DIR` - Data storage location
- `API_TIMEOUT` - Request timeout in seconds

### Cache API

**Module**: `src/data/cache.py`

**Functions**:
- `get(key)` - Retrieve cached value
- `set(key, value, ttl)` - Store value with TTL
- `invalidate(pattern)` - Clear cache entries

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| E001 | API key missing | Set environment variable |
| E002 | Insufficient disk space | Free up space |
| E003 | Schema validation failed | Check input data format |
| E004 | Rate limit exceeded | Wait and retry |
| E005 | Cache error | Clear cache and retry |
