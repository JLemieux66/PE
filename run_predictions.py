"""Wrapper to run predictions from root directory"""
import sys
sys.path.insert(0, 'scripts/sec_edgar')

from scripts.sec_edgar.predict_all_companies import predict_all_companies

if __name__ == "__main__":
    predict_all_companies(confidence_threshold=0.3)
