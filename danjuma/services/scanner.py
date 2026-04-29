from services.gmail_service import GmailService
from services.virustotal_service import VirusTotalService
from models.database import get_db_connection
from config import Config
import os

def run_scan_for_all_registered_emails():
    """Orchestrates the scan flow for all active registered emails."""
    db = get_db_connection()
    cursor = db.cursor()
    
    # Fetch active emails
    cursor.execute("SELECT email FROM registered_emails WHERE is_active = 1")
    active_emails = cursor.fetchall()

    if not active_emails:
        print("No active registered emails to scan.", flush=True)
        db.close()
        return

    vt_service = VirusTotalService(Config.VIRUSTOTAL_API_KEY)

    for row in active_emails:
        email = row['email']
        print(f"Scanning for: {email}", flush=True)
        
        # Create a GmailService instance for THIS specific user
        gmail_service = GmailService(email=email)
        
        if not gmail_service.creds:
            print(f"No credentials found for {email}, skipping.", flush=True)
            continue
        
        # Scan emails from 1 to 9 minutes old (avoid recent and very old emails)
        unread_emails = gmail_service.get_unread_emails_with_attachments(min_age_minutes=1, max_age_minutes=9)
        
        if not unread_emails:
            print(f"No unread emails with attachments for {email}", flush=True)
        
        for email_msg in unread_emails:
            sender = email_msg['sender']
            subject = email_msg['subject']
            
            for attachment in email_msg['attachments']:
                filename = attachment['filename']
                file_data = attachment['data']
                
                print(f"Checking file: {filename} from {sender}", flush=True)
                
                analysis_id = vt_service.upload_file(file_data, filename)
                result = vt_service.get_analysis_result(analysis_id)
                
                if result:
                    verdict = result['verdict']
                    malicious_count = result['malicious_count']
                    suspicious_count = result['suspicious_count']
                    total_engines = result['total_engines']
                    vt_link = result['virustotal_link']
                    
                    # Save to DB
                    cursor.execute("""
                        INSERT INTO scan_history 
                        (registered_email, sender_email, file_name, verdict, malicious_count, suspicious_count, virustotal_link)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (email, sender, filename, verdict, malicious_count, suspicious_count, vt_link))
                    db.commit()
                    
                    # Send result email
                    verdict_emoji = "✅ CLEAN"
                    if verdict == "MALICIOUS":
                        verdict_emoji = "❌ MALICIOUS"
                    elif verdict == "SUSPICIOUS":
                        verdict_emoji = "⚠️ SUSPICIOUS"
                    
                    email_body = f"""
Subject: [Danjuma Checker] Scan Result — {filename}

File: {filename}
Sender: {sender}
Verdict: {verdict_emoji}
Engines that flagged it: {malicious_count} / {total_engines}
Full Report: {vt_link}

Stay safe,
Danjuma Malicious Attachment Checker
"""
                    gmail_service.send_result_email(email, f"[Danjuma Checker] Scan Result — {filename}", email_body)
                    print(f"Result for {filename} sent to {email}", flush=True)
                else:
                    print(f"Failed to get VirusTotal result for {filename}", flush=True)

    db.close()
    print("Scan cycle completed.", flush=True)

if __name__ == "__main__":
    run_scan_for_all_registered_emails()
