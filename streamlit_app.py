"""
Streamlit App to Test Agent Axios Backend
==========================================
A simple interface to test repository vulnerability analysis.
"""

import streamlit as st
import requests
import socketio
import time
import json
from datetime import datetime
import pandas as pd

# Backend configuration
BACKEND_URL = "http://localhost:5000"
API_BASE = f"{BACKEND_URL}/api"

# Initialize session state
if 'analysis_id' not in st.session_state:
    st.session_state.analysis_id = None
if 'analysis_status' not in st.session_state:
    st.session_state.analysis_status = None
if 'progress_logs' not in st.session_state:
    st.session_state.progress_logs = []
if 'results' not in st.session_state:
    st.session_state.results = None

st.set_page_config(
    page_title="Agent Axios Tester",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 Agent Axios Backend Tester")
st.markdown("---")

# Sidebar - Backend Status
with st.sidebar:
    st.header("Backend Status")
    
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if health.status_code == 200:
            st.success("✅ Backend Online")
            st.json(health.json())
        else:
            st.error("❌ Backend Error")
    except Exception as e:
        st.error("❌ Backend Offline")
        st.caption(f"Error: {str(e)}")
    
    st.markdown("---")
    st.caption(f"Backend URL: `{BACKEND_URL}`")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1️⃣ Create Analysis")
    
    repo_url = st.text_input(
        "Repository URL",
        value="https://github.com/example/repo",
        placeholder="https://github.com/user/repo"
    )
    
    analysis_type = st.selectbox(
        "Analysis Type",
        ["SHORT", "MEDIUM", "HARD"],
        index=1,
        help="SHORT: Quick scan (~2-3 min)\nMEDIUM: Balanced with GPT validation (~5-10 min)\nHARD: Deep comprehensive scan (~15-40 min)"
    )
    
    if st.button("🚀 Start Analysis", type="primary"):
        try:
            with st.spinner("Creating analysis..."):
                response = requests.post(
                    f"{API_BASE}/analysis",
                    json={
                        "repo_url": repo_url,
                        "analysis_type": analysis_type
                    },
                    timeout=10
                )
                
                if response.status_code == 201:
                    data = response.json()
                    st.session_state.analysis_id = data['analysis_id']
                    st.session_state.analysis_status = data['status']
                    st.session_state.progress_logs = []
                    st.session_state.results = None
                    st.success(f"✅ Analysis created! ID: {data['analysis_id']}")
                    st.json(data)
                else:
                    st.error(f"❌ Error: {response.text}")
        except Exception as e:
            st.error(f"❌ Request failed: {str(e)}")

with col2:
    st.header("2️⃣ Start Analysis")
    
    if st.session_state.analysis_id:
        st.info(f"Current Analysis ID: **{st.session_state.analysis_id}**")
        
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("▶️ Start Processing"):
                st.info("Starting analysis via WebSocket...")
                
                progress_placeholder = st.empty()
                log_placeholder = st.empty()
                status_placeholder = st.empty()
                
                try:
                    # Create SocketIO client with proper configuration
                    sio = socketio.Client(
                        logger=False,
                        engineio_logger=False
                    )
                    
                    @sio.on('connected', namespace='/analysis')
                    def on_connected(data):
                        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Connected to WebSocket"
                        st.session_state.progress_logs.append(log_msg)
                    
                    @sio.on('progress_update', namespace='/analysis')
                    def on_progress(data):
                        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {data['progress']}% - {data['stage']}: {data['message']}"
                        st.session_state.progress_logs.append(log_msg)
                    
                    @sio.on('analysis_complete', namespace='/analysis')
                    def on_complete(data):
                        st.session_state.progress_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Analysis Complete!")
                        st.session_state.analysis_status = 'completed'
                    
                    @sio.on('analysis_started', namespace='/analysis')
                    def on_started(data):
                        st.session_state.progress_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Analysis pipeline started")
                    
                    @sio.on('error', namespace='/analysis')
                    def on_error(data):
                        st.session_state.progress_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {data}")
                        st.session_state.analysis_status = 'failed'
                    
                    # Connect to server
                    status_placeholder.info("🔌 Connecting to backend...")
                    sio.connect(BACKEND_URL, namespaces=['/analysis'], wait_timeout=10)
                    time.sleep(0.5)  # Give connection time to establish
                    
                    status_placeholder.success("✅ Connected! Starting analysis...")
                    
                    # Emit start_analysis event
                    sio.emit('start_analysis', {'analysis_id': st.session_state.analysis_id}, namespace='/analysis')
                    
                    # Wait for analysis to complete (with timeout)
                    timeout = 3600  # 1 hour max
                    start_time = time.time()
                    
                    while st.session_state.analysis_status not in ['completed', 'failed']:
                        if time.time() - start_time > timeout:
                            status_placeholder.warning("⏱️ Timeout reached")
                            break
                        
                        sio.sleep(0.5)
                        
                        # Update UI with latest logs
                        if st.session_state.progress_logs:
                            recent_logs = st.session_state.progress_logs[-10:]
                            log_placeholder.text_area("Progress Logs", "\n".join(recent_logs), height=200, key=f"log_{len(st.session_state.progress_logs)}")
                            
                            # Try to extract progress percentage from latest log
                            latest_log = st.session_state.progress_logs[-1]
                            if "%" in latest_log:
                                try:
                                    pct = int(latest_log.split("%")[0].split()[-1])
                                    progress_placeholder.progress(pct / 100, text=f"Progress: {pct}%")
                                except:
                                    pass
                        
                        # Also poll the API for status updates
                        if int(time.time() - start_time) % 5 == 0:  # Every 5 seconds
                            try:
                                response = requests.get(f"{API_BASE}/analysis/{st.session_state.analysis_id}", timeout=2)
                                if response.status_code == 200:
                                    data = response.json()
                                    if data['status'] == 'completed':
                                        st.session_state.analysis_status = 'completed'
                                    elif data['status'] == 'failed':
                                        st.session_state.analysis_status = 'failed'
                            except:
                                pass
                    
                    sio.disconnect()
                    
                    if st.session_state.analysis_status == 'completed':
                        status_placeholder.success("✅ Analysis completed successfully!")
                        st.balloons()
                    elif st.session_state.analysis_status == 'failed':
                        status_placeholder.error("❌ Analysis failed")
                    
                except ConnectionRefusedError as e:
                    st.error(f"❌ WebSocket connection refused: {str(e)}")
                    st.info("💡 The backend might not be running. Try using '🔄 Poll & Start Analysis' instead.")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "namespace" in error_msg.lower() or "connect" in error_msg.lower():
                        st.error(f"❌ WebSocket connection failed: {error_msg}")
                        st.info("💡 Try using '🔄 Poll & Start Analysis' button instead (doesn't require WebSocket).")
                    else:
                        st.error(f"❌ Error: {error_msg}")
                        st.info("💡 Try refreshing the page or checking the backend logs.")
        
        with col2b:
            if st.button("🔍 Check Status"):
                try:
                    response = requests.get(f"{API_BASE}/analysis/{st.session_state.analysis_id}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.analysis_status = data['status']
                        st.json(data)
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")
            
            if st.button("🔄 Poll & Start Analysis"):
                try:
                    # First, trigger the analysis via API (without WebSocket)
                    st.info("Starting analysis without WebSocket (using polling instead)...")
                    
                    # We need to start it via WebSocket event, so let's do a simple trigger
                    progress_placeholder = st.empty()
                    status_text = st.empty()
                    
                    # Try to connect and start via WebSocket
                    try:
                        sio = socketio.Client(logger=False, engineio_logger=False)
                        sio.connect(BACKEND_URL, namespaces=['/analysis'], wait_timeout=5)
                        sio.emit('start_analysis', {'analysis_id': st.session_state.analysis_id}, namespace='/analysis')
                        sio.disconnect()
                        status_text.success("✅ Analysis started!")
                    except:
                        status_text.warning("⚠️ WebSocket failed, but you can still poll for status")
                    
                    # Now poll for status
                    max_polls = 120  # 10 minutes at 5 second intervals
                    for i in range(max_polls):
                        time.sleep(5)
                        
                        response = requests.get(f"{API_BASE}/analysis/{st.session_state.analysis_id}", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.analysis_status = data['status']
                            
                            status_text.text(f"Status: {data['status']} | Files: {data['total_files']} | Chunks: {data['total_chunks']} | Findings: {data['total_findings']}")
                            
                            # Calculate rough progress
                            if data['status'] == 'completed':
                                progress_placeholder.progress(1.0, text="✅ Complete!")
                                st.success("Analysis completed!")
                                st.balloons()
                                break
                            elif data['status'] == 'failed':
                                progress_placeholder.progress(0.0, text="❌ Failed")
                                st.error(f"Analysis failed: {data.get('error_message', 'Unknown error')}")
                                break
                            elif data['status'] == 'running':
                                # Estimate progress based on chunks
                                if data['total_chunks'] > 0:
                                    est_progress = min(0.5 + (data['total_findings'] / max(data['total_chunks'], 1)) * 0.5, 0.95)
                                    progress_placeholder.progress(est_progress, text=f"Running... ({int(est_progress*100)}%)")
                                else:
                                    progress_placeholder.progress(0.3, text="Running...")
                            else:
                                progress_placeholder.progress(0.1, text="Pending...")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.warning("⚠️ No analysis created yet. Create one first!")

st.markdown("---")

# Progress Logs Section
if st.session_state.progress_logs:
    st.header("📊 Progress Logs")
    st.text_area(
        "Recent Logs",
        "\n".join(st.session_state.progress_logs),
        height=300,
        key="main_logs"
    )

st.markdown("---")

# Results Section
st.header("3️⃣ View Results")

if st.session_state.analysis_id:
    col3a, col3b = st.columns(2)
    
    with col3a:
        if st.button("📥 Fetch Results", type="primary"):
            try:
                with st.spinner("Fetching results..."):
                    response = requests.get(
                        f"{API_BASE}/analysis/{st.session_state.analysis_id}/results",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.session_state.results = response.json()
                        st.success("✅ Results fetched!")
                    elif response.status_code == 400:
                        st.warning("⚠️ Analysis not completed yet")
                    else:
                        st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Request failed: {str(e)}")
    
    with col3b:
        if st.button("📋 List All Analyses"):
            try:
                response = requests.get(f"{API_BASE}/analyses", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    st.write(f"**Total Analyses:** {data['total']}")
                    if data['analyses']:
                        df = pd.DataFrame(data['analyses'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No analyses found")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

# Display Results
if st.session_state.results:
    st.markdown("---")
    st.header("🎯 Analysis Results")
    
    results = st.session_state.results
    
    # Summary
    st.subheader("📈 Summary")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    with col_s1:
        st.metric("Total Files", results['summary']['total_files'])
    with col_s2:
        st.metric("Total Chunks", results['summary']['total_chunks'])
    with col_s3:
        st.metric("Total Findings", results['summary']['total_findings'])
    with col_s4:
        st.metric("Confirmed Vulnerabilities", results['summary']['confirmed_vulnerabilities'])
    
    # Severity Breakdown
    if results['summary'].get('severity_breakdown'):
        st.subheader("🚨 Severity Breakdown")
        severity_data = results['summary']['severity_breakdown']
        
        col_sev1, col_sev2, col_sev3, col_sev4 = st.columns(4)
        with col_sev1:
            st.metric("🔴 Critical", severity_data.get('CRITICAL', 0))
        with col_sev2:
            st.metric("🟠 High", severity_data.get('HIGH', 0))
        with col_sev3:
            st.metric("🟡 Medium", severity_data.get('MEDIUM', 0))
        with col_sev4:
            st.metric("🟢 Low", severity_data.get('LOW', 0))
    
    # Findings Table
    st.subheader("🔍 Findings (First 100)")
    if results['findings']:
        df = pd.DataFrame(results['findings'])
        
        # Add filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            status_filter = st.multiselect(
                "Filter by Validation Status",
                options=df['validation_status'].unique().tolist() if 'validation_status' in df.columns else [],
                default=df['validation_status'].unique().tolist() if 'validation_status' in df.columns else []
            )
        
        with col_f2:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=df['severity'].dropna().unique().tolist() if 'severity' in df.columns else [],
                default=df['severity'].dropna().unique().tolist() if 'severity' in df.columns else []
            )
        
        # Apply filters
        if status_filter and 'validation_status' in df.columns:
            df = df[df['validation_status'].isin(status_filter)]
        if severity_filter and 'severity' in df.columns:
            df = df[df['severity'].isin(severity_filter)]
        
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"analysis_{st.session_state.analysis_id}_results.csv",
            mime="text/csv"
        )
    else:
        st.info("No findings to display")
    
    # Raw JSON
    with st.expander("📄 View Raw JSON"):
        st.json(results)

else:
    st.info("💡 Run an analysis and fetch results to see detailed findings")

# Footer
st.markdown("---")
st.caption("Agent Axios Backend Tester | Made with Streamlit 🎈")
