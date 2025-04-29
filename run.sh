#!/bin/bash

# 设置环境变量
export STREAMLIT_ENV=production

# 运行Streamlit应用
streamlit run main.py --server.enableCORS false --server.enableXsrfProtection false 