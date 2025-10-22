"""
PE Portfolio Companies - Interactive Dashboard
"""
import streamlit as st
import pandas as pd
from database_models import get_session, PEFirm, PortfolioCompany
from sqlalchemy import func, or_
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="PE Portfolio Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff !important;
    }
    div[data-testid="metric-container"] {
        background-color: #1f77b4;
        border: 2px solid #1f77b4;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_pe_firms():
    """Load all PE firms"""
    session = get_session()
    firms = session.query(PEFirm).all()
    session.close()
    return [(f.name, f.id) for f in firms]


@st.cache_data
def load_all_companies():
    """Load all companies as DataFrame"""
    session = get_session()
    companies = session.query(PortfolioCompany).all()
    
    data = []
    for c in companies:
        data.append({
            'Company': c.name,
            'PE Firm': c.pe_firm.name,
            'Sector': c.sector,
            'Status': c.status,
            'Investment Year': c.investment_year,
            'Headquarters': c.headquarters,
            'Website': c.website,
            'Description': c.description,
            'Exit Info': c.exit_info,
        })
    
    session.close()
    return pd.DataFrame(data)


@st.cache_data
def get_status_counts(pe_firm_name=None):
    """Get status distribution"""
    session = get_session()
    query = session.query(
        PortfolioCompany.status,
        func.count(PortfolioCompany.id).label('count')
    )
    
    if pe_firm_name:
        query = query.join(PEFirm).filter(PEFirm.name == pe_firm_name)
    
    results = query.group_by(PortfolioCompany.status).all()
    session.close()
    
    df = pd.DataFrame(results, columns=['Status', 'Count'])
    
    # Simplify status labels
    df['Status Category'] = df['Status'].apply(lambda x: 
        'Current' if x == 'current' else 
        'Former' if x == 'former' else 
        'Exited'
    )
    
    return df


@st.cache_data
def get_sector_distribution(pe_firm_name=None):
    """Get sector distribution"""
    session = get_session()
    query = session.query(
        PortfolioCompany.sector,
        func.count(PortfolioCompany.id).label('count')
    )
    
    if pe_firm_name:
        query = query.join(PEFirm).filter(PEFirm.name == pe_firm_name)
    
    results = query.filter(PortfolioCompany.sector != '').group_by(PortfolioCompany.sector).all()
    session.close()
    
    return pd.DataFrame(results, columns=['Sector', 'Count']).sort_values('Count', ascending=False)


@st.cache_data
def get_investment_timeline(pe_firm_name=None):
    """Get investment timeline"""
    session = get_session()
    query = session.query(
        PortfolioCompany.investment_year,
        func.count(PortfolioCompany.id).label('count')
    )
    
    if pe_firm_name:
        query = query.join(PEFirm).filter(PEFirm.name == pe_firm_name)
    
    results = query.filter(PortfolioCompany.investment_year != '').group_by(
        PortfolioCompany.investment_year
    ).all()
    session.close()
    
    df = pd.DataFrame(results, columns=['Year', 'Count'])
    df['Year'] = df['Year'].astype(str)
    return df.sort_values('Year')


def main():
    # Header
    st.markdown('<div class="main-header">💼 PE Portfolio Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🔍 Filters")
    
    # Clear filters button at the top
    if st.sidebar.button("🗑️ Clear All Filters", use_container_width=True, type="secondary"):
        # Clear specific session state keys for our filters
        for key in ['firm_select', 'status_select', 'sector_select']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Load data
    firms = load_pe_firms()
    firm_names = [f[0] for f in firms]
    
    # Load companies
    df = load_all_companies()
    
    # Get all unique values for filters
    all_firm_names = sorted(df['PE Firm'].unique().tolist())
    all_statuses = sorted(df['Status'].unique().tolist())
    all_sectors = sorted([s for s in df['Sector'].unique() if s and len(s) > 0])
    
    # PE Firm multi-select
    selected_firms = st.sidebar.multiselect(
        "PE Firm",
        options=all_firm_names,
        default=None,
        key="firm_select"
    )
    
    # Status filter - Multi-select
    selected_statuses = st.sidebar.multiselect(
        "Status",
        options=all_statuses,
        default=None,
        key="status_select"
    )
    
    # Sector filter - Multi-select
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        options=all_sectors,
        default=None,
        key="sector_select"
    )
    
    # Apply filters
    df_filtered = df.copy()
    
    # Filter by PE firms
    if selected_firms:
        df_filtered = df_filtered[df_filtered['PE Firm'].isin(selected_firms)]
    
    # Filter by status
    if selected_statuses:
        df_filtered = df_filtered[df_filtered['Status'].isin(selected_statuses)]
    
    # Filter by sectors
    if selected_sectors:
        mask = df_filtered['Sector'].apply(
            lambda x: any(sector.lower() in str(x).lower() for sector in selected_sectors) if pd.notna(x) else False
        )
        df_filtered = df_filtered[mask]
    
    # Search
    search_term = st.sidebar.text_input("🔍 Search Companies", "")
    if search_term:
        df_filtered = df_filtered[
            df_filtered['Company'].str.contains(search_term, case=False, na=False) |
            df_filtered['Description'].str.contains(search_term, case=False, na=False)
        ]
    
    # Export button in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Export Data")
    csv = df_filtered.to_csv(index=False)
    firm_label = f"{len(selected_firms)}_firms" if selected_firms else "all_firms"
    status_label = f"{len(selected_statuses)}_statuses" if selected_statuses else "all"
    st.sidebar.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=csv,
        file_name=f"portfolio_{firm_label}_{status_label}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.sidebar.caption(f"Will export {len(df_filtered)} companies")
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])
    
    with col1:
        st.metric("Total Companies", len(df_filtered))
    
    with col2:
        current_count = len(df_filtered[df_filtered['Status'] == 'current'])
        st.metric("Current Portfolio", current_count)
    
    with col3:
        exited_count = len(df_filtered[
            (df_filtered['Status'] == 'former') | 
            (df_filtered['Status'].str.startswith('past', na=False))
        ])
        st.metric("Exited", exited_count)
    
    with col4:
        unique_sectors = df_filtered['Sector'].nunique()
        st.metric("Sectors", unique_sectors)
    
    with col5:
        csv = df_filtered.to_csv(index=False)
        firm_label = "_".join([f.lower().replace(' ', '_') for f in selected_firms]) if selected_firms else "all"
        st.download_button(
            label="📥 Export All Filtered Data",
            data=csv,
            file_name=f"portfolio_export_{firm_label}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Analytics", "📋 Companies", "🔍 Company Details"])
    
    with tab1:
        st.subheader("Portfolio Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Status breakdown
            st.markdown("#### Status Distribution")
            # Don't filter by firm for the charts - use the filtered data
            status_df = get_status_counts(None)
            
            # Group by category
            status_summary = status_df.groupby('Status Category')['Count'].sum().reset_index()
            
            fig = px.pie(
                status_summary, 
                values='Count', 
                names='Status Category',
                color='Status Category',
                color_discrete_map={'Current': '#2ecc71', 'Former': '#e74c3c', 'Exited': '#f39c12'},
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top sectors
            st.markdown("#### Top 10 Sectors")
            sector_df = get_sector_distribution(None)
            
            fig = px.bar(
                sector_df.head(10),
                x='Count',
                y='Sector',
                orientation='h',
                color='Count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Investment Analytics")
        
        # Investment timeline
        st.markdown("#### Investment Timeline")
        timeline_df = get_investment_timeline(None)
        
        if not timeline_df.empty:
            fig = px.bar(
                timeline_df,
                x='Year',
                y='Count',
                title='Number of Investments by Year',
                color='Count',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No investment year data available")
        
        # Sector breakdown by status
        st.markdown("#### Sector Analysis")
        
        if not df_filtered.empty:
            # Create sector vs status heatmap
            sector_status = pd.crosstab(
                df_filtered['Sector'].str[:50],  # Truncate long names
                df_filtered['Status'].apply(lambda x: 
                    'Current' if x == 'current' else 
                    'Former' if x == 'former' else 
                    'Exited'
                )
            ).head(15)
            
            fig = px.imshow(
                sector_status,
                labels=dict(x="Status", y="Sector", color="Count"),
                aspect="auto",
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader(f"Companies ({len(df_filtered)} results)")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col2:
            items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
        
        # Pagination
        total_pages = (len(df_filtered) - 1) // items_per_page + 1
        page = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1)
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        # Display table
        display_cols = ['Company', 'PE Firm', 'Sector', 'Status', 'Investment Year', 'Headquarters']
        st.dataframe(
            df_filtered[display_cols].iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = df_filtered.to_csv(index=False)
        firm_label = "_".join([f.lower().replace(' ', '_') for f in selected_firms]) if selected_firms else "all"
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"portfolio_companies_{firm_label}.csv",
            mime="text/csv"
        )
    
    with tab4:
        st.subheader("Company Details")
        
        # Company selector
        company_names = sorted(df_filtered['Company'].unique().tolist())
        
        if company_names:
            selected_company = st.selectbox("Select a company", company_names)
            
            if selected_company:
                company_data = df_filtered[df_filtered['Company'] == selected_company].iloc[0]
                
                # Display company info
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"### {company_data['Company']}")
                    st.markdown(f"**PE Firm:** {company_data['PE Firm']}")
                    st.markdown(f"**Sector:** {company_data['Sector']}")
                    st.markdown(f"**Status:** {company_data['Status']}")
                    st.markdown(f"**Investment Year:** {company_data['Investment Year']}")
                    st.markdown(f"**Headquarters:** {company_data['Headquarters']}")
                    
                    if company_data['Website']:
                        st.markdown(f"**Website:** [{company_data['Website']}]({company_data['Website']})")
                
                with col2:
                    # Status badge
                    status = company_data['Status']
                    if status == 'current':
                        st.success("✅ Current Portfolio")
                    elif status == 'former':
                        st.error("❌ Exited")
                    else:
                        st.warning("⚠️ Past Investment")
                
                # Description
                if company_data['Description']:
                    st.markdown("#### Description")
                    st.write(company_data['Description'])
                
                # Exit info
                if company_data['Exit Info']:
                    st.markdown("#### Exit Information")
                    st.info(company_data['Exit Info'])
        else:
            st.info("No companies found with the current filters")


if __name__ == "__main__":
    main()
