from pyspark.sql import functions as F
from transforms.api import Input, Output, transform


@transform(
    orders_a=Input("/fmlin0429712024-16d385/foundry-poc/orders_system_a"),
    orders_b=Input("/fmlin0429712024-16d385/foundry-poc/orders_system_b"),
    customers=Input("/fmlin0429712024-16d385/foundry-poc/consolidated_customers"),
    output=Output("/fmlin0429712024-16d385/foundry-poc/all_orders"),
)
def compute(orders_a, orders_b, customers, output):
    customers_df = customers.dataframe()

    orders_a_df = (
        orders_a.dataframe()
        .withColumnRenamed("OrderID", "order_id")
        .withColumnRenamed("ItemName", "item_name")
        .withColumnRenamed("Order_Due_Date", "due_date")
        .withColumnRenamed("STATUS", "status")
        .filter(F.trim(F.coalesce(F.col("order_id"), F.lit(""))) != "")
        .withColumn(
            "due_date",
            F.coalesce(
                F.to_timestamp("due_date", "MM/dd/yyyy"),
                F.to_timestamp("due_date", "yyyy-MM-dd"),
                F.to_timestamp("due_date", "dd-MMM-yyyy"),
            ),
        )
        .join(
            customers_df.select(
                F.col("system_a_customer_id").alias("customer_id"),
                "consolidated_customer_id",
                "customer_name",
            ),
            on="customer_id",
            how="left",
        )
        .withColumn("source_system", F.lit("system_a"))
        .select(
            "order_id",
            "consolidated_customer_id",
            "customer_name",
            "item_name",
            "due_date",
            "status",
            "assignee",
            "source_system",
        )
    )

    orders_b_df = (
        orders_b.dataframe()
        .drop("order_placement_date")
        .withColumnRenamed("dueDateTime", "due_date")
        .filter(F.trim(F.coalesce(F.col("order_id"), F.lit(""))) != "")
        .withColumn(
            "due_date",
            F.coalesce(
                F.to_timestamp("due_date"),
                F.to_timestamp("due_date", "yyyy-MM-dd"),
                F.to_timestamp("due_date", "MM/dd/yyyy"),
            ),
        )
        .join(
            customers_df.select(
                F.col("system_b_customer_id").alias("customer_id"),
                "consolidated_customer_id",
                "customer_name",
            ),
            on="customer_id",
            how="left",
        )
        .withColumn("source_system", F.lit("system_b"))
        .select(
            "order_id",
            "consolidated_customer_id",
            "customer_name",
            "item_name",
            "due_date",
            "status",
            "assignee",
            "source_system",
        )
    )

    output.write_dataframe(orders_a_df.unionByName(orders_b_df))
