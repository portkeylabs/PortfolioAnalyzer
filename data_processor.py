import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Optional
import streamlit as st

class DataProcessor:
    """Handle CSV file processing and data validation"""
    
    def __init__(self):
        self.required_columns = ['TextDate', 'Summary', 'MarketName', 'Transaction type', 'PL Amount']
        self.valid_transaction_types = ['DEPO', 'WITH']
        self.valid_summary_types = ['Client Consideration', 'Share Dealing Commissions', 'Cash Out', 'Cash In', 'Dividend']
    
    def process_csv(self, uploaded_file) -> pd.DataFrame:
        """Process uploaded CSV file and return clean DataFrame"""
        try:
            # Read CSV file
            if uploaded_file is not None:
                # Read the file content
                content = uploaded_file.read()
                
                # Try different encodings
                try:
                    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(io.StringIO(content.decode('latin-1')))
                    except UnicodeDecodeError:
                        df = pd.read_csv(io.StringIO(content.decode('cp1252')))
                
                # Validate and clean the data
                cleaned_df = self._validate_and_clean_data(df)
                return cleaned_df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            return pd.DataFrame()
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean the transaction data"""
        if df.empty:
            raise ValueError("Empty CSV file")
        
        # Check for required columns (case insensitive)
        df_columns = [col.strip() for col in df.columns]
        df.columns = df_columns
        
        missing_columns = []
        for required_col in self.required_columns:
            if required_col not in df_columns:
                # Try to find similar column names
                similar_cols = [col for col in df_columns if required_col.lower() in col.lower()]
                if similar_cols:
                    # Use the first similar column
                    old_col = similar_cols[0]
                    df = df.rename(columns={old_col: required_col})
                else:
                    missing_columns.append(required_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Transform the data to match the expected format
        cleaned_df = self._transform_to_standard_format(df)
        
        # Clean and validate data
        cleaned_df = self._clean_data_types(cleaned_df)
        
        # Validate data
        cleaned_df = self._validate_data_values(cleaned_df)
        
        # Sort by date
        cleaned_df = cleaned_df.sort_values('date').reset_index(drop=True)
        
        return cleaned_df
    
    def _transform_to_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the user's specific format to standard portfolio format"""
        standard_transactions = []
        
        for index, row in df.iterrows():
            try:
                # Strict validation - no null values allowed
                summary = row.get('Summary')
                transaction_type = row.get('Transaction type')
                market_name = row.get('MarketName')
                pl_amount = row.get('PL Amount')
                text_date = row.get('TextDate')
                
                # Check for null values and raise error if found
                if pd.isna(transaction_type) or transaction_type == '':
                    raise ValueError(f"Row {index + 1}: Transaction type column cannot be null or empty")
                if pd.isna(market_name) or market_name == '':
                    raise ValueError(f"Row {index + 1}: MarketName column cannot be null or empty")
                if pd.isna(pl_amount):
                    raise ValueError(f"Row {index + 1}: PL Amount column cannot be null")
                if pd.isna(text_date) or text_date == '':
                    raise ValueError(f"Row {index + 1}: TextDate column cannot be null or empty")
                
                # Convert to proper types with validation
                # Handle empty Summary for WITH transactions (usually commission fees)
                if pd.isna(summary) or summary == '':
                    if transaction_type == 'WITH' and pl_amount is not None and float(pl_amount) < 0:
                        summary = 'Share Dealing Commissions'  # Default for empty WITH transactions
                    else:
                        summary = ''
                else:
                    summary = str(summary).strip()
                
                transaction_type = str(transaction_type).strip()
                market_name = str(market_name).strip()
                text_date = str(text_date).strip()
                
                # Convert PL Amount to float (it should already be a number)
                try:
                    if isinstance(pl_amount, str):
                        # Handle potential string formatting issues
                        pl_amount_str = pl_amount.strip().replace(',', '').replace('$', '')
                        pl_amount = float(pl_amount_str)
                    else:
                        # Should already be a number, just convert to float
                        pl_amount = float(pl_amount)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Row {index + 1}: Cannot convert PL Amount ('{pl_amount}') to number. Error: {str(e)}")
                
                # Validate transaction type
                if transaction_type not in ['DEPO', 'WITH']:
                    raise ValueError(f"Row {index + 1}: Transaction type must be 'DEPO' or 'WITH', found '{transaction_type}'")
                
                # Parse MarketName column to determine transaction type and extract stock info
                if 'Card payment' in market_name:
                    # Card payment - cash flow into account, ignore for stock analysis
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': 'CASH_DEPOSIT',
                        'action': 'Cash_In',
                        'quantity': 1,
                        'price': abs(pl_amount)
                    })
                
                elif 'Returned to card' in market_name:
                    # Cash withdrawal - create a cash transaction record
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': 'CASH_WITHDRAWAL',
                        'action': 'Cash_Out',
                        'quantity': 1,
                        'price': abs(pl_amount)
                    })
                
                elif 'DIVIDEND' in market_name:
                    # Extract stock name before DIVIDEND
                    stock_name = market_name.split('DIVIDEND')[0].strip()
                    if not stock_name:
                        raise ValueError(f"Row {index + 1}: Cannot extract stock name from dividend transaction: {market_name}")
                    
                    # Handle negative PL Amount for dividend withdrawals
                    if pl_amount < 0:
                        # This is a dividend withdrawal - subtract from dividends
                        standard_transactions.append({
                            'date': text_date,
                            'symbol': stock_name,
                            'action': 'Dividend_Withdrawal',
                            'quantity': 1,
                            'price': abs(pl_amount)  # Store as positive but mark as withdrawal
                        })
                    else:
                        # Regular dividend payment
                        standard_transactions.append({
                            'date': text_date,
                            'symbol': stock_name,
                            'action': 'Dividend',
                            'quantity': 1,
                            'price': abs(pl_amount)
                        })
                
                elif 'COMM' in market_name:
                    # Commission transaction
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': 'COMMISSION',
                        'action': 'Commission',
                        'quantity': 1,
                        'price': abs(pl_amount)
                    })
                
                elif 'CONS' in market_name:
                    # Stock transaction - parse the format
                    stock_info = self._parse_cons_transaction(market_name, index + 1, pl_amount)
                    
                    # Determine if it's a buy or sell based on transaction type
                    action = 'Buy' if transaction_type == 'WITH' else 'Sell'
                    
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': stock_info['stock_name'],
                        'action': action,
                        'quantity': stock_info['quantity'],
                        'price': stock_info['unit_price']
                    })
                
                elif summary == 'Share Dealing Commissions' or (market_name == '' and transaction_type == 'WITH' and pl_amount < 0):
                    # Commission transaction (empty MarketName with negative PL Amount for WITH transaction)
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': 'COMMISSION',
                        'action': 'Commission',
                        'quantity': 1,
                        'price': abs(pl_amount)
                    })
                
                elif pl_amount < 0 and summary.upper() == 'DIVIDEND':
                    # Special case: Negative PL Amount with Summary = DIVIDEND (dividend withdrawal)
                    # Extract stock name from available data or use a generic name
                    stock_name = market_name.strip() if market_name.strip() else 'UNKNOWN_STOCK'
                    
                    standard_transactions.append({
                        'date': text_date,
                        'symbol': stock_name,
                        'action': 'Dividend_Withdrawal',
                        'quantity': 1,
                        'price': abs(pl_amount)
                    })
                
                else:
                    # Unknown transaction type - strict validation requires we handle all cases
                    raise ValueError(f"Row {index + 1}: Unknown MarketName format: {market_name}, Summary: {summary}")
                
            except Exception as e:
                # Re-raise with clear context
                raise ValueError(f"Error processing row {index + 1}: {str(e)}")
        
        return pd.DataFrame(standard_transactions)
    
    def _parse_cons_transaction(self, market_name: str, row_num: int, pl_amount: float) -> dict:
        """Parse CONS transaction to extract stock name, quantity, and price"""
        try:
            # Split by CONS to get stock name and transaction details
            parts = market_name.split('CONS')
            if len(parts) != 2:
                raise ValueError(f"Invalid CONS format - must contain exactly one 'CONS': {market_name}")
            
            stock_name = parts[0].strip()
            transaction_details = parts[1].strip()
            
            if not stock_name:
                raise ValueError(f"Stock name cannot be empty in: {market_name}")
            
            # Parse transaction details: format like " 127@229 Z70LK:1593848~1369"
            # Extract quantity@price part (first part before any space)
            if '@' not in transaction_details:
                raise ValueError(f"Missing @ symbol in transaction details: {transaction_details}")
            
            # Get the part before any space or additional info
            quantity_price_part = transaction_details.split()[0] if ' ' in transaction_details else transaction_details
            
            if '@' not in quantity_price_part:
                raise ValueError(f"Invalid quantity@price format: {quantity_price_part}")
            
            # Split quantity and price
            quantity_str, price_str = quantity_price_part.split('@', 1)  # Split only on first @
            
            # Parse quantity
            try:
                quantity = int(quantity_str.strip())
                if quantity <= 0:
                    raise ValueError(f"Quantity must be positive: {quantity}")
            except ValueError as e:
                raise ValueError(f"Invalid quantity '{quantity_str}': {str(e)}")
            
            # Parse price (always shift decimal point two places to the left)
            try:
                price_str_clean = price_str.strip()
                # Convert to float first, then shift decimal point two places to left
                price_value = float(price_str_clean)
                unit_price = price_value / 100.0  # Always divide by 100 (527.5 -> 5.275, 229 -> 2.29)
                
                if unit_price <= 0:
                    raise ValueError(f"Price must be positive: {unit_price}")
                    
            except ValueError as e:
                raise ValueError(f"Invalid price '{price_str}': {str(e)}")
            
            # Validate calculated total against PL Amount
            calculated_total = quantity * unit_price
            pl_amount_abs = abs(pl_amount)
            tolerance = 0.02  # Allow small rounding differences
            
            if abs(calculated_total - pl_amount_abs) > tolerance:
                st.warning(f"Row {row_num}: Calculated total ({calculated_total:.2f}) doesn't match PL Amount ({pl_amount_abs:.2f}) - using PL Amount for accuracy")
                # Use the PL Amount to calculate the correct unit price
                unit_price = pl_amount_abs / quantity
            
            return {
                'stock_name': stock_name,
                'quantity': quantity,
                'unit_price': unit_price
            }
            
        except Exception as e:
            raise ValueError(f"Row {row_num}: Error parsing CONS transaction '{market_name}': {str(e)}")
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types"""
        cleaned_df = df.copy()
        
        # Clean column names to lowercase for consistency
        cleaned_df.columns = [col.lower() for col in cleaned_df.columns]
        
        # Convert date column
        try:
            cleaned_df['date'] = pd.to_datetime(cleaned_df['date'])
            # Convert to date only (remove time component)
            cleaned_df['date'] = cleaned_df['date'].dt.date
        except Exception as e:
            raise ValueError(f"Error converting dates: {str(e)}")
        
        # Clean symbol column
        cleaned_df['symbol'] = cleaned_df['symbol'].astype(str).str.strip().str.upper()
        
        # Clean action column
        cleaned_df['action'] = cleaned_df['action'].astype(str).str.strip().str.title()
        
        # Convert quantity to numeric
        try:
            # Remove any non-numeric characters except decimal point and negative sign
            cleaned_df['quantity'] = pd.to_numeric(
                cleaned_df['quantity'].astype(str).str.replace(r'[^\d.-]', '', regex=True),
                errors='coerce'
            )
        except Exception as e:
            raise ValueError(f"Error converting quantities: {str(e)}")
        
        # Convert price to numeric
        try:
            # Remove currency symbols and commas
            cleaned_df['price'] = pd.to_numeric(
                cleaned_df['price'].astype(str).str.replace(r'[\$,]', '', regex=True),
                errors='coerce'
            )
        except Exception as e:
            raise ValueError(f"Error converting prices: {str(e)}")
        
        # Clean and validate PL Amount column
        if 'pl amount' in cleaned_df.columns:
            try:
                # Convert PL Amount to float, removing currency symbols and commas
                cleaned_df['pl amount'] = pd.to_numeric(
                    cleaned_df['pl amount'].astype(str).str.replace(r'[\$,]', '', regex=True),
                    errors='coerce'
                )
                
                # Handle negative PL Amount values - these are dividend withdrawals
                negative_pl_mask = cleaned_df['pl amount'] < 0
                if negative_pl_mask.any():
                    for idx in cleaned_df[negative_pl_mask].index:
                        # Check if Summary is DIVIDEND for negative PL Amount
                        summary_value = str(cleaned_df.loc[idx, 'summary']).strip().upper()
                        if summary_value == 'DIVIDEND':
                            # This is a dividend withdrawal - keep negative value
                            pass
                        else:
                            # Unexpected negative value - raise warning but continue
                            print(f"Warning: Row {idx + 1} has negative PL Amount ({cleaned_df.loc[idx, 'pl amount']}) but Summary is '{summary_value}', not 'DIVIDEND'")
                            
            except Exception as e:
                raise ValueError(f"Error converting PL Amount to numeric: {str(e)}")
        
        return cleaned_df
    
    def _validate_data_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic validation without removing any rows - all validation is done in transform step"""
        cleaned_df = df.copy()
        
        # No data removal - all validation and error handling is done in the transform step
        # This function now just ensures proper data types after transformation
        
        # Validate dates (convert to date objects)
        try:
            cleaned_df['date'] = pd.to_datetime(cleaned_df['date']).dt.date
        except Exception as e:
            raise ValueError(f"Error converting dates: {str(e)}")
        
        # Sort by date
        cleaned_df = cleaned_df.sort_values('date').reset_index(drop=True)
        
        st.success(f"✅ Successfully processed {len(cleaned_df)} transactions")
        
        return cleaned_df
    
    def validate_file_format(self, df: pd.DataFrame) -> bool:
        """Validate if the DataFrame has the expected format"""
        try:
            # Check if we have the required columns
            df_columns = [col.strip().title() for col in df.columns]
            
            for required_col in self.required_columns:
                if required_col not in df_columns:
                    return False
            
            # Check if we have at least one row of data
            if len(df) < 1:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Get summary statistics of the processed data"""
        if df.empty:
            return {}
        
        summary = {
            'total_transactions': len(df),
            'unique_symbols': df['symbol'].nunique(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max()
            },
            'transaction_types': df['action'].value_counts().to_dict(),
            'symbols': sorted(df['symbol'].unique().tolist())
        }
        
        return summary
