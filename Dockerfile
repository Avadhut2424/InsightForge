FROM insightforge-api:latest

USER root

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app source code and alembic files
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY pytest.ini .
COPY run_suite.py .
COPY Makefile .

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
