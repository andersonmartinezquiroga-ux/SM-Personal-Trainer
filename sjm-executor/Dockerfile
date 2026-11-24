FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
# Refresh system certificate trust store for the October 2026 CA compromise advisory.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY executor.py test_form.py server.py api_v2.py applicant.py form_adapter.py workflow_engine.py submit_ypai.py run_authorized_ypai_20261020.py ./
# Compile-only/offline regression: exact public route, no account creation or external POST.
COPY test_applicant.py test_form_adapter.py test_workflow_engine.py ./
RUN python -m unittest test_applicant.SecurityTests.test_skulearn_exact_public_route_only test_form_adapter.FormAdapterTests.test_skulearn_coaching_agreement_blocks_submission test_applicant.SecurityTests.test_wellonis_founding_coach_public_only test_applicant.SecurityTests.test_jobbers_exact_public_path_without_registration test_applicant.SecurityTests.test_mobidea_instruimos_exact_public_readonly_routes test_applicant.SecurityTests.test_blocked_access_is_not_a_job_listing test_applicant.SecurityTests.test_workana_history_query_does_not_break_canonical_public_inspection test_form_adapter.FormAdapterTests.test_wellonis_requires_owner_terms_and_never_submits test_form_adapter.FormAdapterTests.test_jobbers_public_legal_gate test_form_adapter.FormAdapterTests.test_mobidea_instruimos_semantic_block_not_marked_ready test_applicant.SecurityTests.test_magneto_four_registered_exact_public_pages_only test_form_adapter.FormAdapterTests.test_magneto_registered_public_form_needs_review_never_submits test_workflow_engine
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "api_v2.py"]
