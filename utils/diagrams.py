import os
import graphviz
import tempfile
from pathlib import Path

def ensure_diagram_dir():
    """Ensure the diagrams directory exists"""
    diagram_dir = Path("static/diagrams")
    diagram_dir.mkdir(parents=True, exist_ok=True)
    return diagram_dir

def get_temp_path(filename: str) -> str:
    """Get a temporary file path"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)

def get_system_architecture_diagram() -> bytes:
    """
    Generate a PNG diagram showing the SRE Copilot system architecture
    Returns the diagram as bytes
    """
    try:
        dot = graphviz.Digraph(comment='System Architecture')
        dot.attr(rankdir='TB')
        
        # Input Layer
        with dot.subgraph(name='cluster_0') as c:
            c.attr(label='Input Layer')
            c.attr(style='filled', color='lightpink')
            c.node('I1', 'Incident Data')
            c.node('I2', 'Metrics Data')
            c.node('I3', 'Log Data')
            c.node('I4', 'Images')
        
        # Agent Layer
        with dot.subgraph(name='cluster_1') as c:
            c.attr(label='Agent Layer')
            c.attr(style='filled', color='lightblue')
            c.node('A1', 'Incident Analyzer')
            c.node('A2', 'Metric Analyzer')
            c.node('A3', 'Log Analyzer')
            c.node('A4', 'Image Analyzer')
            c.node('B1', 'Root Cause Analysis')
            c.node('B2', 'Impact Analysis')
        
        # AWS Bedrock Layer
        with dot.subgraph(name='cluster_2') as c:
            c.attr(label='AWS Bedrock Layer')
            c.attr(style='filled', color='lightgreen')
            c.node('C1', 'Claude Model')
        
        # Output Layer
        with dot.subgraph(name='cluster_3') as c:
            c.attr(label='Output Layer')
            c.attr(style='filled', color='lightcoral')
            c.node('D1', 'Final Analysis')
            c.node('D2', 'Action Items')
        
        # Add edges
        dot.edge('I1', 'A1')
        dot.edge('I2', 'A2')
        dot.edge('I3', 'A3')
        dot.edge('I4', 'A4')
        
        dot.edge('A1', 'B1')
        dot.edge('A2', 'B1')
        dot.edge('A3', 'B1')
        dot.edge('A4', 'B1')
        
        dot.edge('A1', 'B2')
        dot.edge('A2', 'B2')
        dot.edge('A3', 'B2')
        dot.edge('A4', 'B2')
        
        dot.edge('B1', 'C1')
        dot.edge('B2', 'C1')
        dot.edge('C1', 'B1')
        dot.edge('C1', 'B2')
        
        dot.edge('B1', 'D1')
        dot.edge('B2', 'D1')
        dot.edge('D1', 'D2')
        
        # Use temporary file
        temp_path = get_temp_path('system_architecture')
        dot.render(temp_path, format='png', cleanup=True)
        with open(f"{temp_path}.png", 'rb') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Failed to generate system architecture diagram: {str(e)}")

def get_agent_interaction_diagram() -> bytes:
    """
    Generate a PNG diagram showing agent interactions
    Returns the diagram as bytes
    """
    try:
        dot = graphviz.Digraph(comment='Agent Interactions')
        dot.attr(rankdir='LR')
        
        # Add nodes
        dot.node('User', 'User')
        dot.node('IA', 'Incident Analyzer')
        dot.node('MA', 'Metric Analyzer')
        dot.node('LA', 'Log Analyzer')
        dot.node('Bedrock', 'Bedrock')
        dot.node('Analysis', 'Analysis')
        
        # Add edges with sequence
        dot.edge('User', 'IA', 'Submit Incident')
        dot.edge('IA', 'MA', 'Request Metrics Analysis')
        dot.edge('MA', 'Bedrock', 'Analyze Metrics')
        dot.edge('Bedrock', 'MA', 'Metrics Insights')
        dot.edge('MA', 'IA', 'Metrics Analysis')
        dot.edge('IA', 'LA', 'Request Log Analysis')
        dot.edge('LA', 'Bedrock', 'Analyze Logs')
        dot.edge('Bedrock', 'LA', 'Log Insights')
        dot.edge('LA', 'IA', 'Log Analysis')
        dot.edge('IA', 'Bedrock', 'Generate RCA')
        dot.edge('Bedrock', 'IA', 'RCA Results')
        dot.edge('IA', 'Analysis', 'Combined Analysis')
        dot.edge('Analysis', 'User', 'Final RCA Report')
        
        # Use temporary file
        temp_path = get_temp_path('agent_interaction')
        dot.render(temp_path, format='png', cleanup=True)
        with open(f"{temp_path}.png", 'rb') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Failed to generate agent interaction diagram: {str(e)}")

def get_data_flow_diagram() -> bytes:
    """
    Generate a PNG diagram showing data flow
    Returns the diagram as bytes
    """
    try:
        dot = graphviz.Digraph(comment='Data Flow')
        dot.attr(rankdir='LR')
        
        # Data Sources
        with dot.subgraph(name='cluster_0') as c:
            c.attr(label='Data Sources')
            c.attr(style='filled', color='lightpink')
            c.node('D1', 'Text Data')
            c.node('D2', 'Metrics')
            c.node('D3', 'Logs')
            c.node('D4', 'Images')
        
        # Processors
        with dot.subgraph(name='cluster_1') as c:
            c.attr(label='Processors')
            c.attr(style='filled', color='lightblue')
            c.node('P1', 'Text Processor')
            c.node('P2', 'Metrics Processor')
            c.node('P3', 'Log Processor')
            c.node('P4', 'Image Processor')
        
        # Add edges
        dot.edge('D1', 'P1', 'Incident Details')
        dot.edge('D2', 'P2', 'Time Series')
        dot.edge('D3', 'P3', 'Text')
        dot.edge('D4', 'P4', 'Visual')
        
        # Use temporary file
        temp_path = get_temp_path('data_flow')
        dot.render(temp_path, format='png', cleanup=True)
        with open(f"{temp_path}.png", 'rb') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Failed to generate data flow diagram: {str(e)}") 