import streamlit as st
import pandas as pd
import datacompy
import plotly.express as px
from datetime import datetime
import requests
from io import BytesIO
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Function to generate professional PDF report
def generate_pdf_report(report_data, pdf_data_dict=None):
    """Generate a professional PDF report from comparison data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom professional styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#667eea'),
        borderPadding=8,
        backColor=colors.HexColor('#f0f0f0')
    )
    
    metric_style = ParagraphStyle(
        'Metric',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leftIndent=20
    )
    
    # Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Dataset Comparison Report", title_style))
    story.append(Paragraph("Professional Analysis Report", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(PageBreak())
    
    # Use structured data if available, otherwise parse text
    if pdf_data_dict:
        data = pdf_data_dict
    elif isinstance(report_data, dict):
        data = report_data
    else:
        # Parse text report to extract data
        data = {}
        lines = report_data.split('\n')
        for line in lines:
            if 'DataFrame A:' in line or 'df1' in line.lower():
                # Extract numbers
                import re
                nums = re.findall(r'\d+', line)
                if len(nums) >= 2:
                    data['total_rows_a'] = int(nums[0])
                    data['cols_a'] = int(nums[1])
            elif 'DataFrame B:' in line or 'df2' in line.lower():
                nums = re.findall(r'\d+', line)
                if len(nums) >= 2:
                    data['total_rows_b'] = int(nums[1])
                    data['cols_b'] = int(nums[2]) if len(nums) > 2 else 0
    
    # Executive Summary Section
    story.append(Paragraph("Executive Summary", heading_style))
    summary_data = [
        ['Metric', 'Dataset A', 'Dataset B'],
        ['Total Rows', str(data.get('total_rows_a', 0)), str(data.get('total_rows_b', 0))],
        ['Total Columns', str(data.get('cols_a', 0)), str(data.get('cols_b', 0))],
        ['Common Columns', str(data.get('common_cols', 0)), str(data.get('common_cols', 0))],
    ]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Comparison Results Section
    story.append(Paragraph("Comparison Results", heading_style))
    results_data = [
        ['Metric', 'Value', 'Percentage'],
        ['Matching Rows', str(data.get('matched_rows', 0)), 
         f"{(data.get('matched_rows', 0) / data.get('total_rows_a', 1) * 100):.1f}%" if data.get('total_rows_a', 0) > 0 else "0%"],
        ['Rows Only in A', str(data.get('unq_a', 0)), 
         f"{(data.get('unq_a', 0) / data.get('total_rows_a', 1) * 100):.1f}%" if data.get('total_rows_a', 0) > 0 else "0%"],
        ['Rows Only in B', str(data.get('unq_b', 0)), 
         f"{(data.get('unq_b', 0) / data.get('total_rows_b', 1) * 100):.1f}%" if data.get('total_rows_b', 0) > 0 else "0%"],
        ['Mismatched Rows', str(data.get('mismatch_count', 0)), 
         f"{(data.get('mismatch_count', 0) / data.get('merged_rows', 1) * 100):.1f}%" if data.get('merged_rows', 0) > 0 else "0%"],
        ['Rows in Common', str(data.get('merged_rows', 0)), 
         f"{(data.get('merged_rows', 0) / max(data.get('total_rows_a', 1), data.get('total_rows_b', 1)) * 100):.1f}%"],
    ]
    results_table = Table(results_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Key Columns Section
    if data.get('resolved_join'):
        story.append(Paragraph("Key Columns Used for Comparison", heading_style))
        story.append(Paragraph(f"<b>Join Columns:</b> {', '.join(data.get('resolved_join', []))}", metric_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Detailed Analysis Section
    story.append(Paragraph("Detailed Analysis", heading_style))
    story.append(Paragraph(f"<b>Columns Compared:</b> {data.get('compared_cols', 0)}", metric_style))
    story.append(Paragraph(f"<b>Common Columns:</b> {data.get('common_cols', 0)}", metric_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Add full text report if available
    if not isinstance(report_data, dict) and report_data:
        story.append(Paragraph("Full Comparison Report", heading_style))
        lines = report_data.split('\n')
        for line in lines[:50]:  # Limit to first 50 lines to avoid huge PDFs
            if line.strip() and not line.startswith('---'):
                story.append(Paragraph(line[:100], styles['Normal']))  # Limit line length
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("<i>... (report truncated for brevity) ...</i>", styles['Italic']))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("─" * 80, styles['Normal']))
    story.append(Paragraph(f"<i>Report generated by Dataset Analyzer Pro on {datetime.now().strftime('%B %d, %Y')}</i>", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Page configuration
st.set_page_config(
    page_title="✨ Dataset Analyzer Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Creative Custom CSS
st.markdown("""
<style>
    /* Main app styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    h1 {
        color: #667eea !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    h2, h3 {
        color: #764ba2 !important;
        font-weight: 600 !important;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #667eea !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    /* Success message */
    .stSuccess {
        background-color: #d4edda !important;
        color: #155724 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Error boxes */
    .stError {
        background-color: #f8d7da !important;
        color: #721c24 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: #fff3cd !important;
        color: #856404 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #d1ecf1 !important;
        color: #0c5460 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Tabs styling */
    [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: rgba(102, 126, 234, 0.1) !important;
        border-radius: 10px !important;
        padding: 5px !important;
    }
    
    [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 10px 20px !important;
        background: rgba(255, 255, 255, 0.5) !important;
        color: #333 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
    }
    
    [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-bottom: 2px solid #667eea !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f0f2f6 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* Code blocks */
    [data-testid="stCodeBlock"] {
        border-radius: 8px !important;
        background: #f6f8fa !important;
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #e9ecef !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔍 Dataset Analyzer Pro")
st.markdown("### Compare, Analyze, and Visualize Your Data")

# Sidebar
with st.sidebar:
    # Try to load the Streamlit logo from the web; if it fails (network or blocked),
    # fall back to a simple text header to avoid client-side image errors.
    logo_url = "https://raw.githubusercontent.com/streamlit/docs/main/public/logos/streamlit-mark-color.png"
    try:
        resp = requests.get(logo_url, timeout=3)
        if resp.status_code == 200 and resp.content:
            st.image(BytesIO(resp.content), width=100)
        else:
            st.markdown("### Dataset Analyzer Pro")
    except Exception:
        st.markdown("### Dataset Analyzer Pro")
    st.header("Settings")
    tolerance = st.slider("Numerical Tolerance", 0.0, 1.0, 0.0, 0.01)
    show_viz = st.checkbox("Show Visualizations", True)

# Main content
col1, col2 = st.columns(2)

with col1:
    st.info("📊 Dataset A")
    file_a = st.file_uploader("Upload your first dataset", type=["csv"])
    if file_a:
        df_a = pd.read_csv(file_a, low_memory=False)
        with st.expander("Preview Dataset A", expanded=True):
            st.dataframe(df_a.head(), use_container_width=True)
            st.caption(f"Total rows: {len(df_a)} | Total columns: {len(df_a.columns)}")

            # Quick stats for numeric columns
            num_cols = df_a.select_dtypes(include=['int64', 'float64']).columns
            if len(num_cols) > 0 and show_viz:
                col_to_viz = st.selectbox("Select column to visualize (Dataset A)", num_cols, key="viz_a_select")
                fig = px.histogram(df_a, x=col_to_viz, title=f"Distribution of {col_to_viz}")
                st.plotly_chart(fig, use_container_width=True, key="viz_a_chart")

with col2:
    st.info("📈 Dataset B")
    file_b = st.file_uploader("Upload your second dataset", type=["csv"])
    if file_b:
        df_b = pd.read_csv(file_b, low_memory=False)
        with st.expander("Preview Dataset B", expanded=True):
            st.dataframe(df_b.head(), use_container_width=True)
            st.caption(f"Total rows: {len(df_b)} | Total columns: {len(df_b.columns)}")

            # Quick stats for numeric columns
            num_cols = df_b.select_dtypes(include=['int64', 'float64']).columns
            if len(num_cols) > 0 and show_viz:
                col_to_viz = st.selectbox("Select column to visualize (Dataset B)", num_cols, key="viz_b_select")
                fig = px.histogram(df_b, x=col_to_viz, title=f"Distribution of {col_to_viz}")
                st.plotly_chart(fig, use_container_width=True, key="viz_b_chart")

if file_a and file_b:
    st.markdown("---")
    st.header("🔄 Comparison Analysis")

    # Get common columns (exact match)
    common_cols = list(set(df_a.columns) & set(df_b.columns))
    
    # Find all matching columns (case-insensitive and space-insensitive)
    a_cols_normalized = {c.lower().strip().replace(' ', ''): c for c in df_a.columns}
    b_cols_normalized = {c.lower().strip().replace(' ', ''): c for c in df_b.columns}
    
    # Find all matches
    all_matches = []
    matched_keys = set()
    for norm_key in a_cols_normalized.keys():
        if norm_key in b_cols_normalized:
            matched_keys.add(norm_key)
            all_matches.append({
                'normalized': norm_key,
                'in_a': a_cols_normalized[norm_key],
                'in_b': b_cols_normalized[norm_key],
                'exact_match': a_cols_normalized[norm_key] == b_cols_normalized[norm_key]
            })
    
    # Display matching columns
    if all_matches:
        st.success(f"✅ Found {len(all_matches)} matching column(s) between datasets")
        with st.expander("📋 View All Matching Column Names", expanded=True):
            # Create a DataFrame to display matches
            matches_df = pd.DataFrame(all_matches)
            matches_df['Match Type'] = matches_df['exact_match'].apply(lambda x: '✅ Exact Match' if x else '🔄 Case/Space Variant')
            display_df = matches_df[['in_a', 'in_b', 'Match Type']].copy()
            display_df.columns = ['Column Name in Dataset A', 'Column Name in Dataset B', 'Match Type']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            exact_matches = matches_df[matches_df['exact_match']].shape[0]
            variant_matches = matches_df[~matches_df['exact_match']].shape[0]
            st.caption(f"📊 Summary: {exact_matches} exact matches, {variant_matches} case/space variants")
    else:
        st.warning("⚠ No matching columns found (even with case/space normalization)")

    if not common_cols and not all_matches:
        st.error("❌ No common columns found between the datasets!")
        st.info("💡 Tip: Make sure your datasets have at least one column with matching names.")
    else:
        # Column selection
        col1, col2 = st.columns([2, 1])
        with col1:
            # Use all matches for selection, not just exact matches
            available_cols = [m['in_a'] for m in all_matches] if all_matches else common_cols
            join_cols = st.multiselect(
                "🔑 Select Key Columns for Comparison",
                available_cols,
                default=[available_cols[0]] if available_cols else []
            )

        with col2:
            st.info(f"📝 {len(common_cols)} exact common columns\n🔄 {len(all_matches)} total matches")

        if not join_cols:
            st.warning("⚠ Please select at least one key column to begin comparison")
        elif join_cols:
            # Prepare DataFrames for comparison
            df_a_prep = df_a.copy()
            df_b_prep = df_b.copy()
            
            # Show selected columns
            st.info(f"✅ Selected {len(join_cols)} key column(s) for comparison: {', '.join(join_cols)}")
            
            try:
                # Resolve join columns: use the matching information we already found
                resolved_join = []
                missing_keys = []
                
                # Create a mapping from normalized names to actual column names
                a_cols_lower = {c.lower().strip().replace(' ', ''): c for c in df_a_prep.columns}
                b_cols_lower = {c.lower().strip().replace(' ', ''): c for c in df_b_prep.columns}
                
                # Create a lookup from Dataset A column names to their matches in Dataset B
                match_lookup = {m['in_a']: m['in_b'] for m in all_matches}

                for key in join_cols:
                    # Check if key exists exactly in both dataframes
                    if key in df_a_prep.columns and key in df_b_prep.columns:
                        # Exact match - use as is
                        resolved_join.append(key)
                    elif key in match_lookup:
                        # Key is from Dataset A, get its match in Dataset B
                        col_in_a = key
                        col_in_b = match_lookup[key]
                        
                        # Verify columns exist before renaming
                        if col_in_a not in df_a_prep.columns:
                            missing_keys.append(f"{key} (not found in Dataset A as '{col_in_a}')")
                            continue
                        if col_in_b not in df_b_prep.columns:
                            missing_keys.append(f"{key} (not found in Dataset B as '{col_in_b}')")
                            continue
                        
                        # Rename column in df_b_prep to match df_a_prep
                        if col_in_b != col_in_a:
                            df_b_prep.rename(columns={col_in_b: col_in_a}, inplace=True)
                            # Update mappings after rename
                            b_cols_lower = {c.lower().strip().replace(' ', ''): c for c in df_b_prep.columns}
                        
                        # Verify the column now exists in both after rename
                        if col_in_a in df_a_prep.columns and col_in_a in df_b_prep.columns:
                            resolved_join.append(col_in_a)
                        else:
                            missing_keys.append(f"{key} (failed to resolve)")
                    else:
                        # Try to find by normalization
                        key_norm = key.lower().strip().replace(' ', '')
                        a_match = a_cols_lower.get(key_norm)
                        b_match = b_cols_lower.get(key_norm)
                        
                        if a_match and b_match:
                            # Rename the column in df_b_prep to match df_a_prep
                            if b_match != a_match:
                                df_b_prep.rename(columns={b_match: a_match}, inplace=True)
                                # Update the lowercase mapping after rename
                                b_cols_lower = {c.lower().strip().replace(' ', ''): c for c in df_b_prep.columns}
                            resolved_join.append(a_match)
                        else:
                            missing_keys.append(key)

                if missing_keys and not resolved_join:
                    # Only show error if we have no resolved columns at all
                    st.error(f"❌ Key column(s) not found in both datasets: {', '.join(missing_keys)}")
                    st.stop()
                elif missing_keys:
                    # Some columns failed but we have some resolved - show warning but continue
                    st.warning(f"⚠ Some columns could not be resolved: {', '.join(missing_keys)}")
                    st.info(f"✅ Using resolved columns: {', '.join(resolved_join)}")

                # Recalculate common columns after renaming
                common_cols = list(set(df_a_prep.columns) & set(df_b_prep.columns))

                # Verify all resolved_join columns exist in both dataframes after renaming
                final_missing = []
                verified_join = []
                for col in resolved_join:
                    if col in df_a_prep.columns and col in df_b_prep.columns:
                        verified_join.append(col)
                    else:
                        if col not in df_a_prep.columns:
                            final_missing.append(f"'{col}' missing in Dataset A")
                        if col not in df_b_prep.columns:
                            final_missing.append(f"'{col}' missing in Dataset B")
                
                # Update resolved_join with verified columns
                if verified_join:
                    resolved_join = verified_join
                
                if final_missing and not verified_join:
                    st.error(f"❌ Join column verification failed: {', '.join(final_missing)}")
                    st.error("No valid join columns found!")
                    st.stop()
                
                # Convert join columns to string to prevent merge/datacompy errors
                for col in resolved_join:
                    if col in df_a_prep.columns:
                        df_a_prep[col] = df_a_prep[col].fillna('').astype(str).str.strip()
                    if col in df_b_prep.columns:
                        df_b_prep[col] = df_b_prep[col].fillna('').astype(str).str.strip()

                # Convert all other columns to string to ensure consistent comparison
                for col in df_a_prep.columns:
                    if col not in resolved_join:
                        df_a_prep[col] = df_a_prep[col].fillna('').astype(str).str.strip()
                for col in df_b_prep.columns:
                    if col not in resolved_join:
                        df_b_prep[col] = df_b_prep[col].fillna('').astype(str).str.strip()

                # Create comparison
                try:
                    comp = datacompy.Compare(
                        df_a_prep,
                        df_b_prep,
                        join_columns=resolved_join,
                        abs_tol=tolerance,
                        rel_tol=tolerance,
                        ignore_spaces=True,
                        ignore_case=True
                    )
                    comp_created = True
                except Exception as comp_error:
                    comp = None
                    comp_created = False

                # Results in cards - ALWAYS DISPLAY THIS SECTION
                st.markdown("### 📊 Comparison Results")
                c1, c2, c3, c4, c5 = st.columns(5)

                # Basic statistics
                total_rows_a = len(df_a_prep)
                total_rows_b = len(df_b_prep)

                # Calculate unique rows silently
                unq_a = 0
                unq_b = 0
                
                if resolved_join:
                    # Verify all resolved_join columns exist in both dataframes
                    valid_cols = [col for col in resolved_join if col in df_a_prep.columns and col in df_b_prep.columns]
                    
                    if valid_cols:
                        try:
                            if len(valid_cols) == 1:
                                # Single key column
                                key_col = valid_cols[0]
                                keys_a = set(df_a_prep[key_col].fillna('').astype(str).str.strip())
                                keys_b = set(df_b_prep[key_col].fillna('').astype(str).str.strip())
                            else:
                                # Multiple key columns - create tuples
                                df_a_keys = df_a_prep[valid_cols].fillna('').astype(str)
                                df_b_keys = df_b_prep[valid_cols].fillna('').astype(str)
                                keys_a = set(df_a_keys.apply(lambda x: tuple(v.strip() for v in x), axis=1))
                                keys_b = set(df_b_keys.apply(lambda x: tuple(v.strip() for v in x), axis=1))
                            
                            # Calculate unique rows
                            unq_a_keys = keys_a - keys_b
                            unq_b_keys = keys_b - keys_a
                            unq_a = len(unq_a_keys)
                            unq_b = len(unq_b_keys)
                        except Exception:
                            # Fallback: use merge to find unique rows
                            try:
                                merged_all = df_a_prep.merge(df_b_prep, on=valid_cols, how='outer', indicator=True, suffixes=('_a', '_b'))
                                unq_a = len(merged_all[merged_all['_merge'] == 'left_only'])
                                unq_b = len(merged_all[merged_all['_merge'] == 'right_only'])
                            except Exception:
                                unq_a = 0
                                unq_b = 0

                # Build an inner-joined DataFrame on the resolved key columns to compare matched rows
                merged = pd.DataFrame()  # Initialize as empty
                
                merge_cols = [col for col in resolved_join if col in df_a_prep.columns and col in df_b_prep.columns]
                
                if merge_cols:
                    try:
                        merged = df_a_prep.merge(
                            df_b_prep,
                            on=merge_cols,
                            how='inner',
                            suffixes=("_a", "_b")
                        )
                    except Exception:
                        pass

                # Columns to compare (exclude join/key columns)
                compared_cols = [c for c in common_cols if c not in resolved_join]

                # Compute per-row mismatches
                mismatch_count = 0
                matched_rows = merged.shape[0]
                mismatched_preview = None
                
                if len(compared_cols) > 0 and matched_rows > 0:
                    mismatch_series = pd.Series(False, index=merged.index)

                    for col in compared_cols:
                        try:
                            col_a = f"{col}_a"
                            col_b = f"{col}_b"
                            if col_a not in merged.columns or col_b not in merged.columns:
                                continue

                            a_vals = merged[col_a]
                            b_vals = merged[col_b]

                            # Compare as strings
                            a_str = a_vals.where(a_vals.notna(), "").astype(str).str.strip().str.lower()
                            b_str = b_vals.where(b_vals.notna(), "").astype(str).str.strip().str.lower()
                            col_mismatch = ~(a_str == b_str)

                            mismatch_series = mismatch_series | col_mismatch.fillna(False)
                        except Exception:
                            continue

                    mismatch_count = int(mismatch_series.sum())
                    matched_rows = int((~mismatch_series).sum())

                    # Prepare preview DataFrame of mismatched rows
                    if mismatch_count > 0:
                        keys = resolved_join
                        cols_to_show = keys[:]
                        for c in compared_cols[:10]:
                            if f"{c}_a" in merged.columns and f"{c}_b" in merged.columns:
                                cols_to_show.extend([f"{c}_a", f"{c}_b"])
                        mismatched_preview = merged.loc[mismatch_series, cols_to_show].head(200)

                with c1:
                    match_percent = (matched_rows / total_rows_a * 100) if total_rows_a > 0 else 0
                    st.metric("Matching Rows", str(matched_rows), delta=f"{match_percent:.1f}%")
                with c2:
                    st.metric("Rows Only in A", str(unq_a))
                with c3:
                    st.metric("Rows Only in B", str(unq_b))
                with c4:
                    st.metric("Common Columns", str(len(common_cols)))
                with c5:
                    st.metric("Mismatched Rows", str(mismatch_count))

                # Add debug information in an expandable section
                with st.expander("🔍 Debug Information - Click to expand if results seem wrong", expanded=False):
                    col_debug1, col_debug2 = st.columns(2)
                    with col_debug1:
                        st.write("**Configuration**")
                        st.write(f"Join Columns: {resolved_join}")
                        st.write(f"Common Columns: {len(common_cols)} columns")
                        st.write(f"Compared Columns: {len(compared_cols)} columns")
                    with col_debug2:
                        st.write("**Data Status**")
                        st.write(f"Rows in A: {total_rows_a}")
                        st.write(f"Rows in B: {total_rows_b}")
                        st.write(f"Merged Rows: {merged.shape[0] if not merged.empty else 0}")
                    
                    st.write("**Columns in Prepared Data**")
                    col_debug3, col_debug4 = st.columns(2)
                    with col_debug3:
                        st.write("**Dataset A Columns:**")
                        st.write(list(df_a_prep.columns))
                    with col_debug4:
                        st.write("**Dataset B Columns:**")
                        st.write(list(df_b_prep.columns))
                    
                    if not merged.empty and matched_rows == 0 and len(compared_cols) > 0:
                        st.warning("⚠ Rows matched on keys but all have mismatches in compared columns. Check the sample below:")
                        sample_cols = resolved_join + [c for c in merged.columns[:6] if c not in resolved_join]
                        st.dataframe(merged[sample_cols].head(10), use_container_width=True)

                # Detailed Analysis
                tabs = st.tabs(["📝 Report", "🔍 Null Analysis", "📊 Column Stats", "🔎 Mismatches", "📋 Detailed Info"])

                with tabs[0]:
                    st.subheader("Comparison Report")
                    try:
                        if comp_created and comp is not None:
                            try:
                                report_text = comp.report()
                                st.code(report_text, language="text")
                            except Exception:
                                # Generate a simple report
                                simple_report = f"""
DataFrame Summary
-----------------
DataFrame A: {total_rows_a} rows, {len(df_a_prep.columns)} columns
DataFrame B: {total_rows_b} rows, {len(df_b_prep.columns)} columns

Row Summary
-----------
Matched on: {', '.join(resolved_join)}
Rows in common (matched on keys): {merged.shape[0] if not merged.empty else 0}
Rows only in A: {unq_a}
Rows only in B: {unq_b}
Rows with mismatched values: {mismatch_count}
Rows with all values matching: {matched_rows}

Column Summary
--------------
Common columns: {len(common_cols)}
Columns compared: {len(compared_cols)}
                                """
                                st.code(simple_report, language="text")
                        else:
                            # Generate a simple report when datacompy comparison failed
                            simple_report = f"""
DataFrame Summary
-----------------
DataFrame A: {total_rows_a} rows, {len(df_a_prep.columns)} columns
DataFrame B: {total_rows_b} rows, {len(df_b_prep.columns)} columns

Row Summary
-----------
Matched on: {', '.join(resolved_join)}
Rows in common (matched on keys): {merged.shape[0] if not merged.empty else 0}
Rows only in A: {unq_a}
Rows only in B: {unq_b}
Rows with mismatched values: {mismatch_count}
Rows with all values matching: {matched_rows}

Column Summary
--------------
Common columns: {len(common_cols)}
Columns compared: {len(compared_cols)}
                            """
                            st.code(simple_report, language="text")
                    except Exception as e:
                        st.error(f"Error in Report tab: {str(e)}")

                with tabs[1]:
                    st.subheader("Null Values Analysis")
                    try:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Dataset A - Null Values**")
                            null_a = df_a.isna().sum()
                            if null_a.sum() > 0:
                                st.warning("⚠ Null values found:")
                                st.dataframe(null_a[null_a > 0], use_container_width=True)
                            else:
                                st.success("✅ No null values in Dataset A")

                        with col2:
                            st.write("**Dataset B - Null Values**")
                            null_b = df_b.isna().sum()
                            if null_b.sum() > 0:
                                st.warning("⚠ Null values found:")
                                st.dataframe(null_b[null_b > 0], use_container_width=True)
                            else:
                                st.success("✅ No null values in Dataset B")
                    except Exception as e:
                        st.error(f"Error in Null Analysis tab: {str(e)}")

                with tabs[2]:
                    st.subheader("Column Statistics")
                    try:
                        # Statistical comparison of numeric columns
                        numeric_cols = list(set(df_a.select_dtypes(include=['int64', 'float64']).columns) &
                                         set(df_b.select_dtypes(include=['int64', 'float64']).columns))

                        if numeric_cols and show_viz:
                            selected_col = st.selectbox("Select column for statistical comparison", numeric_cols, key="stats_select")
                            col1, col2 = st.columns(2)

                            with col1:
                                title_a = "Distribution in Dataset A: " + selected_col
                                fig = px.box(df_a, y=selected_col, title=title_a)
                                st.plotly_chart(fig, use_container_width=True, key="stats_a_chart")

                            with col2:
                                title_b = "Distribution in Dataset B: " + selected_col
                                fig = px.box(df_b, y=selected_col, title=title_b)
                                st.plotly_chart(fig, use_container_width=True, key="stats_b_chart")
                        else:
                            if not numeric_cols:
                                st.info("ℹ No numeric columns found for statistical comparison")
                            elif not show_viz:
                                st.info("ℹ Visualizations are disabled in settings")
                    except Exception as e:
                        st.error(f"Error in Column Stats tab: {str(e)}")

                with tabs[3]:
                    st.subheader("Mismatched Rows")
                    try:
                        if mismatched_preview is not None and not mismatched_preview.empty:
                            st.write(f"Showing top {len(mismatched_preview)} mismatched rows (keys + compared columns)")
                            st.dataframe(mismatched_preview, use_container_width=True)
                            csv = mismatched_preview.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Mismatched Rows (CSV)",
                                data=csv,
                                file_name=f"mismatched_rows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("ℹ No mismatched rows detected or no matching rows to compare.")
                            st.write(f"Details: {matched_rows} matching rows with compared columns")
                    except Exception as e:
                        st.error(f"Error in Mismatches tab: {str(e)}")

                with tabs[4]:
                    st.subheader("Detailed Comparison Information")
                    try:
                        # Display detailed metrics
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("### Dataset Overview")
                            overview_data = {
                                'Metric': ['Total Rows', 'Total Columns', 'Data Types'],
                                'Dataset A': [total_rows_a, len(df_a_prep.columns), f"{len(df_a_prep.dtypes.unique())} unique"],
                                'Dataset B': [total_rows_b, len(df_b_prep.columns), f"{len(df_b_prep.dtypes.unique())} unique"]
                            }
                            overview_df = pd.DataFrame(overview_data)
                            st.dataframe(overview_df, use_container_width=True, hide_index=True)
                        
                        with col2:
                            st.write("### Comparison Summary")
                            summary_data = {
                                'Category': ['Key Columns', 'Common Columns', 'Compared Columns', 'Rows in Common'],
                                'Value': [len(resolved_join), len(common_cols), len(compared_cols), merged.shape[0] if not merged.empty else 0]
                            }
                            summary_df = pd.DataFrame(summary_data)
                            st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        st.divider()
                        
                        # Display column details
                        st.write("### Column Details")
                        col_details = {
                            'Column Name': common_cols,
                            'In Join': [col in resolved_join for col in common_cols],
                            'Type A': [str(df_a_prep[col].dtype) for col in common_cols],
                            'Type B': [str(df_b_prep[col].dtype) for col in common_cols]
                        }
                        col_details_df = pd.DataFrame(col_details)
                        st.dataframe(col_details_df, use_container_width=True, hide_index=True)
                        
                        st.divider()
                        
                        # Row analysis
                        st.write("### Row Analysis")
                        row_analysis = {
                            'Metric': ['Total Rows A', 'Total Rows B', 'Rows Only in A', 'Rows Only in B', 
                                      'Rows in Common', 'Matching Rows', 'Mismatched Rows'],
                            'Count': [total_rows_a, total_rows_b, unq_a, unq_b, 
                                     merged.shape[0] if not merged.empty else 0, matched_rows, mismatch_count]
                        }
                        row_df = pd.DataFrame(row_analysis)
                        st.dataframe(row_df, use_container_width=True, hide_index=True)
                        
                        # Show matched columns
                        if resolved_join:
                            st.divider()
                            st.write("### Join/Key Columns Used")
                            st.write(f"**Columns:** {', '.join(resolved_join)}")
                            
                    except Exception as e:
                        st.error(f"Error in Detailed Info tab: {str(e)}")


                # Export options
                st.markdown("---")
                st.markdown("### 📥 Export Options")
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    try:
                        if comp_created and comp is not None:
                            report_text = comp.report()
                        else:
                            report_text = f"""DataFrame Summary
-----------------
DataFrame A: {total_rows_a} rows, {len(df_a_prep.columns)} columns
DataFrame B: {total_rows_b} rows, {len(df_b_prep.columns)} columns

Row Summary
-----------
Matched on: {', '.join(resolved_join)}
Rows in common (matched on keys): {merged.shape[0]}
Rows only in A: {unq_a}
Rows only in B: {unq_b}
Rows with mismatched values: {mismatch_count}
Rows with all values matching: {matched_rows}

Column Summary
--------------
Common columns: {len(common_cols)}
Columns compared: {len(compared_cols)}
"""
                        
                        st.download_button(
                            label="📄 Download TXT Report",
                            data=report_text,
                            file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Error exporting TXT report: {str(e)}")
                
                with col_export2:
                    # Prepare report data for PDF
                    try:
                        if comp_created and comp is not None:
                            report_text = comp.report()
                        else:
                            report_text = f"""DataFrame Summary
-----------------
DataFrame A: {total_rows_a} rows, {len(df_a_prep.columns)} columns
DataFrame B: {total_rows_b} rows, {len(df_b_prep.columns)} columns

Row Summary
-----------
Matched on: {', '.join(resolved_join)}
Rows in common (matched on keys): {merged.shape[0]}
Rows only in A: {unq_a}
Rows only in B: {unq_b}
Rows with mismatched values: {mismatch_count}
Rows with all values matching: {matched_rows}

Column Summary
--------------
Common columns: {len(common_cols)}
Columns compared: {len(compared_cols)}
"""
                        
                        # Create structured data for PDF
                        pdf_data = {
                            'total_rows_a': total_rows_a,
                            'total_rows_b': total_rows_b,
                            'cols_a': len(df_a_prep.columns),
                            'cols_b': len(df_b_prep.columns),
                            'resolved_join': resolved_join,
                            'merged_rows': merged.shape[0] if not merged.empty else 0,
                            'unq_a': unq_a,
                            'unq_b': unq_b,
                            'mismatch_count': mismatch_count,
                            'matched_rows': matched_rows,
                            'common_cols': len(common_cols),
                            'compared_cols': len(compared_cols)
                        }
                        
                        # Generate PDF with structured data
                        pdf_bytes = generate_pdf_report(report_text, pdf_data)
                        
                        # Download button
                        st.download_button(
                            label="📑 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            help="Download the comparison report as a PDF file"
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.info("Make sure reportlab is installed: pip install reportlab")

            except Exception as e:
                import traceback
                st.error(f"❌ Error comparing datasets: {str(e)}")
                st.info("💡 Tip: Make sure your datasets have compatible key columns and data types.")