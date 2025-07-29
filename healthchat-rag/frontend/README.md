# HealthMate Frontend Dashboard

A modern, responsive web dashboard for health data visualization and analytics built with Streamlit.

## 🚀 Features

### 📊 **Comprehensive Health Analytics**
- Real-time health metrics monitoring
- Advanced trend analysis and predictions
- Interactive data visualizations
- Health score calculations and insights

### 🎨 **Rich Visualizations**
- **Line Charts**: Health trends, medication adherence, health score timeline
- **Pie Charts**: Symptom distribution, data completeness
- **Doughnut Charts**: Data completeness overview
- **Heatmaps**: Correlation matrices between health data types
- **Bar Charts**: Severity distributions, frequency analysis

### 🔐 **Secure Authentication**
- JWT-based authentication
- Session management
- Secure API communication
- Role-based access control

### 📱 **Responsive Design**
- Mobile-friendly interface
- Adaptive layouts
- Touch-optimized controls
- Cross-platform compatibility

### 📤 **Data Export**
- CSV export functionality
- JSON data export
- Chart image downloads
- Report generation

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager
- HealthMate API running (backend)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthchat-rag/frontend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   export HEALTHMATE_API_URL="https://healthmate-production.up.railway.app"
   export STREAMLIT_SERVER_PORT=8501
   export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
   ```

4. **Start the dashboard**
   ```bash
   # Using the startup script
   ./start_dashboard.sh
   
   # Or directly with streamlit
   streamlit run health_dashboard.py
   ```

## 📖 Usage

### 🔐 Authentication
1. Open the dashboard in your browser
2. Enter your HealthMate credentials
3. Click "Login" to access your health data

### 📊 Dashboard Sections

#### **Overview**
- Health score and key metrics
- Recent activity feed
- Health insights and recommendations
- Risk factor alerts

#### **Health Trends**
- Interactive trend charts
- Multi-dimensional analysis
- Trend comparison tools
- Historical data visualization

#### **Analytics**
- Health score breakdown
- Symptom analysis
- Medication adherence tracking
- Predictive analytics

#### **Visualizations**
- Customizable chart types
- Interactive data exploration
- Chart configuration options
- Export capabilities

#### **Data Management**
- Health data records
- Data completeness analysis
- Export functionality
- Data filtering and search

### 🎨 Chart Types

| Chart Type | Description | Use Case |
|------------|-------------|----------|
| Health Trends | Line chart showing health data over time | Monitor vital signs, symptoms, medications |
| Symptom Distribution | Pie chart showing symptom frequency | Analyze symptom patterns and severity |
| Medication Adherence | Line chart showing adherence rates | Track medication compliance |
| Data Completeness | Doughnut chart showing data coverage | Assess data quality and completeness |
| Health Score Timeline | Line chart showing health score trends | Monitor overall health progression |
| Correlation Matrix | Heatmap showing data relationships | Identify correlations between health metrics |

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HEALTHMATE_API_URL` | HealthMate API endpoint | `https://healthmate-production.up.railway.app` |
| `STREAMLIT_SERVER_PORT` | Dashboard port | `8501` |
| `STREAMLIT_SERVER_ADDRESS` | Server address | `0.0.0.0` |
| `API_TIMEOUT` | API request timeout | `30` |
| `SESSION_TIMEOUT` | Session timeout (seconds) | `3600` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `300` |

### Dashboard Configuration

The dashboard configuration is managed in `dashboard_config.py`:

- **Chart Configuration**: Colors, dimensions, and styling
- **Health Score Weights**: Component weights for health score calculation
- **Alert Thresholds**: Thresholds for health alerts and warnings
- **UI Theme**: Color scheme and styling preferences
- **Performance Settings**: Caching and request limits

## 🔧 Development

### Project Structure
```
frontend/
├── health_dashboard.py      # Main dashboard application
├── dashboard_config.py      # Configuration settings
├── requirements.txt         # Python dependencies
├── start_dashboard.sh       # Startup script
└── README.md               # This file
```

### Adding New Features

1. **New Chart Types**
   - Add chart configuration to `dashboard_config.py`
   - Create chart function in `health_dashboard.py`
   - Update visualization section

2. **New API Endpoints**
   - Add API method to `HealthMateDashboard` class
   - Update corresponding dashboard sections
   - Add error handling and loading states

3. **UI Improvements**
   - Modify CSS styles in the main dashboard file
   - Update layout and component structure
   - Add new interactive elements

### Testing

```bash
# Run the dashboard in development mode
streamlit run health_dashboard.py --server.port 8501

# Test with different data periods
# Modify the days_filter parameter in the dashboard
```

## 🚀 Deployment

### Local Development
```bash
cd healthchat-rag/frontend
./start_dashboard.sh
```

### Production Deployment
```bash
# Set production environment variables
export HEALTHMATE_API_URL="https://your-api-url.com"
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"

# Start the dashboard
streamlit run health_dashboard.py \
    --server.port $STREAMLIT_SERVER_PORT \
    --server.address $STREAMLIT_SERVER_ADDRESS \
    --server.headless true
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "health_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📊 API Integration

The dashboard integrates with the HealthMate API endpoints:

- **Authentication**: `/auth/login`
- **Dashboard Data**: `/advanced-analytics/dashboard`
- **Health Data**: `/health-data/`
- **Analytics**: `/analytics/health-score`
- **Visualizations**: `/visualization/chart/{chart_type}`

### API Response Format
```json
{
  "success": true,
  "data": {
    "overview": {
      "health_score": 85.5,
      "total_health_data_points": 150,
      "total_symptoms": 12,
      "medication_adherence_rate": 92.3
    },
    "health_score": { ... },
    "symptom_analysis": { ... },
    "medication_adherence": { ... },
    "recommendations": [ ... ],
    "health_insights": { ... }
  }
}
```

## 🔒 Security

- **JWT Authentication**: Secure token-based authentication
- **HTTPS Communication**: Encrypted API communication
- **Session Management**: Automatic token refresh
- **Input Validation**: Client-side and server-side validation
- **Error Handling**: Secure error messages

## 📈 Performance

- **Caching**: Client-side caching for improved performance
- **Lazy Loading**: Load data on demand
- **Optimized Queries**: Efficient API requests
- **Responsive Design**: Fast loading on all devices

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check API URL configuration
   - Verify credentials
   - Check network connectivity

2. **Charts Not Loading**
   - Verify API endpoints are accessible
   - Check data format compatibility
   - Review browser console for errors

3. **Performance Issues**
   - Reduce data period filter
   - Check API response times
   - Monitor memory usage

### Debug Mode
```bash
# Enable debug logging
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run health_dashboard.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

---

**HealthMate Dashboard** - Empowering health through data visualization and analytics 🏥📊 