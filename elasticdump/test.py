from elasticsearch import Elasticsearch

# Create the client
es = Elasticsearch(
    "https://192.168.1.20:9200",
    basic_auth=("elastic", "Q1oyklvcIJLR+5qhb0RG"),
    verify_certs=False
)

# Check connection
try:
    info = es.info()
    print(f"✅ Connected to Elasticsearch {info['version']['number']} - Cluster: {info['cluster_name']}")
except Exception as e:
    print("❌ Connection failed:", e)
    exit()

# List available indices
indices = es.indices.get_alias(index="*")  # ✅ Correct: keyword argument
print("\n📦 Available Indices:")
for name in indices:
    print(f" - {name}")

# Try reading top 3 logs from one of the system logs
INDEX_NAME = ".ds-logs-system.syslog-default-2025.07.02-000001"  # Replace if needed

try:
    res = es.search(index=INDEX_NAME, size=3, sort="@timestamp:desc")
    print("\n📄 Top 3 Documents:")
    for hit in res["hits"]["hits"]:
        print(hit["_source"])
except Exception as e:
    print("❌ Failed to fetch documents:", e)
