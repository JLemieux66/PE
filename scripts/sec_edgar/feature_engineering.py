"""
Shared feature engineering for revenue prediction
Used by both training (train_sec_model.py) and prediction (predict_all_companies.py)
"""
import pandas as pd
import numpy as np


# Industry/Sector mapping
SECTOR_MAPPING = {
    # Yahoo Finance sectors -> Portfolio categories
    'Technology': 'Technology & Software',
    'Financial Services': 'Finance & Insurance',
    'Healthcare': 'Healthcare & Biotech',
    'Consumer Cyclical': 'E-commerce & Retail',
    'Consumer Defensive': 'E-commerce & Retail',
    'Industrials': 'Manufacturing & Industrial',
    'Communication Services': 'Technology & Software',
    'Real Estate': 'Real Estate & Construction',
    'Utilities': 'Energy & Sustainability',
    'Basic Materials': 'Manufacturing & Industrial',
    'Energy': 'Energy & Sustainability',
}

# Revenue per employee benchmarks by industry (approximate)
INDUSTRY_EFFICIENCY = {
    'Technology & Software': 500000,
    'Finance & Insurance': 400000,
    'Healthcare & Biotech': 350000,
    'Manufacturing & Industrial': 300000,
    'Energy & Sustainability': 800000,
    'E-commerce & Retail': 250000,
    'Real Estate & Construction': 300000,
    'Professional Services': 200000,
    'Education & HR': 150000,
    'Media & Entertainment': 350000,
    'Transportation & Automotive': 400000,
    'Legal & Compliance': 250000,
    'Marketing & Advertising': 200000,
    'Agriculture & Food': 300000,
    'Artificial Intelligence & Data': 600000,
}


def engineer_features(df):
    """
    Engineer features from raw company data
    
    Args:
        df: DataFrame with columns: employees, assets, sector (optional), industry_category (optional), country (optional)
        
    Returns:
        DataFrame with engineered features
    """
    df = df.copy()
    
    # Ensure employees is numeric
    df['employees'] = pd.to_numeric(df['employees'], errors='coerce').fillna(50)
    
    # Log transforms (handle zeros and negatives)
    df['log_employees'] = np.log1p(df['employees'])
    df['log_assets'] = np.log1p(df['assets'].fillna(0) if 'assets' in df.columns else 0)
    
    # Asset-based features
    if 'assets' in df.columns:
        df['has_assets_data'] = (df['assets'].notna() & (df['assets'] > 0)).astype(int)
    else:
        df['has_assets_data'] = 0
    
    # Employee-based features
    df['is_large_company'] = (df['employees'] >= 1000).astype(int)
    
    # Company size categories
    df['size_Small'] = (df['employees'] < 100).astype(int)
    df['size_Medium'] = ((df['employees'] >= 100) & (df['employees'] < 500)).astype(int)
    df['size_Large'] = ((df['employees'] >= 500) & (df['employees'] < 1000)).astype(int)
    df['size_Enterprise'] = (df['employees'] >= 1000).astype(int)
    
    # Industry/Sector features
    if 'sector' in df.columns:
        # Map Yahoo Finance sectors to portfolio categories
        df['industry_category'] = df['sector'].map(SECTOR_MAPPING).fillna('Other')
    
    if 'industry_category' in df.columns:
        # One-hot encode top industries
        top_industries = [
            'Technology & Software',
            'Healthcare & Biotech',
            'Finance & Insurance',
            'E-commerce & Retail',
            'Manufacturing & Industrial',
            'Energy & Sustainability'
        ]
        
        for industry in top_industries:
            col_name = f'industry_{industry.replace(" & ", "_").replace(" ", "_")}'
            df[col_name] = (df['industry_category'] == industry).astype(int)
        
        # Get expected revenue per employee for industry
        df['industry_efficiency'] = df['industry_category'].map(INDUSTRY_EFFICIENCY).fillna(300000)
        df['expected_revenue_estimate'] = df['employees'] * df['industry_efficiency']
        df['log_expected_revenue'] = np.log1p(df['expected_revenue_estimate'])
    else:
        # Default industry features if not available
        df['industry_efficiency'] = 300000
        df['expected_revenue_estimate'] = df['employees'] * 300000
        df['log_expected_revenue'] = np.log1p(df['expected_revenue_estimate'])
        for industry in ['Technology & Software', 'Healthcare & Biotech', 'Finance & Insurance', 
                        'E-commerce & Retail', 'Manufacturing & Industrial', 'Energy & Sustainability']:
            col_name = f'industry_{industry.replace(" & ", "_").replace(" ", "_")}'
            df[col_name] = 0
    
    # Location features
    if 'country' in df.columns:
        df['is_us'] = (df['country'] == 'United States').astype(int)
        df['is_developed_market'] = df['country'].isin([
            'United States', 'United Kingdom', 'Canada', 'Germany', 
            'France', 'Japan', 'Australia', 'Switzerland', 'Netherlands'
        ]).astype(int)
    else:
        df['is_us'] = 0
        df['is_developed_market'] = 0
    
    # Public company feature (if available)
    if 'is_public' in df.columns:
        df['is_public_flag'] = df['is_public'].fillna(False).astype(int)
    else:
        df['is_public_flag'] = 0
    
    return df


def prepare_model_features(df_features):
    """
    Select and prepare final features for model
    ONLY includes features available at prediction time (no revenue-derived features!)
    
    Returns:
        X: Feature matrix
        y: Target (if 'revenue_category' exists, else None)
        feature_names: List of feature column names
    """
    # Core numeric features - NO revenue-derived features
    feature_cols = [
        'employees',
        'log_employees',
        'log_assets',
        'has_assets_data',
        'is_large_company',
        'industry_efficiency',
        'expected_revenue_estimate',
        'log_expected_revenue',
        'is_us',
        'is_developed_market',
        'is_public_flag'
    ]
    
    # Size category one-hot features
    size_cols = ['size_Small', 'size_Medium', 'size_Large', 'size_Enterprise']
    feature_cols.extend(size_cols)
    
    # Industry one-hot features
    industry_cols = [
        'industry_Technology_Software',
        'industry_Healthcare_Biotech',
        'industry_Finance_Insurance',
        'industry_E-commerce_Retail',
        'industry_Manufacturing_Industrial',
        'industry_Energy_Sustainability'
    ]
    feature_cols.extend(industry_cols)
    
    # Ensure all feature columns exist
    for col in feature_cols:
        if col not in df_features.columns:
            df_features[col] = 0
    
    X = df_features[feature_cols].fillna(0)
    
    # Target (if available)
    y = None
    if 'revenue_category' in df_features.columns:
        y = df_features['revenue_category'].values
    
    return X, y, feature_cols
