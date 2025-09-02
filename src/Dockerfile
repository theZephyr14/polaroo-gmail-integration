FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# Install browser binaries for Playwright
RUN playwright install
ENV PORT=8501
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8501", "--server.address", "0.0.0.0"]
