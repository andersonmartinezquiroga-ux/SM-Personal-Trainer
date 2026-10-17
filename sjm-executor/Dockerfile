FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY executor.py test_form.py server.py api_v2.py applicant.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "api_v2.py"]
