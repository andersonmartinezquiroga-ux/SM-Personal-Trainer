FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
# Refresh system certificate trust store for the October 2026 CA compromise advisory.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY executor.py test_form.py server.py api_v2.py applicant.py form_adapter.py submit_ypai.py run_authorized_ypai_20261020.py ./
# Compile-only/offline regression: exact public route, no account creation or external POST.
COPY test_applicant.py test_form_adapter.py ./
RUN python -m unittest test_applicant.SecurityTests.test_wellonis_founding_coach_public_only test_form_adapter.FormAdapterTests.test_wellonis_requires_owner_terms_and_never_submits
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "api_v2.py"]
