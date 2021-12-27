from flask import Flask, render_template, request, jsonify

import pymongo
from flask_pymongo import PyMongo
import json
from prometheus_flask_exporter import PrometheusMetrics
from jaeger_client import Config
from flask_opentracing import FlaskTracing


JAEGER_HOST = getenv('JAEGER_HOST', 'localhost')

app = Flask(__name__)

config = Config(config={'sampler': {'type': 'const', 'param': 1},
                                'logging': True,
                                'local_agent':
                                # Also, provide a hostname of Jaeger instance to send traces to.
                                {'reporting_host': "my-traces-query.observability.svc.cluster.local"}},
                        # Service name can be arbitrary string describing this particular web service.
                        service_name="backend")
jaeger_tracer = config.initialize_tracer()
tracing = FlaskTracing(jaeger_tracer)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.3')

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)


@app.route("/")
def homepage():
    return "Hello World"


@app.route("/api")
@tracing.trace()
def my_api():
    answer = "something"
    with jaeger_tracer.start_active_span(
                        'python webserver internal span of log method') as scope:
                    # Perform some computations to be traced.

                    a = 1
                    b = 2
                    c = a + b

                    scope.span.log_kv({'event': 'my computer knows math!', 'result': c})

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
