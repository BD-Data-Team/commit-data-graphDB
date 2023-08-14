from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame
from enum import Enum
import yaml, os

SPARK_MASTER_URL="spark://spark-master:7077"

NEO4J_FORMAT = "org.neo4j.spark.DataSource"
ARANGO_FORMAT = "com.arangodb.spark"
TIGERGRAPH_FORMAT = "jdbc"

fileDir = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(fileDir, os.environ["CONNECTORS_DEFAULT_OPTIONS"])

with open(configPath, "r") as f:
    config = yaml.safe_load(f)


class SparkConnector(Enum):
    NEO4J = "neo4j"
    ARANGO = "arangodb"
    TIGERGRAPH = "tigergraph"

def get_default_options(connector: SparkConnector):
    # return { key : config [connector.value][key] for key in config[connector.value].keys() }
    options = {}

    for key in config[connector.value].keys():
            options[key] = config[connector.value][key]

    return options

# Create the spark session for a given connector
def create_spark_session(app_name: str, connector: SparkConnector):
    build = SparkSession.builder \
        .appName(app_name) \
        .master(SPARK_MASTER_URL) \
        .config("spark.authenticate", "false")
    
    # Add the connector dependencies
    connectorsDepsDir = os.path.join(fileDir, "dependencies", connector.value)

    lambdaMap = lambda x: os.path.join(connectorsDepsDir, x)
    toListMap = lambda func, lst: list(map(func, lst))

    dependenciesFiles = os.listdir(connectorsDepsDir)
    dependencies = toListMap(lambdaMap, dependenciesFiles)
    dependenciesStr = ",".join(dependencies)

    build = build.config("spark.jars", dependenciesStr) \
        .config("spark.driver.extraClassPath", dependenciesStr)
    
    print("Added dependencies: \n", dependenciesFiles)
    return build.getOrCreate()


def spark_write(connector: SparkConnector, df: DataFrame, mode: str, options: dict):
    # Get the connector format
    format = globals()[f"{connector.vlue}_FORMAT"]

    df.write.mode(mode) \
        .format(format) \
        .options(**options) \
        .save()
    
    print(f"Dataframe saved to {connector.name}")

def spark_read(connector: SparkConnector, session: SparkSession, options: dir) -> DataFrame:
    # Get the connector format
    format = globals()[f"{connector.name}_FORMAT"]

    df = session.read \
        .format(format) \
        .options(**options) \
        .load()
    
    print(f"Dataframe loaded from {connector.value}")
    return df