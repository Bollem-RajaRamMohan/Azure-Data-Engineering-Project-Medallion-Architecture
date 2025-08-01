# Databricks notebook source
# MAGIC %md
# MAGIC #Creating Fact Table

# COMMAND ----------


df_silver=spark.sql("select * from parquet.`abfss://silver@prjtdelta.dfs.core.windows.net/carsales`")

# COMMAND ----------

df_silver.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### read all dims

# COMMAND ----------

df_dealer=spark.sql("select * from deltaprjt.gold.dim_dealer")
df_branch=spark.sql("select * from deltaprjt.gold.dim_branch")
df_model=spark.sql("select * from deltaprjt.gold.dim_model")
df_date=spark.sql("select * from deltaprjt.gold.dim_date")


# COMMAND ----------

# MAGIC %md
# MAGIC ### Bringing keys to fact table

# COMMAND ----------

df_fact=df_silver.join(df_branch,df_silver.Branch_ID==df_branch.Branch_ID,how='left')\
                .join(df_dealer,df_silver.Dealer_ID==df_dealer.Dealer_ID,how='left')\
                 .join(df_model,df_silver.Model_ID==df_model.Model_ID,how='left')\
                  .join(df_date,df_silver.Date_ID==df_date.Date_ID,how='left')\
                  .select(df_silver.Revenue,df_silver.Units_Sold,df_silver.RevPerUnit,df_branch.dim_branch_key,df_dealer.dim_dealer_key,df_model.dim_model_key,df_date.dim_date_key)

# COMMAND ----------

df_fact.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### writing fact table

# COMMAND ----------

from delta.tables import DeltaTable

# COMMAND ----------

if spark.catalog.tableExists("factsales"):
    delta_tbl=DeltaTable.forName(spark,"deltaprjt.gold.factsales")
    delta_tbl.alias("trg").merge(df_fact.alias("src"),"trg.dim_branch_key=src.dim_branch_key and trg.dim_dealer_key=src.dim_dealer_key and trg.dim_model_key=src.dim_model_key and trg.dim_date_key=src.dim_date_key")\
    .whenMatchedUpdateAll()\
    .whenNotMatchedInsertAll()\
    .execute()

else:
    df_fact.write.format('delta')\
        .mode('Overwrite')\
        .option('path',"abfss://gold@prjtdelta.dfs.core.windows.net/factsales")\
        .saveAsTable("deltaprjt.gold.factsales")

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from deltaprjt.gold.factsales