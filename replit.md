# Stock Portfolio Analyzer

## Overview

This is a Streamlit-based web application for analyzing stock portfolios using transaction data from Google Sheets. The application provides comprehensive portfolio analysis including current holdings, performance metrics, and interactive visualizations.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit web interface for user interaction and data visualization
- **Data Processing**: CSV file processing and validation layer
- **Portfolio Analysis**: Core business logic for calculating portfolio metrics
- **Data Fetching**: External API integration for real-time stock prices
- **Visualization**: Interactive charting and reporting components

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Entry point and UI orchestration
- **Technology**: Streamlit framework
- **Responsibilities**: File upload handling, UI layout, workflow coordination

### 2. Data Processor (`data_processor.py`)
- **Purpose**: CSV file processing and data validation
- **Responsibilities**: File parsing, data cleaning, format validation
- **Features**: Multiple encoding support, required column validation

### 3. Portfolio Analyzer (`portfolio_analyzer.py`)
- **Purpose**: Core portfolio calculation engine
- **Responsibilities**: Holdings calculation, performance metrics, profit/loss analysis
- **Key Functions**: Current position tracking, average cost calculation, performance metrics

### 4. Stock Data Fetcher (`stock_data.py`)
- **Purpose**: External stock price data integration
- **Technology**: Yahoo Finance API (yfinance)
- **Features**: Price caching (5-minute duration), batch fetching, error handling

### 5. Portfolio Visualizer (`visualizations.py`)
- **Purpose**: Interactive data visualization
- **Technology**: Plotly for interactive charts
- **Features**: Performance charts, portfolio composition, time-series analysis

## Data Flow

1. **Data Input**: User uploads CSV file through Streamlit interface
2. **Data Processing**: DataProcessor validates and cleans transaction data
3. **Price Fetching**: StockDataFetcher retrieves current market prices
4. **Analysis**: PortfolioAnalyzer calculates holdings and performance metrics
5. **Visualization**: PortfolioVisualizer generates interactive charts
6. **Output**: Results displayed in Streamlit web interface

## External Dependencies

### Core Framework
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

### Data Visualization
- **Plotly**: Interactive charting library
- **Plotly Express**: Simplified plotting interface

### Data Sources
- **yfinance**: Yahoo Finance API for stock prices
- **CSV files**: Transaction data from Google Sheets exports

### Utilities
- **datetime**: Date and time handling
- **io**: File input/output operations

## Deployment Strategy

The application is designed for cloud deployment on Replit with:

- **Web Interface**: Streamlit app accessible via web browser
- **File Upload**: Direct CSV file upload through web interface
- **Real-time Data**: Live stock price fetching from Yahoo Finance
- **Caching Strategy**: 5-minute cache for stock prices to optimize API usage

### Key Architectural Decisions

1. **Modular Design**: Separated concerns into distinct classes for maintainability
2. **Streamlit Choice**: Selected for rapid development and built-in web interface
3. **Yahoo Finance Integration**: Chosen for free, reliable stock price data
4. **Caching Implementation**: Added to reduce API calls and improve performance
5. **Plotly Visualization**: Selected for interactive, professional charts

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 01, 2025. Initial setup