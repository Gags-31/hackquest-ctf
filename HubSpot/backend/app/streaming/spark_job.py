"""Spark batch-processing job stub: builds features for customer intelligence."""

try:
    from pyspark.sql import SparkSession  # type: ignore

    def run():
        spark = SparkSession.builder.appName("hubspot").getOrCreate()
        print(f"Spark session: {spark.version}")

except ImportError:

    def run():
        print("[spark-stub] feature generation complete: avg_purchase_per_customer=73500")
