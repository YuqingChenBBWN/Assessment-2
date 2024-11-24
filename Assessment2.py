import streamlit as st
import openai
from datetime import datetime
import json
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from PIL import Image
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# 设置页面配置
st.set_page_config(
    page_title="智能租房合同审查助手",
    page_icon="📋",
    layout="wide"
)

# 初始化会话状态
if 'contract_text' not in st.session_state:
    st.session_state.contract_text = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = {}
if 'risk_score' not in st.session_state:
    st.session_state.risk_score = {}

def validate_api_key(api_key: str) -> bool:
    """验证API密钥是否有效"""
    if not api_key.startswith('sk-'):
        return False
    return True

def calculate_risk_score(analysis_results: Dict) -> float:
    """计算风险评分"""
    risk_factors = {
        'missing_terms': 0.3,
        'unclear_terms': 0.2,
        'unfair_terms': 0.3,
        'legal_issues': 0.2
    }
    
    total_score = 0
    for factor, weight in risk_factors.items():
        if factor in analysis_results:
            total_score += len(analysis_results[factor]) * weight
            
    return min(100, max(0, 100 - total_score * 10))

def create_risk_gauge(risk_score: float) -> go.Figure:
    """创建风险仪表盘"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "合同风险评分"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "red"},
                {'range': [33, 66], 'color': "yellow"},
                {'range': [66, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    return fig

def analyze_contract_with_ai(contract_text: str, api_key: str) -> Dict:
    """使用AI分析合同"""
    openai.api_key = api_key
    
    # 系统提示
    system_prompt = """你是一位专业的法律分析AI助手。请分析提供的租房合同，并返回以下JSON格式的分析结果：
    {
        "basic_terms": {
            "rental_period": "",
            "monthly_rent": "",
            "deposit": "",
            "payment_method": ""
        },
        "legal_issues": [],
        "risk_factors": [],
        "suggestions": [],
        "missing_terms": [],
        "unclear_terms": [],
        "unfair_terms": []
    }"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": contract_text}
            ],
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"分析过程中发生错误：{str(e)}")
        return {}

def generate_visualization(analysis_results: Dict):
    """生成可视化分析图表"""
    # 创建问题类型统计
    issue_types = {
        '法律问题': len(analysis_results.get('legal_issues', [])),
        '风险因素': len(analysis_results.get('risk_factors', [])),
        '缺失条款': len(analysis_results.get('missing_terms', [])),
        '模糊条款': len(analysis_results.get('unclear_terms', [])),
        '不公平条款': len(analysis_results.get('unfair_terms', []))
    }
    
    # 创建条形图
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("husl", len(issue_types))
    bars = ax.bar(issue_types.keys(), issue_types.values(), color=colors)
    
    # 设置图表样式
    ax.set_title('合同问题分析')
    ax.set_ylabel('问题数量')
    plt.xticks(rotation=45)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def main():
    st.title("🏠 智能租房合同审查助手")
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 配置")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    # 主界面
    st.markdown("""
    ### 📝 使用说明
    1. 在右侧填入您的OpenAI API密钥
    2. 将租房合同文本粘贴到下方文本框
    3. 点击"开始分析"按钮
    4. 查看分析结果和建议
    """)
    
    # 文本输入区域
    contract_text = st.text_area("请输入租房合同内容", height=300)
    
    if st.button("开始分析", type="primary"):
        if not contract_text:
            st.error("请输入合同内容！")
            return
            
        if not validate_api_key(api_key):
            st.error("请输入有效的OpenAI API密钥！")
            return
            
        with st.spinner("正在分析合同内容..."):
            # 分析合同
            analysis_results = analyze_contract_with_ai(contract_text, api_key)
            
            if not analysis_results:
                st.error("分析失败，请重试！")
                return
            
            # 计算风险评分
            risk_score = calculate_risk_score(analysis_results)
            
            # 创建三列布局
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("### 📊 风险评估")
                fig_gauge = create_risk_gauge(risk_score)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                st.markdown("### 📈 问题分析")
                fig_issues = generate_visualization(analysis_results)
                st.pyplot(fig_issues)
            
            with col3:
                st.markdown("### 📋 基本条款")
                basic_terms = analysis_results.get('basic_terms', {})
                for term, value in basic_terms.items():
                    st.write(f"**{term}:** {value}")
            
            # 详细分析结果
            st.markdown("### 📑 详细分析")
            
            tabs = st.tabs(["法律问题", "风险因素", "改进建议", "完整报告"])
            
            with tabs[0]:
                st.markdown("#### ⚖️ 法律问题")
                for issue in analysis_results.get('legal_issues', []):
                    st.warning(issue)
            
            with tabs[1]:
                st.markdown("#### ⚠️ 风险因素")
                for risk in analysis_results.get('risk_factors', []):
                    st.info(risk)
            
            with tabs[2]:
                st.markdown("#### 💡 改进建议")
                for suggestion in analysis_results.get('suggestions', []):
                    st.success(suggestion)
            
            with tabs[3]:
                st.markdown("#### 📄 完整报告")
                report = f"""
                # 租房合同审查报告
                
                ## 风险评分: {risk_score}/100
                
                ## 基本条款
                {json.dumps(basic_terms, ensure_ascii=False, indent=2)}
                
                ## 法律问题
                {json.dumps(analysis_results.get('legal_issues', []), ensure_ascii=False, indent=2)}
                
                ## 风险因素
                {json.dumps(analysis_results.get('risk_factors', []), ensure_ascii=False, indent=2)}
                
                ## 改进建议
                {json.dumps(analysis_results.get('suggestions', []), ensure_ascii=False, indent=2)}
                
                报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """
                
                st.download_button(
                    label="下载完整报告",
                    data=report,
                    file_name=f"租房合同审查报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()