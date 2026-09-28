FROM insightforge-api:latest

USER root

# Copy the app source code and alembic files
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
