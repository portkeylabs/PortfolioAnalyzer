import sys
import pandas as pd
from data_processor import DataProcessor
from portfolio_analyzer import PortfolioAnalyzer
from stock_data import StockDataFetcher

def main():
    if len(sys.argv) < 2:
        print("Usage: python portfolio_cli.py <transactions.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Process the CSV file
    processor = DataProcessor()
    try:
        with open(csv_path, "rb") as f:
            transactions_df = processor.process_csv(f)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)

    if transactions_df.empty:
        print("No valid transactions found in the uploaded file.")
        sys.exit(1)

    print("\n=== Transaction Data Preview ===")
    print(transactions_df.head(10).to_string(index=False))
    print(f"\nTotal transactions loaded: {len(transactions_df)}")

    # Create the StockDataFetcher instance
    stock_fetcher = StockDataFetcher()

    # Analyze the portfolio
    analyzer = PortfolioAnalyzer(transactions_df, stock_fetcher=stock_fetcher)

    print("\n=== Portfolio Summary (No Current Prices) ===")
    summary = analyzer.calculate_portfolio_summary_without_prices()
    for k, v in summary.items():
        print(f"{k.replace('_', ' ').title()}: {v}")

    print("\n=== Holdings (No Current Prices) ===")
    holdings = analyzer.calculate_current_holdings_without_prices()
    if not holdings.empty:
        print(holdings.to_string(index=False))
    else:
        print("No holdings found.")

    # Portfolio summary with current prices
    print("\n=== Portfolio Summary (With Current Prices) ===")
    unique_symbols = analyzer.get_unique_symbols()
    current_prices = stock_fetcher.get_current_prices(unique_symbols)
    summary_with_prices = analyzer.calculate_portfolio_summary(current_prices)
    for k, v in summary_with_prices.items():
        print(f"{k.replace('_', ' ').title()}: {v}")

    print("\n=== Holdings (With Current Prices) ===")
    holdings_with_prices = analyzer.calculate_current_holdings()
    if not holdings_with_prices.empty:
        print(holdings_with_prices.to_string(index=False))
    else:
        print("No holdings found.")

    print("\n=== Dividend Summary ===")
    dividend_summary = analyzer.calculate_dividend_summary()
    print(f"Total Dividends: {dividend_summary['total_dividends']}")
    print(f"Dividend Count: {dividend_summary['dividend_count']}")
    if not dividend_summary['dividend_history'].empty:
        print(dividend_summary['dividend_history'].to_string(index=False))
    else:
        print("No dividend history found.")

if __name__ == "__main__":
    main()