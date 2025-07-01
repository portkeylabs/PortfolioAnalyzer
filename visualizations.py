import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

class PortfolioVisualizer:
    """Create interactive visualizations for portfolio analysis"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_performance_chart(self, performance_data: pd.DataFrame) -> go.Figure:
        """Create portfolio performance over time chart"""
        if performance_data.empty:
            return self._create_empty_chart("No performance data available")
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Portfolio Value Over Time', 'Gain/Loss Over Time'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Portfolio value chart
        fig.add_trace(
            go.Scatter(
                x=performance_data['date'],
                y=performance_data['portfolio_value'],
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=6),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                              '<b>Portfolio Value:</b> $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add invested amount line
        fig.add_trace(
            go.Scatter(
                x=performance_data['date'],
                y=performance_data['cumulative_investment'],
                mode='lines',
                name='Total Invested',
                line=dict(color='#A23B72', width=2, dash='dash'),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                              '<b>Invested:</b> $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Gain/Loss chart
        colors = ['green' if x >= 0 else 'red' for x in performance_data['gain_loss']]
        fig.add_trace(
            go.Bar(
                x=performance_data['date'],
                y=performance_data['gain_loss'],
                name='Gain/Loss',
                marker_color=colors,
                hovertemplate='<b>Date:</b> %{x}<br>' +
                              '<b>Gain/Loss:</b> $%{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Portfolio Performance Analysis",
            height=600,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Gain/Loss ($)", row=2, col=1)
        
        return fig
    
    def create_allocation_pie_chart(self, holdings_df: pd.DataFrame) -> go.Figure:
        """Create portfolio allocation pie chart"""
        if holdings_df.empty:
            return self._create_empty_chart("No holdings data available")
        
        # Filter out very small allocations for better readability
        display_holdings = holdings_df[holdings_df['allocation_pct'] >= 1.0].copy()
        
        if len(display_holdings) < len(holdings_df):
            # Group small holdings together
            small_holdings_value = holdings_df[holdings_df['allocation_pct'] < 1.0]['current_value'].sum()
            small_holdings_pct = holdings_df[holdings_df['allocation_pct'] < 1.0]['allocation_pct'].sum()
            
            if small_holdings_pct > 0:
                other_row = pd.DataFrame({
                    'symbol': ['Others'],
                    'current_value': [small_holdings_value],
                    'allocation_pct': [small_holdings_pct]
                })
                display_holdings = pd.concat([display_holdings, other_row], ignore_index=True)
        
        fig = go.Figure(data=[go.Pie(
            labels=display_holdings['symbol'],
            values=display_holdings['current_value'],
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>' +
                          'Value: $%{value:,.2f}<br>' +
                          'Allocation: %{percent}<extra></extra>',
            marker=dict(colors=self.color_palette)
        )])
        
        fig.update_layout(
            title="Portfolio Allocation by Holdings",
            template='plotly_white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    def create_sector_pie_chart(self, sector_df: pd.DataFrame) -> go.Figure:
        """Create sector allocation pie chart"""
        if sector_df.empty:
            return self._create_empty_chart("No sector data available")
        
        fig = go.Figure(data=[go.Pie(
            labels=sector_df['sector'],
            values=sector_df['value'],
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>' +
                          'Value: $%{value:,.2f}<br>' +
                          'Allocation: %{percent}<extra></extra>',
            marker=dict(colors=self.color_palette)
        )])
        
        fig.update_layout(
            title="Portfolio Allocation by Sector",
            template='plotly_white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    def create_dividend_chart(self, dividend_history: pd.DataFrame) -> go.Figure:
        """Create dividend income over time chart"""
        if dividend_history.empty:
            return self._create_empty_chart("No dividend data available")
        
        # Convert date to datetime for proper sorting
        dividend_history = dividend_history.copy()
        dividend_history['date'] = pd.to_datetime(dividend_history['date'])
        dividend_history = dividend_history.sort_values('date')
        
        # Group by month for better visualization
        dividend_history['month'] = dividend_history['date'].dt.to_period('M')
        monthly_dividends = dividend_history.groupby('month')['amount'].sum().reset_index()
        monthly_dividends['month'] = monthly_dividends['month'].astype(str)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=monthly_dividends['month'],
            y=monthly_dividends['amount'],
            name='Monthly Dividends',
            marker_color='#2E86AB',
            hovertemplate='<b>Month:</b> %{x}<br>' +
                          '<b>Dividends:</b> $%{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Dividend Income Over Time",
            xaxis_title="Month",
            yaxis_title="Dividend Amount ($)",
            template='plotly_white',
            height=300
        )
        
        return fig
    
    def create_performance_comparison_chart(self, holdings_df: pd.DataFrame) -> go.Figure:
        """Create individual stock performance comparison chart"""
        if holdings_df.empty:
            return self._create_empty_chart("No holdings data available")
        
        # Sort by gain/loss percentage
        sorted_holdings = holdings_df.sort_values('gain_loss_pct', ascending=True)
        
        # Color bars based on performance
        colors = ['red' if x < 0 else 'green' for x in sorted_holdings['gain_loss_pct']]
        
        fig = go.Figure(data=[go.Bar(
            y=sorted_holdings['symbol'],
            x=sorted_holdings['gain_loss_pct'],
            orientation='h',
            marker_color=colors,
            hovertemplate='<b>%{y}</b><br>' +
                          'Performance: %{x:+.2f}%<br>' +
                          'Gain/Loss: $%{customdata:,.2f}<extra></extra>',
            customdata=sorted_holdings['gain_loss']
        )])
        
        fig.update_layout(
            title="Individual Stock Performance",
            xaxis_title="Performance (%)",
            yaxis_title="Stock Symbol",
            template='plotly_white',
            height=max(400, len(sorted_holdings) * 30),
            yaxis=dict(autorange="reversed")
        )
        
        # Add vertical line at 0%
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        
        return fig
    
    def create_investment_timeline(self, transactions_df: pd.DataFrame) -> go.Figure:
        """Create investment timeline chart"""
        if transactions_df.empty:
            return self._create_empty_chart("No transaction data available")
        
        # Filter buy transactions
        buy_transactions = transactions_df[transactions_df['action'] == 'Buy'].copy()
        
        if buy_transactions.empty:
            return self._create_empty_chart("No buy transactions found")
        
        # Calculate cumulative investment
        buy_transactions = buy_transactions.sort_values('date')
        buy_transactions['investment_amount'] = buy_transactions['quantity'] * buy_transactions['price']
        buy_transactions['cumulative_investment'] = buy_transactions['investment_amount'].cumsum()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=buy_transactions['date'],
            y=buy_transactions['cumulative_investment'],
            mode='lines+markers',
            name='Cumulative Investment',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                          '<b>Cumulative Investment:</b> $%{y:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Investment Timeline",
            xaxis_title="Date",
            yaxis_title="Cumulative Investment ($)",
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
