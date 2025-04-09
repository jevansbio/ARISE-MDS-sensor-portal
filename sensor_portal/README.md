# Sensor Portal Backend

## Core Components

### Data Models (`data_models/`)
- **Device**: Represents physical sensor devices
- **Deployment**: Tracks device deployments at specific locations
- **DataFile**: Manages sensor data files (audio, readings)
- **Project**: Organizes deployments into projects
- **Site**: Geographic locations for deployments
- **QualityCheck**: Tracks data quality assessments

### User Management (`user_management/`)
- Custom user model with extended fields
- JWT-based authentication system
- Role-based access control (RBAC)
- Permission management with Bridgekeeper
- User profile and preferences

### Data Handlers (`data_handlers/`)
- Audio file processing and analysis
- Sensor data parsing and validation
- Quality assessment algorithms
- File format conversion utilities
- Metadata extraction

### Quality Checking and Observations

#### Audio Quality Assessment
The system performs comprehensive audio quality checks using the `AudioQualityChecker` service:

1. **Technical Metrics**:
   - Signal-to-Noise Ratio (SNR): Calculated as `20 * log10(signal_peak / noise_floor)`
   - Clipping detection: Ratio of samples exceeding 0.99 amplitude
   - DC offset analysis: Mean value of audio signal
   - Sample rate validation: Verification against expected rate
   - File duration verification: Actual vs expected duration

2. **Content Analysis**:
   - Silence ratio calculation: Percentage of frames below RMS threshold
   - Audio segment detection: Number of distinct audio events
   - Spectral analysis:
     - Centroid: Mean frequency weighted by magnitude
     - Bandwidth: Spread of frequencies around centroid
     - Rolloff: Frequency below which 85% of energy is contained
   - Zero crossing rate: Measure of signal noisiness
   - Temporal evolution tracking: RMS energy over time

3. **Quality Scoring**:
   The quality score (0-100) is calculated with automatic deductions:

   ```python
   quality_score = 100.0  # Start with perfect score
   
   # Technical deductions
   if clipping_ratio > 0.01:  # More than 1% clipping
       quality_score -= 20
   if abs(dc_offset) > 0.1:  # Significant DC offset
       quality_score -= 15
   if snr < 20:  # Poor signal-to-noise ratio
       quality_score -= max(0, min(25, (20 - snr)))
   
   # Content-based deductions
   if silence_ratio > 0.8:  # More than 80% silence
       quality_score -= 40
   elif silence_ratio > 0.5:  # More than 50% silence
       quality_score -= 20
   elif silence_ratio > 0.3:  # More than 30% silence
       quality_score -= 10
   
   if num_segments < 2 and duration > 5:  # No significant events
       quality_score -= 30
   
   if zcr_mean > 0.4:  # Very noisy signal
       quality_score -= 15
   ```

4. **Quality Check States**:
   - `pending`: Initial state
   - `in_progress`: Check running
   - `completed`: Check finished
   - `failed`: Error occurred

#### Observation System
The system supports detailed observations through:

1. **Automatic Observations**:
   - Spectral content analysis:
     - High frequency content: `cent_mean > 2000`
     - Low frequency content: `cent_mean < 500`
     - Rich spectral content: `band_mean > 2000`
     - Limited spectral content: `band_mean < 500`
   - Audio event detection: Number of segments
   - Silence pattern analysis: Silence ratio
   - Frequency distribution: Spectral characteristics

2. **Quality Issues**:
   - Technical problems:
     - Clipping: `clipping_ratio > 0.01`
     - DC offset: `abs(dc_offset) > 0.1`
     - Noise: `snr < 20` or `zcr_mean > 0.4`
   - Content issues:
     - Excessive silence: `silence_ratio > 0.8`
     - Missing events: `num_segments < 2` for long recordings
   - Format problems: Invalid sample rate or duration
   - Metadata inconsistencies: Missing or invalid metadata

