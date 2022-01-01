from flask import Flask, render_template, request, jsonify
import flask
import pymongo
import requests
from flask_pymongo import PyMongo
import json
from prometheus_flask_exporter import PrometheusMetrics
from jaeger_client import Config
from flask_opentracing import FlaskTracing
from os import getenv

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
        resource=Resource.create({SERVICE_NAME: "backend"})
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


app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()



metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.3')
app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)

tracer = trace.get_tracer(__name__)

@app.route("/")
def homepage():
    return "Hello World"


@app.route("/api")
# @tracing.trace()
def my_api():
    with tracer.start_as_current_span("example-request"):
        answer = "something"

    return jsonify(repsonse=answer)

@app.route("/ap2")
def my_api2():
    answer = "something"
    return jsonify(repsonse=answer)

@app.route("/star", methods=["POST"])
def add_star():
    star = mongo.db.stars
    name = request.json["name"]
    distance = request.json["distance"]
    star_id = star.insert({"name": name, "distance": distance})
    new_star = star.find_one({"_id": star_id})
    output = {"name": new_star["name"], "distance": new_star["distance"]}
    return jsonify({"result": output})


if __name__ == "__main__":
    app.run()
