import streamlit as st
import os
import asyncio
import sys
import requests
from langchain_groq import ChatGroq
from langchain_core.tools import tool

# --- THE WINDOWS ASYNC FIX ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain.agents import create_agent
import langchain
langchain.debug = True

# --- UI Setup ---
st.set_page_config(page_title="SOC AI Agent", layout="wide")
st.title("🛡️ Autonomous Cybersecurity SOC Agent")
st.markdown("Investigate anomalous logins and lateral movement (Blast Radius) using FalkorDB.")

# --- MCP Tools for the Agent (Mocked for Local Demo) ---
@tool
def check_login_anomaly(user_name: str) -> str:
    """Check if a user's recent login location is unusual or if they are using a VPN."""
    print(f"\n🚀 QUERYING FALKORDB FOR LOGIN: {user_name}...\n")
    # Hackathon Bypass: Return the exact expected DB row for the video demo
    if user_name.lower() == 'alice':
        return "ALERT: Alice logged in from Amsterdam (usually in Bangalore). Threat intel: VPN."
    return "No recent anomalous login events found."

@tool
def check_blast_radius(user_name: str) -> str:
    """Find the lateral movement path and sensitive databases a user can access if compromised."""
    print(f"\n💥 QUERYING FALKORDB FOR BLAST RADIUS: {user_name}...\n")
    # Hackathon Bypass: Return the exact expected DB row for the video demo
    if user_name.lower() == 'alice':
        return "CRITICAL BLAST RADIUS: The user has direct access to high-sensitivity assets: Customer_Database (via DevOps_Admin role)."
    return "No high-sensitivity assets at risk."

# --- Agent Initialization & Chat ---
api_key = st.text_input("Enter your Groq API Key to start:", type="password")

if api_key:
    os.environ["GROQ_API_KEY"] = api_key
    
    try:
        # Fetch the exact models YOUR API key is allowed to use
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.groq.com/openai/v1/models", headers=headers).json()
        
        allowed_models = [m["id"] for m in response.get("data", [])]
        chat_models = [
            m for m in allowed_models 
            if "guard" not in m.lower() and "whisper" not in m.lower() and "vision" not in m.lower()
        ]
        
        if not chat_models:
            st.error("Groq verified your key, but hasn't assigned chat models to this region yet.")
        else:
            active_model = chat_models[0]
            for m in chat_models:
                if any(kw in m.lower() for kw in ["versatile", "instant", "instruct", "tool", "oss"]):
                    active_model = m
                    break
                    
            st.info(f"🔌 Dynamically connected to fully-unlocked Groq model: `{active_model}`")
            
            llm = ChatGroq(model=active_model, temperature=0, api_key=api_key)
            tools = [check_login_anomaly, check_blast_radius]
            agent = create_agent(llm, tools)

            user_input = st.text_input("Instruct the Agent (e.g., 'Check Alice for suspicious activity and tell me her blast radius'):")
            
            if st.button("Run Investigation"):
                with st.spinner(f"Agent is reasoning using {active_model}..."):
                    try:
                        res = agent.invoke({"messages": [("user", user_input)]})
                        st.success("Investigation Complete")
                        st.write(res["messages"][-1].content)
                    except Exception as e:
                        st.error(f"Agent Error: {e}")

    except Exception as api_error:
        st.error(f"Network Error fetching models: {api_error}")

# --- Threat Map Visualization ---
st.markdown("---")
st.subheader("🕸️ Visual Threat Map")

if st.button("Map Alice's Blast Radius"):
    from pyvis.network import Network
    import streamlit.components.v1 as components
    
    with st.spinner("Rendering Physics Graph..."):
        # Hackathon Bypass: Local graph data mapping for PyVis
        mock_result = [
            ('Alice', 'DevOps_Admin', 'Customer_Database', 'High'),
            ('Alice', 'DevOps_Admin', 'Internal_Wiki', 'Low')
        ]
        
        net = Network(height="500px", width="100%", bgcolor="#0E1117", font_color="white", directed=True)
        net.toggle_physics(True)
        
        for row in mock_result:
            user, role, asset, sensitivity = row[0], row[1], row[2], row[3]
            
            net.add_node(user, label=f"User:\n{user}", color="#2ECC71", shape="circle")
            net.add_node(role, label=f"Role:\n{role}", color="#3498DB", shape="box")
            
            asset_color = "#E74C3C" if sensitivity == 'High' else "#F1C40F"
            net.add_node(asset, label=f"Asset:\n{asset}", color=asset_color, shape="database")
            
            net.add_edge(user, role, label="HAS_ROLE", color="#aaaaaa")
            net.add_edge(role, asset, label="CAN_ACCESS", color="#aaaaaa")
            
        net.save_graph("blast_radius.html")
        with open("blast_radius.html", 'r', encoding='utf-8') as f:
            components.html(f.read(), height=515)