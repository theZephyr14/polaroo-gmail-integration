"""
Enhanced Streamlit application for Polaroo utility bill processing.

This app provides a professional interface for operations teams to:
1. Run monthly utility bill calculations
2. View historical data and trends
3. Export results for billing purposes
4. Configure allowances and settings

The system automatically:
- Scrapes the latest Polaroo utility report
- Calculates excess charges based on configured allowances
- Stores data for historical tracking
- Provides actionable insights for property management
"""

import tempfile
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

from polaroo_scrape import download_report_sync
from polaroo_process import process_usage, USER_ADDRESSES
from load_supabase import upload_raw, upsert_monthly

# Page configuration
st.set_page_config(
    page_title="Utility Bill Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_monthly_calculation(elec_allowance: float, water_allowance: float) -> pd.DataFrame:
    """Run the complete monthly utility calculation workflow.
    
    Parameters
    ----------
    elec_allowance : float
        Allowed electricity cost before extra charges are incurred.
    water_allowance : float
        Allowed water cost before extra charges are incurred.
    
    Returns
    -------
    pandas.DataFrame
        Processed usage records with over-usage calculations.
    """
    try:
        # Step 1: Download latest report from Polaroo
        with st.status("🔄 Downloading latest utility report from Polaroo...", expanded=True) as status:
            file_bytes, filename = download_report_sync()
            status.update(label="✅ Report downloaded successfully", state="complete")
        
        # Step 2: Upload to Supabase for archival
        with st.status("💾 Archiving report to database...", expanded=True) as status:
            try:
                upload_raw(date.today(), file_bytes, filename)
                status.update(label="✅ Report archived successfully", state="complete")
            except Exception as e:
                st.warning(f"⚠️ Archive upload failed: {e}")
                status.update(label="⚠️ Archive upload failed", state="error")
        
        # Step 3: Process the data
        with st.status("📊 Processing utility data and calculating charges...", expanded=True) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            allowances = {"electricity": elec_allowance, "water": water_allowance}
            df = process_usage(tmp_path, allowances=allowances)
            
            # Clean up temporary file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            
            status.update(label="✅ Data processing complete", state="complete")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Calculation failed: {str(e)}")
        raise

def display_results(df: pd.DataFrame, elec_allowance: float, water_allowance: float):
    """Display the calculation results with visualizations."""
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_elec_cost = df['elec_cost'].sum()
    total_water_cost = df['water_cost'].sum()
    total_elec_extra = df['elec_extra'].sum()
    total_water_extra = df['water_extra'].sum()
    
    with col1:
        st.metric("Total Electricity Cost", f"€{total_elec_cost:.2f}")
    with col2:
        st.metric("Total Water Cost", f"€{total_water_cost:.2f}")
    with col3:
        st.metric("Electricity Overages", f"€{total_elec_extra:.2f}", 
                 delta=f"{len(df[df['elec_extra'] > 0])} properties")
    with col4:
        st.metric("Water Overages", f"€{total_water_extra:.2f}", 
                 delta=f"{len(df[df['water_extra'] > 0])} properties")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Overages", "📈 Charts", "📋 Export"])
    
    with tab1:
        st.subheader("All Properties Summary")
        display_df = df.copy()
        display_df['Total Cost'] = display_df['elec_cost'] + display_df['water_cost']
        display_df['Total Extra'] = display_df['elec_extra'] + display_df['water_extra']
        
        # Color code rows with overages
        def highlight_overages(row):
            if row['Total Extra'] > 0:
                return ['background-color: #ffebee'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            display_df[['name', 'elec_cost', 'water_cost', 'elec_extra', 'water_extra', 'Total Cost', 'Total Extra']]
            .style.apply(highlight_overages, axis=1),
            use_container_width=True
        )
    
    with tab2:
        st.subheader("Properties with Overages")
        overages = df[(df['elec_extra'] > 0) | (df['water_extra'] > 0)].copy()
        
        if overages.empty:
            st.success("🎉 No properties exceeded their allowances this month!")
        else:
            st.dataframe(
                overages[['name', 'elec_cost', 'water_cost', 'elec_extra', 'water_extra']]
                .sort_values('elec_extra', ascending=False),
                use_container_width=True
            )
    
    with tab3:
        st.subheader("Utility Usage Visualization")
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Electricity Costs', 'Water Costs', 'Electricity Overages', 'Water Overages'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Electricity costs
        fig.add_trace(
            go.Bar(x=df['name'], y=df['elec_cost'], name='Electricity Cost', marker_color='#ff9800'),
            row=1, col=1
        )
        fig.add_hline(y=elec_allowance, line_dash="dash", line_color="red", 
                     annotation_text=f"Allowance: €{elec_allowance}", row=1, col=1)
        
        # Water costs
        fig.add_trace(
            go.Bar(x=df['name'], y=df['water_cost'], name='Water Cost', marker_color='#2196f3'),
            row=1, col=2
        )
        fig.add_hline(y=water_allowance, line_dash="dash", line_color="red", 
                     annotation_text=f"Allowance: €{water_allowance}", row=1, col=2)
        
        # Electricity overages
        fig.add_trace(
            go.Bar(x=df['name'], y=df['elec_extra'], name='Electricity Extra', marker_color='#f44336'),
            row=2, col=1
        )
        
        # Water overages
        fig.add_trace(
            go.Bar(x=df['name'], y=df['water_extra'], name='Water Extra', marker_color='#e91e63'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, title_text="Monthly Utility Analysis")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Export Results")
        
        # Prepare export data
        export_df = df.copy()
        export_df['calculation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        export_df['electricity_allowance'] = elec_allowance
        export_df['water_allowance'] = water_allowance
        
        # CSV export
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name=f"utility_report_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Excel export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='Utility Report', index=False)
            
            # Create summary sheet
            summary_data = {
                'Metric': ['Total Properties', 'Properties with Elec Overages', 'Properties with Water Overages',
                          'Total Electricity Cost', 'Total Water Cost', 'Total Electricity Extra', 'Total Water Extra'],
                'Value': [len(df), len(df[df['elec_extra'] > 0]), len(df[df['water_extra'] > 0]),
                         total_elec_cost, total_water_cost, total_elec_extra, total_water_extra]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        buffer.seek(0)
        st.download_button(
            label="📥 Download Excel Report",
            data=buffer.getvalue(),
            file_name=f"utility_report_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def main():
    """Main application function."""
    
    # Header
    st.title("⚡ Utility Bill Calculator")
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Allowances
    st.sidebar.subheader("Monthly Allowances (EUR)")
    elec_allow = st.sidebar.number_input(
        "Electricity allowance", 
        min_value=0.0, 
        value=100.0, 
        step=10.0,
        help="Monthly electricity cost allowance per property"
    )
    water_allow = st.sidebar.number_input(
        "Water allowance", 
        min_value=0.0, 
        value=50.0, 
        step=10.0,
        help="Monthly water cost allowance per property"
    )
    
    # Additional settings
    st.sidebar.subheader("Settings")
    auto_save = st.sidebar.checkbox("Auto-save to database", value=True)
    
    # Main content area
    st.header("📊 Monthly Utility Analysis")
    
    # Info box
    st.info(
        "💡 **How it works**: Click 'Calculate Monthly Report' to automatically download the latest "
        "utility data from Polaroo, calculate excess charges based on your configured allowances, "
        "and display the results with detailed analysis."
    )
    
    # Calculate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Calculate Monthly Report", type="primary", use_container_width=True):
            if st.session_state.get('calculation_running', False):
                st.warning("⚠️ Calculation already in progress...")
                return
            
            st.session_state.calculation_running = True
            
            try:
                # Run the calculation
                df = run_monthly_calculation(elec_allow, water_allow)
                
                # Store results in session state
                st.session_state.results = df
                st.session_state.allowances = {'electricity': elec_allow, 'water': water_allow}
                
                # Auto-save to database if enabled
                if auto_save:
                    try:
                        # Convert DataFrame to list of dicts for database storage
                        records = df.to_dict('records')
                        for record in records:
                            record['calculation_date'] = datetime.now().isoformat()
                            record['electricity_allowance'] = elec_allow
                            record['water_allowance'] = water_allow
                        
                        upsert_monthly(records)
                        st.success("✅ Results saved to database")
                    except Exception as e:
                        st.warning(f"⚠️ Database save failed: {e}")
                
                st.success("🎉 Monthly calculation completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Calculation failed: {str(e)}")
            finally:
                st.session_state.calculation_running = False
    
    # Display results if available
    if hasattr(st.session_state, 'results') and st.session_state.results is not None:
        st.markdown("---")
        display_results(
            st.session_state.results, 
            st.session_state.allowances['electricity'], 
            st.session_state.allowances['water']
        )
    else:
        st.markdown("---")
        st.info("👆 Click 'Calculate Monthly Report' to start the analysis.")

if __name__ == "__main__":
    main()
