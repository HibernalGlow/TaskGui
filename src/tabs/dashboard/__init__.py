import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts
from datetime import datetime, timedelta
from src.utils.selection_utils import get_global_state, get_selected_tasks
from src.components.tag_filters import get_all_tags

def render_dashboard():
    """渲染仪表盘页面"""
    st.markdown("## 📊 任务仪表盘")
    
    # 获取全局状态和任务数据
    global_state = get_global_state()
    tasks_data = global_state.get('tasks', {})
    task_files = global_state.get('task_files', {})
    
    # 如果没有任务数据，显示提示信息
    if not tasks_data:
        st.warning("没有找到任务数据，请先加载任务文件")
        return
    
    # 顶部统计指标
    render_top_metrics(tasks_data)
    
    # 布局为两栏
    col1, col2 = st.columns(2)
    
    # 在第一栏展示任务概览和执行状态
    with col1:
        render_task_overview(tasks_data)
        render_execution_status(tasks_data)
        render_priority_distribution(tasks_data)
    
    # 在第二栏展示运行历史和标签分布
    with col2:
        render_execution_history(tasks_data)
        render_tag_distribution(tasks_data)
        render_execution_time(tasks_data)

def render_top_metrics(tasks_data):
    """渲染顶部关键指标"""
    # 创建四列布局用于顶部指标
    col1, col2, col3, col4 = st.columns(4)
    
    # 计算关键指标
    total_tasks = len(tasks_data)
    selected_tasks = len(get_selected_tasks())
    
    # 计算今日和本周执行的任务数
    today = datetime.now().strftime("%Y-%m-%d")
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    
    today_run_count = 0
    week_run_count = 0
    pending_count = 0
    
    for task_name, task_info in tasks_data.items():
        runtime = task_info.get('runtime', {})
        last_run = runtime.get('last_run', '')
        status = task_info.get('status', '')
        
        # 检查是否在今天运行过
        if last_run and today in last_run:
            today_run_count += 1
            
        # 检查是否在本周运行过
        if last_run and last_run >= week_start:
            week_run_count += 1
            
        # 检查是否待处理
        if status == 'pending':
            pending_count += 1
    
    # 填充指标
    with col1:
        st.metric(label="🔢 总任务数", value=str(total_tasks))
    
    with col2:
        st.metric(label="✅ 选中任务", value=str(selected_tasks))
    
    with col3:
        st.metric(label="📅 今日执行", value=str(today_run_count))
    
    with col4:
        st.metric(label="⏳ 待处理任务", value=str(pending_count))
        
def render_task_overview(tasks_data):
    """渲染任务概览统计卡片"""
    st.markdown("### 任务概览")
    
    # 获取任务总数
    total_tasks = len(tasks_data)
    
    # 计算今日执行的任务数
    today = datetime.now().strftime("%Y-%m-%d")
    today_run_count = 0
    success_count = 0
    
    for task_name, task_info in tasks_data.items():
        # 获取任务运行时信息
        runtime = task_info.get('runtime', {})
        last_run = runtime.get('last_run', '')
        
        # 检查是否在今天运行过
        if last_run and today in last_run:
            today_run_count += 1
        
        # 检查最后状态是否为成功
        if runtime.get('last_status', '') == 'success':
            success_count += 1
    
    # 计算成功率
    success_rate = "0%" if total_tasks == 0 else f"{(success_count / total_tasks) * 100:.1f}%"
    
    # 创建三列布局
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    # 创建三个指标卡片
    with metric_col1:
        st.metric(label="总任务数", value=str(total_tasks))
    
    with metric_col2:
        st.metric(label="今日执行", value=str(today_run_count))
    
    with metric_col3:
        st.metric(label="成功率", value=success_rate)

def render_execution_status(tasks_data):
    """渲染任务执行状态的饼图"""
    st.markdown("### 执行状态")
    
    # 统计不同状态的任务数量
    status_counts = {"成功": 0, "失败": 0, "未执行": 0}
    
    for task_name, task_info in tasks_data.items():
        runtime = task_info.get('runtime', {})
        last_status = runtime.get('last_status', '')
        
        if last_status == 'success':
            status_counts["成功"] += 1
        elif last_status == 'failed':
            status_counts["失败"] += 1
        else:
            status_counts["未执行"] += 1
    
    # 饼图配置
    pie_options = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "执行状态",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": "18", "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": [
                    {"value": status_counts["成功"], "name": "成功", "itemStyle": {"color": "#91cc75"}},
                    {"value": status_counts["失败"], "name": "失败", "itemStyle": {"color": "#ee6666"}},
                    {"value": status_counts["未执行"], "name": "未执行", "itemStyle": {"color": "#5470c6"}},
                ],
            }
        ],
    }
    
    # 显示饼图
    st_echarts(options=pie_options, height="300px")

