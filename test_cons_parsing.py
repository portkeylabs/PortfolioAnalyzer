#!/usr/bin/env python3
"""Test script to validate CONS parsing logic"""

def parse_cons_transaction(market_name: str, pl_amount: float) -> dict:
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
        
        validation_passed = abs(calculated_total - pl_amount_abs) <= tolerance
        
        if not validation_passed:
            print(f"WARNING: Calculated total ({calculated_total:.2f}) doesn't match PL Amount ({pl_amount_abs:.2f})")
            # Use the PL Amount to calculate the correct unit price
            unit_price = pl_amount_abs / quantity
        
        return {
            'stock_name': stock_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'calculated_total': calculated_total,
            'pl_amount_abs': pl_amount_abs,
            'validation_passed': validation_passed
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing CONS transaction '{market_name}': {str(e)}")

# Test cases
test_cases = [
    {
        'market_name': 'BetaShares S&P 500 Yield Maximiser Fund CONS 37@2150 Z70LK:1749026~249',
        'pl_amount': -795.50,  # Expected: 37 * 21.50 = 795.50
        'expected_stock': 'BetaShares S&P 500 Yield Maximiser Fund',
        'expected_quantity': 37,
        'expected_unit_price': 21.50
    },
    {
        'market_name': 'Betashares Crypto Innovators ETF CONS 127@229 Z70LK:1593848~1369',
        'pl_amount': -290.83,  # Expected: 127 * 2.29 = 290.83
        'expected_stock': 'Betashares Crypto Innovators ETF',
        'expected_quantity': 127,
        'expected_unit_price': 2.29
    },
    {
        'market_name': 'Polynovo Limited CONS 358@124 Z70LK:1470050~3319',
        'pl_amount': -443.92,  # Expected: 358 * 1.24 = 443.92
        'expected_stock': 'Polynovo Limited',
        'expected_quantity': 358,
        'expected_unit_price': 1.24
    },
    {
        'market_name': 'Qantas Airways Ltd CONS 143@527.5 Z70LK:1748411~2100',
        'pl_amount': -754.325,  # Expected: 143 * 5.275 = 754.325
        'expected_stock': 'Qantas Airways Ltd',
        'expected_quantity': 143,
        'expected_unit_price': 5.275  # 527.5 / 100 = 5.275 (shift decimal 2 places left)
    }
]

print("Testing CONS parsing logic...")
print("=" * 60)

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest Case {i}:")
    print(f"Input: {test_case['market_name']}")
    print(f"PL Amount: {test_case['pl_amount']}")
    
    try:
        result = parse_cons_transaction(test_case['market_name'], test_case['pl_amount'])
        
        print(f"Parsed Stock Name: '{result['stock_name']}'")
        print(f"Parsed Quantity: {result['quantity']}")
        print(f"Parsed Unit Price: {result['unit_price']:.2f}")
        print(f"Calculated Total: {result['calculated_total']:.2f}")
        print(f"PL Amount (abs): {result['pl_amount_abs']:.2f}")
        print(f"Validation Passed: {result['validation_passed']}")
        
        # Check if results match expectations
        stock_match = result['stock_name'] == test_case['expected_stock']
        quantity_match = result['quantity'] == test_case['expected_quantity']
        price_match = abs(result['unit_price'] - test_case['expected_unit_price']) < 0.01
        
        print(f"Stock Name Match: {stock_match}")
        print(f"Quantity Match: {quantity_match}")
        print(f"Unit Price Match: {price_match}")
        
        if stock_match and quantity_match and price_match:
            print("✅ TEST PASSED")
        else:
            print("❌ TEST FAILED")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 60)
print("Testing complete!")