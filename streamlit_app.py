import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from dotenv import load_dotenv
import os
from utils.test_data import generate_test_incident, generate_test_snapshot
from utils.diagrams import get_system_architecture_diagram, get_agent_interaction_diagram, get_data_flow_diagram
from models.incident import Incident, IncidentAnalysis
import asyncio
import httpx
from main import analyze_incident

# Load environment variables
load_dotenv()

# Verify AWS configuration
if not all(key in st.secrets for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']):
    st.error("""
    ⚠️ AWS credentials not found in Streamlit secrets.
    
    Please configure the following in your Streamlit Cloud settings:
    1. Go to your app dashboard on share.streamlit.io
    2. Click on ⚙️ Settings
    3. Go to Secrets section
    4. Add your secrets in TOML format:
    ```toml
    AWS_ACCESS_KEY_ID = "your_access_key"
    AWS_SECRET_ACCESS_KEY = "your_secret_key"
    AWS_REGION = "us-east-1"  # or your preferred region
    ```
    """)
    st.stop()

# Set AWS credentials from Streamlit secrets
os.environ['AWS_ACCESS_KEY_ID'] = st.secrets['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = st.secrets['AWS_SECRET_ACCESS_KEY']
os.environ['AWS_REGION'] = st.secrets['AWS_REGION']

# Create a new event loop for async operations
async def run_analysis(incident: Incident):
    try:
        return await analyze_incident(incident)
    except Exception as e:
        if "NoRegionError" in str(e):
            st.error("""
            ⚠️ AWS Region not properly configured.
            Please check your AWS_REGION in Streamlit secrets.
            """)
        elif "AccessDenied" in str(e):
            st.error("""
            ⚠️ AWS Access Denied.
            Please check your AWS credentials in Streamlit secrets.
            """)
        else:
            st.error(f"Analysis failed: {str(e)}")
        return None

# Set page config
st.set_page_config(
    page_title="SRE Copilot - Incident RCA",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .confidence-bar {
        height: 20px;
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        background-color: #4CAF50;
        transition: width 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

def display_system_architecture():
    """Display system architecture diagrams"""
    st.header("🏗️ System Architecture")
    
    try:
        # System Architecture Diagram
        st.subheader("System Overview")
        system_diagram = get_system_architecture_diagram()
        st.image(system_diagram)
        
        # Agent Interaction Diagram
        st.subheader("Agent Interactions")
        agent_diagram = get_agent_interaction_diagram()
        st.image(agent_diagram)
        
        # Data Flow Diagram
        st.subheader("Data Flow")
        data_diagram = get_data_flow_diagram()
        st.image(data_diagram)
    except Exception as e:
        st.error("""
        Failed to generate diagrams. Please make sure Graphviz is installed:
        
        1. The error might be temporary - try refreshing the page
        2. If the error persists, please report it to the development team
        
        Error details: """ + str(e))

def display_metrics(incident: Incident):
    """Display metrics visualization"""
    st.subheader("📊 Metrics Analysis")
    
    try:
        # Convert metrics to DataFrame
        metrics_data = []
        if not incident.metrics:
            st.warning("No metrics data available")
            return
            
        for metric in incident.metrics:
            metrics_data.append({
                "timestamp": metric.timestamp,
                "value": metric.value,
                "name": metric.name,
                "service": metric.tags.get("service", "unknown")
            })
        
        df = pd.DataFrame(metrics_data)
        if df.empty:
            st.warning("No metrics data to display")
            return
            
        # Create tabs for different visualizations
        tab1, tab2 = st.tabs(["Time Series", "Distribution"])
        
        with tab1:
            # Time series plot
            try:
                fig = px.line(df, x="timestamp", y="value", 
                         color="name", line_group="service",
                         title="Metrics Over Time")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to create time series plot: {str(e)}")
        
        with tab2:
            # Distribution plot
            try:
                fig = px.box(df, x="name", y="value", 
                        color="service",
                        title="Metrics Distribution")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to create distribution plot: {str(e)}")
    except Exception as e:
        st.error(f"Error displaying metrics: {str(e)}")

def display_logs(incident: Incident):
    """Display logs analysis"""
    st.subheader("📝 Log Analysis")
    
    try:
        # Convert logs to DataFrame
        logs_data = []
        if not incident.logs:
            st.warning("No logs data available")
            return
            
        for log in incident.logs:
            logs_data.append({
                "timestamp": log.timestamp,
                "level": log.level,
                "message": log.message,
                "source": log.source
            })
        
        df = pd.DataFrame(logs_data)
        if df.empty:
            st.warning("No logs data to display")
            return
        
        # Log level distribution
        try:
            fig = px.pie(df, names="level", title="Log Level Distribution")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create log level distribution chart: {str(e)}")
        
        # Log timeline
        try:
            fig = px.scatter(df, x="timestamp", y="level", 
                        color="source", size=[1] * len(df),
                        title="Log Timeline")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create log timeline chart: {str(e)}")
        
        # Display log table
        try:
            st.dataframe(df)
        except Exception as e:
            st.error(f"Failed to display logs table: {str(e)}")
    except Exception as e:
        st.error(f"Error displaying logs: {str(e)}")

def display_analysis(analysis: IncidentAnalysis):
    """Display RCA analysis results"""
    st.subheader("🔍 Root Cause Analysis")
    
    try:
        if not analysis:
            st.warning("No analysis results available")
            return
            
        # Root Cause
        st.markdown("### Root Cause")
        if analysis.root_cause:
            st.markdown(f"**{analysis.root_cause.description}**")
            st.markdown(f"Confidence: {analysis.root_cause.confidence:.0%}")
            st.markdown("**Evidence:**")
            for evidence in analysis.root_cause.evidence:
                st.markdown(f"- {evidence}")
        else:
            st.warning("No root cause analysis available")
        
        # Impact Analysis
        st.markdown("### Impact Analysis")
        if analysis.impact_analysis:
            st.markdown(f"**{analysis.impact_analysis.description}**")
            st.markdown(f"Confidence: {analysis.impact_analysis.confidence:.0%}")
            st.markdown("**Evidence:**")
            for evidence in analysis.impact_analysis.evidence:
                st.markdown(f"- {evidence}")
        else:
            st.warning("No impact analysis available")
        
        # Metric Insights
        st.markdown("### Metric Insights")
        if analysis.metric_insights:
            for insight in analysis.metric_insights:
                with st.expander(insight.description):
                    st.markdown(f"Confidence: {insight.confidence:.0%}")
                    st.markdown("**Evidence:**")
                    for evidence in insight.evidence:
                        st.markdown(f"- {evidence}")
        else:
            st.warning("No metric insights available")
        
        # Log Insights
        st.markdown("### Log Insights")
        if analysis.log_insights:
            for insight in analysis.log_insights:
                with st.expander(insight.description):
                    st.markdown(f"Confidence: {insight.confidence:.0%}")
                    st.markdown("**Evidence:**")
                    for evidence in insight.evidence:
                        st.markdown(f"- {evidence}")
        else:
            st.warning("No log insights available")
        
        # Recommendations
        st.markdown("### Recommendations")
        if analysis.recommendations:
            for i, rec in enumerate(analysis.recommendations, 1):
                st.markdown(f"{i}. {rec}")
        else:
            st.warning("No recommendations available")
    except Exception as e:
        st.error(f"Error displaying analysis results: {str(e)}")

def main():
    st.title("🔍 SRE Copilot - Incident RCA")
    
    # Sidebar
    st.sidebar.title("Options")
    use_test_data = st.sidebar.checkbox("Use Test Data", value=True)
    show_architecture = st.sidebar.checkbox("Show System Architecture", value=True)
    
    if show_architecture:
        display_system_architecture()
    
    # Initialize incident and analysis as None
    incident = None
    analysis = None
    
    if use_test_data:
        incident = generate_test_incident()
        
        # Display incident details
        st.header("📋 Incident Details")
        st.json(incident.dict())
        
        # Display metrics and logs
        display_metrics(incident)
        display_logs(incident)
        
        # Analyze incident
        if st.sidebar.button("Analyze Incident"):
            with st.spinner("Analyzing incident..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    analysis = loop.run_until_complete(run_analysis(incident))
                    loop.close()
                except Exception as e:
                    st.error(f"Failed to analyze incident: {str(e)}")
                    return
        
        # Display analysis if available
        if analysis:
            display_analysis(analysis)
    else:
        st.info("Please upload incident data or enable test data")

if __name__ == "__main__":
    main() 