def render_execution_history(tasks_data):
    """渲染任务执行历史的折线图"""
    st.markdown("### 执行历史")
    
    # 生成过去7天的日期
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    date_labels = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]
    
    # 初始化每天的成功和失败计数
    success_counts = [0] * 7
    failure_counts = [0] * 7
    
    # 遍历所有任务的运行记录
    for task_name, task_info in tasks_data.items():
        runtime = task_info.get('runtime', {})
        run_history = runtime.get('run_history', [])
        
        # 处理运行历史记录
        for record in run_history:
            run_date = record.get('date', '')
            run_status = record.get('status', '')
            
            # 检查是否在过去7天内
            if run_date in dates:
                day_index = dates.index(run_date)
                if run_status == 'success':
                    success_counts[day_index] += 1
                elif run_status == 'failed':
                    failure_counts[day_index] += 1
    
    # 折线图配置
    line_options = {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["成功", "失败"]},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": date_labels,
        },
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": "成功",
                "type": "line",
                "stack": "Total",
                "data": success_counts,
                "smooth": True,
                "lineStyle": {"width": 3},
                "showSymbol": True,
                "itemStyle": {"color": "#5470c6"},
                "areaStyle": {"opacity": 0.2},
            },
            {
                "name": "失败",
                "type": "line",
                "stack": "Total",
                "data": failure_counts,
                "smooth": True,
                "lineStyle": {"width": 3},
                "showSymbol": True,
                "itemStyle": {"color": "#ee6666"},
                "areaStyle": {"opacity": 0.2},
            },
        ],
    }
    
    # 显示折线图
    st_echarts(options=line_options, height="300px")

def render_tag_distribution(tasks_data):
    """渲染标签分布的条形图"""
    st.markdown("### 标签分布")
    
    # 统计标签
    tag_counts = {}
    
    # 遍历任务数据，收集标签
    for task_name, task_info in tasks_data.items():
        tags = task_info.get('tags', [])
        
        for tag in tags:
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1
    
    # 排序标签并取前10个
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    tag_names = [tag for tag, count in sorted_tags]
    tag_values = [count for tag, count in sorted_tags]
    
    # 条形图配置
    bar_options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": tag_names},
        "series": [
            {
                "name": "任务数",
                "type": "bar",
                "data": tag_values,
                "itemStyle": {"color": "#91cc75"},
            }
        ],
    }
    
    # 显示条形图
    st_echarts(options=bar_options, height="300px")

def render_priority_distribution(tasks_data):
    """渲染任务优先级分布的饼图"""
    st.markdown("### 优先级分布")
    
    # 初始化优先级计数
    priority_counts = {"高": 0, "中": 0, "低": 0, "未设置": 0}
    
    # 遍历所有任务，统计不同优先级的任务数量
    for task_name, task_info in tasks_data.items():
        priority = task_info.get('priority', 'medium')
        
        if priority == 'high':
            priority_counts["高"] += 1
        elif priority == 'medium':
            priority_counts["中"] += 1
        elif priority == 'low':
            priority_counts["低"] += 1
        else:
            priority_counts["未设置"] += 1
    
    # 饼图配置
    pie_options = {
        "tooltip": {"trigger": "item"},
        "legend": {"orient": "vertical", "left": "left"},
        "series": [
            {
                "name": "优先级分布",
                "type": "pie",
                "radius": "60%",
                "data": [
                    {"value": priority_counts["高"], "name": "高", "itemStyle": {"color": "#ee6666"}},
                    {"value": priority_counts["中"], "name": "中", "itemStyle": {"color": "#5470c6"}},
                    {"value": priority_counts["低"], "name": "低", "itemStyle": {"color": "#91cc75"}},
                    {"value": priority_counts["未设置"], "name": "未设置", "itemStyle": {"color": "#909399"}},
                ],
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    }
                },
            }
        ],
    }
    
    # 显示饼图
    st_echarts(options=pie_options, height="300px")

def render_execution_time(tasks_data):
    """渲染任务执行时间统计图表"""
    st.markdown("### 执行时间统计")
    
    # 提取有执行时间记录的任务
    task_times = []
    
    for task_name, task_info in tasks_data.items():
        runtime = task_info.get('runtime', {})
        duration = runtime.get('duration', 0)
        
        # 只处理有执行时间记录的任务
        if duration > 0:
            task_times.append({"name": task_name, "duration": duration})
    
    # 按执行时间排序，获取前10个耗时最长的任务
    sorted_tasks = sorted(task_times, key=lambda x: x["duration"], reverse=True)[:10]
    
    if not sorted_tasks:
        st.info("没有足够的执行时间数据")
        return
    
    # 提取数据用于图表
    task_names = [task["name"] for task in sorted_tasks]
    durations = [task["duration"] for task in sorted_tasks]
    
    # 条形图配置
    bar_options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": task_names,
            "axisLabel": {"interval": 0, "rotate": 30},
        },
        "yAxis": {"type": "value", "name": "执行时间 (秒)"},
        "series": [
            {
                "name": "执行时间",
                "type": "bar",
                "data": durations,
                "itemStyle": {"color": "#5470c6"},
            }
        ],
    }
    
    # 显示条形图
    st_echarts(options=bar_options, height="300px")
