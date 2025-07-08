import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io
import sys
import traceback

from portfolio_analyzer import PortfolioAnalyzer
from data_processor import DataProcessor
from stock_data import StockDataFetcher


def main():
    st.set_page_config(page_title="Stock Portfolio Analyzer",
                       page_icon="📈",
                       layout="wide",
                       initial_sidebar_state="expanded")

    st.title("📈 Stock Portfolio Analyzer")
    st.markdown(
        "Upload your Google Sheets transaction data and get comprehensive portfolio analysis"
    )

    # Sidebar for file upload and controls
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload CSV file from Google Sheets",
            type=['csv'],
            help=
            "Upload your transaction data in CSV format exported from Google Sheets"
        )

        if uploaded_file:
            st.success("✅ File uploaded successfully!")

    # Main content area
    if uploaded_file is not None:
        try:
            # Process the uploaded data
            with st.spinner("Processing transaction data..."):
                processor = DataProcessor()
                transactions_df = processor.process_csv(uploaded_file)

            if transactions_df.empty:
                st.error("❌ No valid transactions found in the uploaded file")
                st.info(
                    "Please ensure your CSV has columns: Date, Symbol, Action, Quantity, Price"
                )
                return

            # Display data preview
            with st.expander("📋 Transaction Data Preview", expanded=False):
                st.dataframe(transactions_df, use_container_width=True)
                st.info(f"Total transactions loaded: {len(transactions_df)}")

            # Initialize components
            stock_fetcher = StockDataFetcher()
            analyzer = PortfolioAnalyzer(transactions_df, stock_fetcher)

            # Calculate portfolio metrics (without current prices)
            with st.spinner("Calculating portfolio metrics..."):
                try:
                    portfolio_summary = analyzer.calculate_portfolio_summary_without_prices(
                    )
                    holdings = analyzer.calculate_current_holdings_without_prices(
                    )
                    performance_data = analyzer.calculate_performance_over_time_without_prices(
                    )
                    dividend_summary = analyzer.calculate_dividend_summary()

                except Exception as e:
                    import traceback
                    st.error(f"Error processing portfolio data: {str(e)}")
                    st.write("DEBUG - Error details:", str(e))
                    st.code(traceback.format_exc())
                    return

            # Display main metrics
            st.header("📊 Portfolio Overview")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Invested",
                          f"${portfolio_summary['total_invested']:,.2f}",
                          help="Total amount invested across all positions")

            with col2:
                st.metric(
                    "Current Value",
                    f"${portfolio_summary['current_value']:,.2f}",
                    help="Current portfolio value based on transaction data")

            with col3:
                # Calculate return percentage using realized gains since no current prices
                return_pct = 0.0
                if portfolio_summary['total_invested'] > 0:
                    return_pct = (portfolio_summary['realized_gain_loss'] /
                                  portfolio_summary['total_invested']) * 100
                st.metric(
                    "Total Return",
                    f"{return_pct:+.2f}%",
                    delta=f"${portfolio_summary['realized_gain_loss']:,.2f}",
                    help="Return percentage based on realized gains/losses")

            with col4:
                st.metric("Dividend Income",
                          f"${dividend_summary['total_dividends']:,.2f}",
                          help="Total dividend income received")

        except Exception as e:
            import traceback
            st.error(f"❌ Error processing portfolio data: {str(e)}")
            st.error("Please check your data format and try again.")

            # Show detailed error in expander for debugging
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

    else:
        # Welcome screen
        st.info(
            "👆 Please upload your transaction data CSV file using the sidebar to get started"
        )

        st.markdown("### 📋 Required CSV Format")
        st.markdown("""
        Your CSV file should contain the following columns:
        - **TextDate**: Transaction date in text format
        - **Summary**: Transaction description (Client Consideration, Dividend, etc.)
        - **MarketName**: Stock ticker symbol (e.g., AAPL, GOOGL)
        - **ProfitAndLoss**: Profit/Loss amount
        - **Transaction type**: DEPO (money in) or WITH (money out)
        - **Currency**: Transaction currency
        - **PL Amount**: Transaction amount value
        - **DateUtc**: UTC date and time
        - **OpenDateUtc**: UTC date and time when executed
        """)

        # Sample data format
        sample_data = pd.DataFrame({
            'TextDate': ['2024-01-15', '2024-02-01', '2024-03-01'],
            'Summary':
            ['Client Consideration', 'Client Consideration', 'Dividend'],
            'MarketName': ['AAPL', 'GOOGL', 'AAPL'],
            'ProfitAndLoss': [-1500.00, -14000.00, 25.00],
            'Transaction type': ['WITH', 'WITH', 'DEPO'],
            'Currency': ['USD', 'USD', 'USD'],
            'PL Amount': [-1500.00, -14000.00, 25.00],
            'DateUtc': [
                '2024-01-15T10:30:00Z', '2024-02-01T14:20:00Z',
                '2024-03-01T09:15:00Z'
            ],
            'OpenDateUtc': [
                '2024-01-15T10:30:00Z', '2024-02-01T14:20:00Z',
                '2024-03-01T09:15:00Z'
            ]
        })

        st.markdown("### 📊 Sample Data Format")
        st.dataframe(sample_data, use_container_width=True)


if __name__ == "__main__":
    main()
