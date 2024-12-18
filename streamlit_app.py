import streamlit as st
import pandas as pd
from spending_analyzer import SpendingAnalyzer
import plotly.express as px
from pathlib import Path
import tempfile

st.set_page_config(page_title="Personal Spending Analyzer", layout="wide")

st.title("Personal Spending Analyzer")

st.write("""
## Upload Your Bank Statements
Upload your CSV files from your bank statements below. The app will analyze your spending patterns and generate insights.
""")

# File upload
uploaded_files = st.file_uploader("Choose CSV files", accept_multiple_files=True, type=['csv'])

if uploaded_files:
    try:
        analyzer = SpendingAnalyzer()
        
        # Save uploaded files temporarily
        temp_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_paths.append(tmp_file.name)
        
        # Process the files
        data = analyzer.process_files(temp_paths)
        
        # Generate insights
        insights = analyzer.generate_insights()
        
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Summary Statistics")
            st.write(f"Total Spending: ${insights['total_spending']:,.2f}")
            st.write(f"Average Monthly Spending: ${insights['avg_monthly_spending']:,.2f}")
            
            st.subheader("Top Spending Categories")
            category_data = pd.DataFrame.from_dict(
                insights['spending_by_category'], 
                orient='index',
                columns=['Amount']
            ).sort_values('Amount', ascending=False)
            st.dataframe(category_data)
        
        with col2:
            st.subheader("Top Merchants")
            merchant_data = pd.DataFrame.from_dict(
                insights['top_merchants'],
                orient='index',
                columns=['Amount']
            )
            st.dataframe(merchant_data)
        
        # Display visualizations
        st.subheader("Spending Trends")
        trend_plot, category_plot = analyzer.plot_spending_trends()
        st.plotly_chart(trend_plot, use_container_width=True)
        st.plotly_chart(category_plot, use_container_width=True)
        
        # Export button
        if st.button("Export to Excel"):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                analyzer.export_to_excel(tmp_file.name)
                with open(tmp_file.name, 'rb') as f:
                    st.download_button(
                        label="Download Excel file",
                        data=f,
                        file_name="spending_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        # Cleanup temporary files
        for path in temp_paths:
            Path(path).unlink()
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please make sure your CSV files contain date and amount columns.")

st.write("""
### Instructions:
1. Export your bank statements as CSV files
2. Upload them using the file uploader above
3. View your spending analysis
4. Download the Excel report for detailed analysis

### Supported Banks:
- Most major banks (statements must be in CSV format)
- Common columns needed: Date, Description, Amount
""")
