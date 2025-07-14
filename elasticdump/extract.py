from elasticsearch import Elasticsearch

# 1. Connect to Elasticsearch
es = Elasticsearch("http://192.168.1.13:5601")

# 2. Check if cluster is up
if not es.ping():
    print("❌ Elasticsearch is not reachable")
    exit()

print("✅ Connected to Elasticsearch!")

# 3. List available indices (optional)
indices = es.indices.get_alias("*")
print("\n📦 Available indices:")
for idx in indices:
    print(" -", idx)

# 4. Replace 'your-index-name' below with a real one from above
INDEX_NAME = "your-index-name"

# 5. Fetch logs
try:
    response = es.search(index=INDEX_NAME, size=5, body={
        "query": {
            "match_all": {}
        }
    })

    print(f"\n🔍 Sample logs from index: {INDEX_NAME}\n")
    for hit in response['hits']['hits']:
        print("🧾", hit['_source'])

except Exception as e:
    print(f"\n❌ Error fetching logs from index '{INDEX_NAME}':\n", e)
    


#~~~~~~~~~~~~~suggested mid way by GPT 
from elasticsearch import Elasticsearch

es = Elasticsearch(
    "https://192.168.1.20:9200",
    basic_auth=("elastic", "your_password"),
    verify_certs=False  # Since you’re not using a real SSL cert
)