3. **Observation Applications**:
   - **Audio Analysis**:
     - Detect recording environment (indoor/outdoor) based on spectral characteristics
     - Identify potential equipment issues (e.g., microphone problems)
     - Monitor recording conditions over time
     - Track audio event patterns in long recordings
   
   - **Quality Monitoring**:
     - Batch quality assessment of multiple files
     - Trend analysis of recording quality
     - Automated quality alerts
     - Quality score distribution analysis
   
   - **Data Validation**:
     - Verify recording completeness
     - Check for consistent audio levels
     - Validate metadata accuracy
     - Detect corrupted or incomplete files
   
   - **Research Applications**:
     - Study acoustic patterns
     - Analyze environmental changes
     - Track temporal variations
     - Compare different recording setups

4. **API Endpoints**:
   ```python
   # Check quality for a file
   POST /api/datafiles/{id}/check_quality/
   
   # Get quality status
   GET /api/datafiles/{id}/quality_status/
   
   # Get temporal evolution data
   GET /api/datafiles/{id}/temporal_data/
   
   # Get spectral analysis
   GET /api/datafiles/{id}/spectral_analysis/
   
   # Batch quality check
   POST /api/datafiles/batch_quality_check/
   ```

5. **Quality Metrics Storage**:
   - Quality score: Final calculated score (0-100)
   - Issue list: JSON array of detected problems
   - Check timestamp: When the check was performed
   - Temporal evolution data:
     ```python
     {
         'times': [float],  # Time points
         'rms_energy': [float],  # RMS energy over time
         'spectral_centroid': [float],  # Frequency centroid over time
         'zero_crossing_rate': [float]  # ZCR over time
     }
     ```
   - Spectral analysis results:
     ```python
     {
         'cent_mean': float,  # Mean spectral centroid
         'band_mean': float,  # Mean spectral bandwidth
         'rolloff_mean': float  # Mean spectral rolloff
     }
     ```

6. **Visualization Tools**:
   - Temporal evolution plots
   - Spectral analysis graphs
   - Quality score distributions
   - Issue type frequency charts
   - Recording environment classification
   - Audio event timeline visualization

7. **Export Capabilities**:
   - Quality reports in CSV/JSON format
   - Spectral analysis data export
   - Temporal evolution data export
   - Batch quality assessment results
   - Custom observation reports

#### Customizing Quality Checks and Observations

1. **Configuration Location**:
   The quality check criteria are defined in `sensor_portal/data_models/services/audio_quality.py`:
   ```python
   class AudioQualityChecker:
       # Thresholds for quality assessment
       CLIPPING_THRESHOLD = 0.01  # 1% clipping allowed
       DC_OFFSET_THRESHOLD = 0.1  # Maximum allowed DC offset
       SNR_THRESHOLD = 20  # Minimum acceptable SNR in dB
       SILENCE_THRESHOLD = 0.3  # Warning threshold for silence ratio
       ZCR_NOISE_THRESHOLD = 0.4  # Maximum allowed zero crossing rate
   ```

2. **Modifying Quality Score Deductions**:
   To adjust the scoring system, modify the deduction rules in the `check_audio_quality` method:
   ```python
   # Technical deductions
   if clipping_ratio > CLIPPING_THRESHOLD:
       quality_score -= 20  # Adjust deduction value
   
   # Content-based deductions
   if silence_ratio > 0.8:
       quality_score -= 40  # Adjust deduction value
   ```

3. **Adding New Observations**:
   To add new observation criteria, extend the `check_audio_quality` method:
   ```python
   # Example: Add new spectral observation
   if spectral_flatness > 0.8:
       observations.append("High spectral flatness detected")
   ```

4. **Custom Quality Checks**:
   Create a new method in `AudioQualityChecker` for custom checks:
   ```python
   @staticmethod
   def custom_quality_check(file_path, custom_thresholds):
       # Implement custom quality checks
       pass
   ```

