"""Setup script to create the Pinecone index for PE portfolio companies."""

import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

INDEX_NAME = "pe-portfolio-companies"

def setup_index():
    """Create or verify Pinecone index exists."""

    # Initialize Pinecone
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_names = [index.name for index in existing_indexes]

    if INDEX_NAME in index_names:
        print(f"✅ Index '{INDEX_NAME}' already exists!")

        # Get index stats
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"   Dimension: {stats.get('dimension', 'unknown')}")

        return True
    else:
        print(f"📝 Index '{INDEX_NAME}' does not exist. Creating it now...")

        try:
            # Create index with appropriate settings
            pc.create_index(
                name=INDEX_NAME,
                dimension=1536,  # text-embedding-3-small dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

            print(f"✅ Successfully created index '{INDEX_NAME}'!")
            print(f"   Dimension: 1536")
            print(f"   Metric: cosine")
            print(f"   Cloud: AWS (us-east-1)")

            return True

        except Exception as e:
            print(f"❌ Error creating index: {e}")
            print(f"\nPlease create the index manually in Pinecone console:")
            print(f"   Name: {INDEX_NAME}")
            print(f"   Dimensions: 1536")
            print(f"   Metric: cosine")
            return False

if __name__ == "__main__":
    print("="*60)
    print("PINECONE INDEX SETUP FOR PE PORTFOLIO COMPANIES")
    print("="*60)
    print()

    success = setup_index()

    print()
    if success:
        print("="*60)
        print("✅ SETUP COMPLETE - Ready to run ingestion!")
        print("="*60)
        print()
        print("Next step: Run the ingestion script")
        print("  python ingestion_pe_portfolio.py")
        print("  or double-click run_pe_ingestion.bat")
    else:
        print("="*60)
        print("⚠️  SETUP INCOMPLETE - Please create index manually")
        print("="*60)
