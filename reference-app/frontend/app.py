from flask import Flask, render_template, request
import requests
from flask_pymongo import PyMongo
import json
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "frontend"})
    )
)

jaeger_exporter = JaegerExporter(
    agent_host_name="hotrod-agent.observability.svc.cluster.local",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)


app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()



metrics = PrometheusMetrics(app)
metrics.info('frontend_app', 'frontend_app', version='1.1.2')



@app.route("/")
def homepage():
    return render_template("main.html")


if __name__ == "__main__":
    app.run()
