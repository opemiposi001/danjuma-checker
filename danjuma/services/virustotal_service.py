import requests
import time
import os

class VirusTotalService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
        self.headers = {
            "x-apikey": self.api_key
        }

    def upload_file(self, file_bytes, filename):
        """Uploads a file to VirusTotal and returns the analysis ID."""
        files = {"file": (filename, file_bytes)}
        response = requests.post(f"{self.base_url}/files", headers=self.headers, files=files)
        
        if response.status_code != 200:
            print(f"Error uploading file: {response.text}")
            return None
        
        return response.json().get('data', {}).get('id')

    def get_analysis_result(self, analysis_id):
        """Polls VirusTotal for the analysis result."""
        if not analysis_id:
            return None

        for attempt in range(5):
            response = requests.get(f"{self.base_url}/analyses/{analysis_id}", headers=self.headers)
            
            if response.status_code != 200:
                print(f"Error getting analysis: {response.text}")
                return None

            data = response.json().get('data', {})
            attributes = data.get('attributes', {})
            status = attributes.get('status')

            if status == 'completed':
                stats = attributes.get('stats', {})
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                total_engines = sum(stats.values()) if stats else 0
                
                # Verdict logic
                if malicious > 0:
                    verdict = "MALICIOUS"
                elif suspicious > 0:
                    verdict = "SUSPICIOUS"
                else:
                    verdict = "CLEAN"

                meta = data.get('meta', {})
                file_info = meta.get('file_info', {})
                sha256 = file_info.get('sha256')
                vt_link = f"https://www.virustotal.com/gui/file/{sha256}" if sha256 else None

                return {
                    "verdict": verdict,
                    "malicious_count": malicious,
                    "suspicious_count": suspicious,
                    "total_engines": total_engines,
                    "virustotal_link": vt_link
                }
            
            print(f"Analysis status: {status}. Waiting 15 seconds (attempt {attempt + 1}/5)...")
            time.sleep(15)

        print("Max attempts reached for VirusTotal analysis.")
        return None
