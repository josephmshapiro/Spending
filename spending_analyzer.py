import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

class SpendingAnalyzer:
    def __init__(self):
        self.data = None
        self.categories = {
            'groceries': ['grocery', 'food', 'market', 'trader', 'whole foods'],
            'dining': ['restaurant', 'cafe', 'coffee', 'doordash', 'uber eats'],
            'transport': ['uber', 'lyft', 'taxi', 'transit', 'gas', 'fuel'],
            'shopping': ['amazon', 'target', 'walmart', 'store'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone'],
            'entertainment': ['netflix', 'spotify', 'movie', 'theater'],
            'health': ['pharmacy', 'doctor', 'medical', 'fitness'],
        }
    
    def read_csv(self, filepath):
        """Read a CSV file and standardize the format"""
        df = pd.read_csv(filepath)
        
        # Try to identify date and amount columns
        date_col = None
        amount_col = None
        
        # Look for date columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col])
                    date_col = col
                    break
                except:
                    continue
        
        # Look for amount columns
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64'] or (
                df[col].dtype == 'object' and df[col].str.contains(r'[\d\.\-\$]').all()
            ):
                amount_col = col
                break
        
        if not date_col or not amount_col:
            raise ValueError("Could not identify date and amount columns")
            
        # Standardize the dataframe
        standardized = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]),
            'description': df.select_dtypes(include=['object']).iloc[:, 0],
            'amount': pd.to_numeric(df[amount_col].astype(str).str.replace('[\$,]', '', regex=True))
        })
        
        return standardized
    
    def categorize_transaction(self, description):
        """Categorize a transaction based on its description"""
        description = description.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        return 'other'
    
    def process_files(self, filepaths):
        """Process multiple CSV files and combine them"""
        dfs = []
        for filepath in filepaths:
            try:
                df = self.read_csv(filepath)
                dfs.append(df)
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")
                
        if not dfs:
            raise ValueError("No valid files to process")
            
        # Combine all dataframes
        self.data = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates
        self.data = self.data.drop_duplicates()
        
        # Sort by date
        self.data = self.data.sort_values('date')
        
        # Add categories
        self.data['category'] = self.data['description'].apply(self.categorize_transaction)
        
        return self.data
    
    def generate_insights(self):
        """Generate spending insights"""
        if self.data is None:
            raise ValueError("No data available. Please process files first.")
            
        insights = {
            'total_spending': self.data['amount'].sum(),
            'avg_monthly_spending': self.data.groupby(
                self.data['date'].dt.to_period('M')
            )['amount'].sum().mean(),
            'spending_by_category': self.data.groupby('category')['amount'].sum().to_dict(),
            'top_merchants': self.data.groupby('description')['amount'].sum().nlargest(5).to_dict(),
            'monthly_trend': self.data.groupby(
                self.data['date'].dt.to_period('M')
            )['amount'].sum().to_dict()
        }
        
        return insights
    
    def plot_spending_trends(self):
        """Create visualizations of spending trends"""
        if self.data is None:
            raise ValueError("No data available. Please process files first.")
            
        # Monthly spending trend
        monthly_spending = self.data.groupby(
            self.data['date'].dt.to_period('M')
        )['amount'].sum().reset_index()
        monthly_spending['date'] = monthly_spending['date'].astype(str)
        
        fig1 = px.line(monthly_spending, x='date', y='amount',
                      title='Monthly Spending Trend')
        
        # Spending by category
        category_spending = self.data.groupby('category')['amount'].sum().reset_index()
        fig2 = px.pie(category_spending, values='amount', names='category',
                      title='Spending by Category')
        
        return fig1, fig2
    
    def export_to_excel(self, output_path):
        """Export analyzed data to Excel"""
        if self.data is None:
            raise ValueError("No data available. Please process files first.")
            
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write transaction data
            self.data.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Write summary data
            insights = self.generate_insights()
            
            # Create summary dataframe
            summary_data = {
                'Metric': ['Total Spending', 'Average Monthly Spending'],
                'Value': [insights['total_spending'], insights['avg_monthly_spending']]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Write category spending
            category_spending = pd.DataFrame.from_dict(
                insights['spending_by_category'], 
                orient='index',
                columns=['Amount']
            )
            category_spending.to_excel(writer, sheet_name='Category Spending')
            
            # Write monthly trend
            monthly_trend = pd.DataFrame.from_dict(
                insights['monthly_trend'],
                orient='index',
                columns=['Amount']
            )
            monthly_trend.to_excel(writer, sheet_name='Monthly Trend')

# Example usage
if __name__ == "__main__":
    analyzer = SpendingAnalyzer()
    
    # Example file paths
    files = ['bank1.csv', 'bank2.csv']
    
    # Process files
    data = analyzer.process_files(files)
    
    # Generate insights
    insights = analyzer.generate_insights()
    print("Spending Insights:", insights)
    
    # Create visualizations
    trend_plot, category_plot = analyzer.plot_spending_trends()
    
    # Export to Excel
    analyzer.export_to_excel('spending_analysis.xlsx')