5. **Configuration via Settings**:
   Add custom thresholds to Django settings:
   ```python
   # settings.py
   QUALITY_CHECK_THRESHOLDS = {
       'clipping': 0.01,
       'dc_offset': 0.1,
       'snr': 20,
       'silence': 0.3,
       'zcr': 0.4
   }
   ```

6. **Dynamic Threshold Adjustment**:
   Implement dynamic thresholds based on recording conditions:
   ```python
   def adjust_thresholds(recording_conditions):
       # Adjust thresholds based on recording environment
       pass
   ```

7. **Adding New Metrics**:
   To add new quality metrics:
   1. Add new fields to the `DataFile` model
   2. Update the quality check service
   3. Modify the serializer to include new metrics
   4. Update the API endpoints

8. **Testing Changes**:
   After modifying criteria:
   ```bash
   # Run quality check tests
   pytest data_models/tests/test_audio_quality.py
   
   # Validate changes with sample files
   python manage.py test_quality_criteria
   ```

9. **Version Control**:
   - Track changes to quality criteria
   - Document threshold modifications
   - Maintain backward compatibility
   - Update documentation

10. **Monitoring Impact**:
    - Track quality score distributions
    - Monitor false positive/negative rates
    - Analyze impact on data validation
    - Adjust thresholds based on results

### API Layer (`api/`)
- RESTful endpoints for all models
- GIS-enabled endpoints for spatial queries
- File upload/download endpoints
- Bulk operations support
- Custom pagination and filtering

## Technical Stack

### Core Dependencies
- Django 4.2
- Django REST Framework
- Django REST Framework GIS
- PostgreSQL with PostGIS
- Redis
- Celery

### Key Features
- **Authentication**
  - JWT token-based authentication
  - Token refresh mechanism
  - Session-based authentication for admin
  - Custom permission rules

- **Data Processing**
  - Asynchronous task processing with Celery
  - Background file processing
  - Quality assessment automation
  - Data validation and cleaning

- **Storage**
  - File storage abstraction layer
  - Support for multiple storage backends
  - Metadata management
  - File versioning

- **API Features**
  - Swagger/OpenAPI documentation
  - Custom pagination
  - Advanced filtering
  - Bulk operations
  - GIS query support

## Development Setup

### Environment Variables
```bash
# Database
POSTGRES_NAME=sensor_portal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Security
DJANGO_SECRET_KEY=your_secret_key
FIELD_ENCRYPTION_KEY=your_encryption_key

# Redis/Celery
CELERY_BROKER=redis://redis:6379/0
```

### Database Setup
```bash
# Create database extensions
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest data_models/tests/test_models.py

# Run with coverage
pytest --cov=sensor_portal
```

## API Documentation

### Authentication
```python
# JWT Token Authentication
headers = {
    'Authorization': 'Bearer your_jwt_token'
}

# Token Refresh
POST /api/token/refresh/
{
    "refresh": "your_refresh_token"
}
```

### Common Endpoints
```python
# Devices
GET /api/devices/
POST /api/devices/
GET /api/devices/{id}/

# Deployments
GET /api/deployments/
POST /api/deployments/
GET /api/deployments/{id}/

# Data Files
GET /api/datafiles/
POST /api/datafiles/
GET /api/datafiles/{id}/
```

## Background Tasks

### Celery Configuration
```python
# settings.py
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_DEFAULT_QUEUE = 'main_worker'
```

### Common Tasks
- File processing and validation
- Quality assessment
- Metadata extraction
- Data archiving
- Report generation

## Security Features

- JWT token authentication
- Role-based access control
- Field-level encryption
- CORS protection
- CSRF protection
- Rate limiting
- Input validation
- SQL injection protection

## Performance Optimization

- Redis caching
- Database indexing
- Query optimization
- Bulk operations
- Asynchronous processing
- File streaming
- Pagination
- Compression

## Monitoring and Logging

- Django debug toolbar
- Celery task monitoring
- Error tracking
- Performance metrics
- Audit logging
- User activity tracking
