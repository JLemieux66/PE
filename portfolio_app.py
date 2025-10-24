"""
PE Portfolio Companies - Enhanced Interactive Dashboard
with full Swarm enrichment data
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
    .company-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .company-name {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .company-subtitle {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 1rem;
    }
    .info-label {
        font-weight: 600;
        color: #495057;
    }
    .info-value {
        color: #212529;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_companies():
    """Load all companies with enrichment data"""
    session = get_session()
    companies = session.query(PortfolioCompany).all()
    
    data = []
    for c in companies:
        data.append({
            'ID': c.id,
            'Company': c.name,
            'PE Firm': c.pe_firm.name,
            'Sector': c.sector or '',
            'Industry': c.swarm_industry or '',
            'Industry Category': c.industry_category or '',
            'Status': c.status,
            'Founded': c.investment_year or '',
            'Headquarters': c.headquarters or '',
            'Website': c.website or '',
            'Description': c.description or '',
            'Exit Info': c.exit_info or '',
            # Crunchbase business metrics
            'Revenue Range': c.revenue_range or '',
            'Employee Count': c.employee_count or '',
            # Financial data
            'Market Cap': c.market_cap,
            'Total Funding': c.total_funding_usd,
            'Last Round Type': c.last_round_type or '',
            'Last Round Amount': c.last_round_amount_usd,
            # Company size
            'Size Class': c.size_class or '',
            # IPO data
            'IPO Year': c.ipo_year,
            'IPO Date': c.ipo_date or '',
            'Stock Exchange': c.stock_exchange or '',
            # Ownership
            'Ownership Status': c.ownership_status or '',
            'Is Public': c.is_public,
            'Is Acquired': c.is_acquired,
            'Customer Types': c.customer_types or '',
            'Summary': c.summary or '',
        })
    
    session.close()
    return pd.DataFrame(data)


def format_currency(value):
    """Format large numbers as currency"""
    if pd.isna(value) or value == 0:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    else:
        return f"${value:,.0f}"


def main():
    # Header
    st.markdown('<div class="main-header">💼 PE Portfolio Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    df = load_all_companies()
    
    # Sidebar Filters
    st.sidebar.title("🔍 Filters")
    
    # Clear filters button
    if st.sidebar.button("🗑️ Clear All Filters", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            if key.endswith('_filter'):
                del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Get unique values for filters
    all_firms = ['All'] + sorted(df['PE Firm'].unique().tolist())
    all_statuses = ['All'] + sorted(df['Status'].unique().tolist())
    all_categories = ['All'] + sorted([c for c in df['Industry Category'].unique() if c])
    all_sectors = ['All'] + sorted([s for s in df['Sector'].unique() if s])
    all_ownership = ['All'] + sorted([o for o in df['Ownership Status'].unique() if o])
    
    # PE Firm filter - Multi-select
    selected_firms = st.sidebar.multiselect(
        "PE Firm",
        options=[f for f in all_firms if f != 'All'],
        default=None,
        key="firm_filter"
    )
    
    # Status filter - Multi-select
    selected_statuses = st.sidebar.multiselect(
        "Status",
        options=[s for s in all_statuses if s != 'All'],
        default=None,
        key="status_filter"
    )
    
    # Industry Category filter - Multi-select (20 categories instead of 288 industries)
    selected_categories = st.sidebar.multiselect(
        "Industry Category",
        options=[c for c in all_categories if c != 'All'],
        default=None,
        key="category_filter"
    )
    
    # Sector filter - Multi-select
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        options=[s for s in all_sectors if s != 'All'],
        default=None,
        key="sector_filter"
    )
    
    # Ownership filter - Multi-select
    selected_ownership = st.sidebar.multiselect(
        "Ownership Status",
        options=[o for o in all_ownership if o != 'All'],
        default=None,
        key="ownership_filter"
    )
    
    # Public companies filter
    public_filter = st.sidebar.radio(
        "Company Type",
        options=["All", "Public Only", "Private Only"],
        key="public_filter"
    )
    
    # IPO Year range filter - handle mixed types
    try:
        # Convert IPO Year to numeric, coercing errors to NaN
        df_temp = df.copy()
        df_temp['IPO Year Numeric'] = pd.to_numeric(df_temp['IPO Year'], errors='coerce')
        ipo_years = df_temp[df_temp['IPO Year Numeric'].notna() & (df_temp['IPO Year Numeric'] > 0)]['IPO Year Numeric']
        
        if len(ipo_years) > 0:
            min_year = int(ipo_years.min())
            max_year = int(ipo_years.max())
            
            ipo_filter = st.sidebar.checkbox("Filter by IPO Year", key="ipo_checkbox")
            if ipo_filter:
                ipo_range = st.sidebar.slider(
                    "IPO Year Range",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year),
                    key="ipo_year_filter"
                )
    except Exception as e:
        # Skip IPO filter if there's an issue
        pass
    
    # Search
    search_term = st.sidebar.text_input("🔍 Search Companies", "", key="search_filter")
    
    st.sidebar.markdown("---")
    
    # Apply filters
    df_filtered = df.copy()
    
    if selected_firms:
        df_filtered = df_filtered[df_filtered['PE Firm'].isin(selected_firms)]
    
    if selected_statuses:
        df_filtered = df_filtered[df_filtered['Status'].isin(selected_statuses)]
    
    if selected_categories:
        df_filtered = df_filtered[df_filtered['Industry Category'].isin(selected_categories)]
    
    if selected_sectors:
        # For sectors, check if any selected sector is in the company's sector string
        mask = df_filtered['Sector'].apply(
            lambda x: any(sector.lower() in str(x).lower() for sector in selected_sectors) if pd.notna(x) else False
        )
        df_filtered = df_filtered[mask]
    
    if selected_ownership:
        df_filtered = df_filtered[df_filtered['Ownership Status'].isin(selected_ownership)]
    
    if public_filter == "Public Only":
        df_filtered = df_filtered[df_filtered['Is Public'] == True]
    elif public_filter == "Private Only":
        df_filtered = df_filtered[df_filtered['Is Public'] != True]
    
    if 'ipo_checkbox' in st.session_state and st.session_state.ipo_checkbox:
        if 'ipo_year_filter' in st.session_state:
            ipo_range = st.session_state.ipo_year_filter
            # Convert to numeric for comparison
            df_filtered['IPO Year Numeric'] = pd.to_numeric(df_filtered['IPO Year'], errors='coerce')
            df_filtered = df_filtered[
                (df_filtered['IPO Year Numeric'] >= ipo_range[0]) & 
                (df_filtered['IPO Year Numeric'] <= ipo_range[1])
            ]
    
    if search_term:
        df_filtered = df_filtered[
            df_filtered['Company'].str.contains(search_term, case=False, na=False) |
            df_filtered['Description'].str.contains(search_term, case=False, na=False) |
            df_filtered['Industry'].str.contains(search_term, case=False, na=False)
        ]
    
    # Show active filters
    active_filters = []
    if selected_firms:
        active_filters.append(f"PE Firms: {len(selected_firms)}")
    if selected_statuses:
        active_filters.append(f"Status: {len(selected_statuses)}")
    if selected_categories:
        active_filters.append(f"Categories: {len(selected_categories)}")
    if selected_sectors:
        active_filters.append(f"Sectors: {len(selected_sectors)}")
    if selected_ownership:
        active_filters.append(f"Ownership: {len(selected_ownership)}")
    if public_filter != "All":
        active_filters.append(f"Type: {public_filter}")
    if 'ipo_checkbox' in st.session_state and st.session_state.ipo_checkbox:
        active_filters.append("IPO Year Range")
    if search_term:
        active_filters.append(f"Search: '{search_term}'")
    
    if active_filters:
        st.sidebar.markdown("### 🔍 Active Filters")
        for f in active_filters:
            st.sidebar.caption(f"✓ {f}")
        st.sidebar.markdown("---")
    
    # Export in sidebar
    st.sidebar.markdown("### 📥 Export")
    csv = df_filtered.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Download Filtered Data",
        data=csv,
        file_name=f"portfolio_export_{len(df_filtered)}_companies.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.sidebar.caption(f"{len(df_filtered)} companies selected")
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Companies", len(df_filtered))
    
    with col2:
        active_count = len(df_filtered[df_filtered['Status'] == 'Active'])
        st.metric("Active", active_count)
    
    with col3:
        exited_count = len(df_filtered[df_filtered['Status'] == 'Exit'])
        st.metric("Exited", exited_count)
    
    with col4:
        public_count = len(df_filtered[df_filtered['Is Public'] == True])
        st.metric("Public", public_count)
    
    with col5:
        acquired_count = len(df_filtered[df_filtered['Is Acquired'] == True])
        st.metric("Acquired", acquired_count)
    
    with col6:
        industries_count = df_filtered['Industry'].nunique()
        st.metric("Industries", industries_count)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "💰 Financial Analytics", "📋 Company List", "🔍 Company Profile"])
    
    with tab1:
        st.subheader("Portfolio Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            st.markdown("#### Status Distribution")
            status_counts = df_filtered['Status'].value_counts()
            
            colors = {'Active': '#2ecc71', 'Exit': '#e74c3c', 'Unknown': '#95a5a6'}
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color=status_counts.index,
                color_discrete_map=colors,
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top industries
            st.markdown("#### Top 10 Industries")
            industry_counts = df_filtered[df_filtered['Industry'] != '']['Industry'].value_counts().head(10)
            
            fig = px.bar(
                x=industry_counts.values,
                y=industry_counts.index,
                orientation='h',
                color=industry_counts.values,
                color_continuous_scale='Blues',
                labels={'x': 'Count', 'y': 'Industry'}
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Ownership breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ownership Status")
            ownership_counts = df_filtered[df_filtered['Ownership Status'] != '']['Ownership Status'].value_counts()
            
            if len(ownership_counts) > 0:
                fig = px.bar(
                    x=ownership_counts.index,
                    y=ownership_counts.values,
                    color=ownership_counts.values,
                    color_continuous_scale='Viridis',
                    labels={'x': 'Status', 'y': 'Count'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No ownership data available")
        
        with col2:
            st.markdown("#### Public vs Private")
            public_counts = df_filtered['Is Public'].value_counts()
            
            fig = px.pie(
                values=public_counts.values,
                names=['Private' if not x else 'Public' for x in public_counts.index],
                color_discrete_map={'Public': '#3498db', 'Private': '#95a5a6'},
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Financial Analytics")
        
        # Market Cap distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Companies by Market Cap")
            df_mcap = df_filtered[df_filtered['Market Cap'].notna() & (df_filtered['Market Cap'] > 0)].copy()
            df_mcap = df_mcap.sort_values('Market Cap', ascending=False).head(15)
            
            if len(df_mcap) > 0:
                df_mcap['Market Cap Display'] = df_mcap['Market Cap'].apply(
                    lambda x: x / 1_000_000_000
                )
                
                fig = px.bar(
                    df_mcap,
                    x='Market Cap Display',
                    y='Company',
                    orientation='h',
                    color='Market Cap Display',
                    color_continuous_scale='Greens',
                    labels={'Market Cap Display': 'Market Cap ($B)'}
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No market cap data available")
        
        with col2:
            st.markdown("#### Top Companies by Total Funding")
            df_funding = df_filtered[df_filtered['Total Funding'].notna() & (df_filtered['Total Funding'] > 0)].copy()
            df_funding = df_funding.sort_values('Total Funding', ascending=False).head(15)
            
            if len(df_funding) > 0:
                df_funding['Funding Display'] = df_funding['Total Funding'].apply(
                    lambda x: x / 1_000_000_000 if x >= 1_000_000_000 else x / 1_000_000
                )
                df_funding['Unit'] = df_funding['Total Funding'].apply(
                    lambda x: 'B' if x >= 1_000_000_000 else 'M'
                )
                
                fig = px.bar(
                    df_funding,
                    x='Funding Display',
                    y='Company',
                    orientation='h',
                    color='Funding Display',
                    color_continuous_scale='Blues',
                    labels={'Funding Display': 'Total Funding ($M)'}
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No funding data available")
        
        # IPO Timeline
        st.markdown("#### IPO Timeline")
        df_ipo = df_filtered.copy()
        df_ipo['IPO Year Numeric'] = pd.to_numeric(df_ipo['IPO Year'], errors='coerce')
        df_ipo = df_ipo[df_ipo['IPO Year Numeric'].notna()]
        
        if len(df_ipo) > 0:
            ipo_counts = df_ipo['IPO Year Numeric'].value_counts().sort_index()
            
            fig = px.bar(
                x=ipo_counts.index.astype(int),
                y=ipo_counts.values,
                color=ipo_counts.values,
                color_continuous_scale='Purples',
                labels={'x': 'Year', 'y': 'Number of IPOs'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # IPO companies table
            st.markdown("#### Recent IPOs")
            df_ipo_display = df_ipo[['Company', 'PE Firm', 'Industry', 'IPO Year Numeric', 'Stock Exchange', 'Market Cap']].copy()
            df_ipo_display.rename(columns={'IPO Year Numeric': 'IPO Year'}, inplace=True)
            df_ipo_display['IPO Year'] = df_ipo_display['IPO Year'].astype(int)
            df_ipo_display['Market Cap'] = df_ipo_display['Market Cap'].apply(format_currency)
            df_ipo_display = df_ipo_display.sort_values('IPO Year', ascending=False).head(20)
            st.dataframe(df_ipo_display, use_container_width=True, hide_index=True)
        else:
            st.info("No IPO data available")
    
    with tab3:
        st.subheader(f"📋 Company List ({len(df_filtered)} companies)")
        
        # Display options
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            items_per_page = st.selectbox("Items per page", [25, 50, 100, 200], index=0)
        with col3:
            sort_by = st.selectbox("Sort by", ["Company", "Industry", "Market Cap", "Total Funding", "Status"])
        
        # Sort data
        if sort_by == "Market Cap":
            df_filtered = df_filtered.sort_values('Market Cap', ascending=False, na_position='last')
        elif sort_by == "Total Funding":
            df_filtered = df_filtered.sort_values('Total Funding', ascending=False, na_position='last')
        else:
            df_filtered = df_filtered.sort_values(sort_by)
        
        # Pagination
        total_pages = (len(df_filtered) - 1) // items_per_page + 1
        page = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1)
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        # Prepare display dataframe
        df_display = df_filtered.copy()
        df_display['Market Cap Display'] = df_display['Market Cap'].apply(format_currency)
        df_display['Total Funding Display'] = df_display['Total Funding'].apply(format_currency)
        
        # Select columns to display (no duplicate Ownership Status)
        display_cols = ['Company', 'PE Firm', 'Industry', 'Status', 'Headquarters', 'Market Cap Display', 'Total Funding Display']
        
        # Rename for display
        df_display_final = df_display[display_cols].copy()
        df_display_final.rename(columns={
            'Market Cap Display': 'Market Cap',
            'Total Funding Display': 'Total Funding'
        }, inplace=True)
        
        st.dataframe(
            df_display_final.iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(df_filtered))} of {len(df_filtered)} companies")
    
    with tab4:
        st.subheader("🔍 Company Profile")
        
        # Company selector
        company_names = sorted(df_filtered['Company'].unique().tolist())
        
        if company_names:
            selected_company = st.selectbox("Select a company", company_names, key="company_profile_select")
            
            if selected_company:
                company = df_filtered[df_filtered['Company'] == selected_company].iloc[0]
                
                # Company header
                st.markdown(f'<div class="company-name">{company["Company"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="company-subtitle">{company["Industry"]} • {company["PE Firm"]}</div>', unsafe_allow_html=True)
                
                # Status badges
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if company['Status'] == 'Active':
                        st.success("✅ Active Portfolio")
                    else:
                        st.error("❌ Exited")
                
                with col2:
                    if company['Is Public']:
                        st.info(f"📈 Public Company")
                    else:
                        st.info("🔒 Private Company")
                
                with col3:
                    if company['Is Acquired']:
                        st.warning("🤝 Acquired")
                
                with col4:
                    if pd.notna(company['IPO Year']) and company['IPO Year'] not in ['', 0]:
                        try:
                            ipo_year = int(float(company['IPO Year']))
                            st.success(f"🎉 IPO {ipo_year}")
                        except (ValueError, TypeError):
                            pass
                
                st.markdown("---")
                
                # Basic Information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📍 Basic Information")
                    st.markdown(f"**Sector:** {company['Sector'] or 'N/A'}")
                    st.markdown(f"**Industry:** {company['Industry'] or 'N/A'}")
                    st.markdown(f"**Headquarters:** {company['Headquarters'] or 'N/A'}")
                    st.markdown(f"**Founded:** {company['Founded'] or 'N/A'}")
                    if company['Website']:
                        st.markdown(f"**Website:** [{company['Website']}]({company['Website']})")
                
                with col2:
                    st.markdown("#### 💼 Company Size & Revenue")
                    # Decode revenue range for display
                    revenue_display = "N/A"
                    if company['Revenue Range']:
                        revenue_codes = {
                            "r_00000000": "< $1M",
                            "r_00001000": "$1M - $10M",
                            "r_00010000": "$10M - $50M",
                            "r_00050000": "$50M - $100M",
                            "r_00100000": "$100M - $500M",
                            "r_00500000": "$500M - $1B",
                            "r_01000000": "$1B - $10B",
                            "r_10000000": "$10B+"
                        }
                        revenue_display = revenue_codes.get(company['Revenue Range'], company['Revenue Range'])
                    
                    # Decode employee count for display
                    employee_display = "N/A"
                    if company['Employee Count']:
                        employee_codes = {
                            "c_00001_00010": "1-10",
                            "c_00011_00050": "11-50",
                            "c_00051_00100": "51-100",
                            "c_00101_00250": "101-250",
                            "c_00251_00500": "251-500",
                            "c_00501_01000": "501-1,000",
                            "c_01001_05000": "1,001-5,000",
                            "c_05001_10000": "5,001-10,000",
                            "c_10001_max": "10,001+"
                        }
                        employee_display = employee_codes.get(company['Employee Count'], company['Employee Count'])
                    
                    st.markdown(f"**Revenue Range:** {revenue_display}")
                    st.markdown(f"**Employee Count:** {employee_display}")
                    st.markdown(f"**Status:** {company['Status']}")
                    st.markdown(f"**Ownership Status:** {company['Ownership Status'] or 'N/A'}")
                    st.markdown(f"**Customer Types:** {company['Customer Types'] or 'N/A'}")
                
                # Financial Information
                st.markdown("#### 💰 Financial Information")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Market Cap", format_currency(company['Market Cap']))
                
                with col2:
                    st.metric("Total Funding", format_currency(company['Total Funding']))
                
                with col3:
                    if company['Last Round Type']:
                        st.metric("Last Round", company['Last Round Type'])
                    else:
                        st.metric("Last Round", "N/A")
                
                with col4:
                    st.metric("Last Round Amount", format_currency(company['Last Round Amount']))
                
                # IPO Information
                if company['IPO Year'] or company['Stock Exchange']:
                    st.markdown("#### 📈 IPO Information")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        ipo_year_display = 'N/A'
                        if pd.notna(company['IPO Year']):
                            try:
                                ipo_year_display = int(float(company['IPO Year']))
                            except (ValueError, TypeError):
                                ipo_year_display = str(company['IPO Year'])
                        st.markdown(f"**IPO Year:** {ipo_year_display}")
                    
                    with col2:
                        st.markdown(f"**IPO Date:** {company['IPO Date'] or 'N/A'}")
                    
                    with col3:
                        st.markdown(f"**Stock Exchange:** {company['Stock Exchange'] or 'N/A'}")
                
                # Description
                if company['Description']:
                    st.markdown("#### 📄 Description")
                    st.write(company['Description'])
                
                # Summary (from Swarm)
                if company['Summary']:
                    st.markdown("#### 📊 Company Summary")
                    st.info(company['Summary'])
                
                # Exit Info
                if company['Exit Info']:
                    st.markdown("#### 🚪 Exit Information")
                    st.warning(company['Exit Info'])
        else:
            st.info("No companies found with the current filters")


if __name__ == "__main__":
    main()
