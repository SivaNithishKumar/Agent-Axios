"""Seed CVE dataset with sample vulnerabilities."""
import os
import sys
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import CVEDataset
from app.services.cohere_service import CohereEmbeddingService
from app.services.faiss_manager import CVEIndexManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample CVE data (common web vulnerabilities)
SAMPLE_CVES = [
    {
        'cve_id': 'CVE-2021-44228',
        'description': 'Apache Log4j2 Remote Code Execution (Log4Shell). JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints. An attacker who can control log messages or log message parameters can execute arbitrary code loaded from LDAP servers when message lookup substitution is enabled.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-502',
        'published_date': '2021-12-10'
    },
    {
        'cve_id': 'CVE-2021-45046',
        'description': 'Apache Log4j2 Denial of Service. It was found that the fix to address CVE-2021-44228 in Apache Log4j 2.15.0 was incomplete in certain non-default configurations. When the logging configuration uses a non-default Pattern Layout with a Context Lookup, attackers with control over Thread Context Map data can craft malicious input data that contains a recursive lookup, resulting in a StackOverflowError.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-400',
        'published_date': '2021-12-14'
    },
    {
        'cve_id': 'CVE-2017-5638',
        'description': 'Apache Struts2 Remote Code Execution. The Jakarta Multipart parser in Apache Struts 2.3.x before 2.3.32 and 2.5.x before 2.5.10.1 has incorrect exception handling and error-message generation during file-upload attempts, which allows remote attackers to execute arbitrary commands via a crafted Content-Type, Content-Disposition, or Content-Length HTTP header.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-20',
        'published_date': '2017-03-10'
    },
    {
        'cve_id': 'CVE-2014-0160',
        'description': 'OpenSSL Heartbleed vulnerability. The TLS heartbeat extension implementation in OpenSSL allows remote attackers to obtain sensitive information from process memory via crafted packets that trigger a buffer over-read, potentially disclosing sensitive information including private keys, usernames, passwords, and other confidential data.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-119',
        'published_date': '2014-04-07'
    },
    {
        'cve_id': 'CVE-2022-22965',
        'description': 'Spring Framework Remote Code Execution (Spring4Shell). A Spring MVC or Spring WebFlux application running on JDK 9+ may be vulnerable to remote code execution (RCE) via data binding. The specific exploit requires the application to run on Tomcat as a WAR deployment. If the application is deployed as a Spring Boot executable jar, it is not vulnerable.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-94',
        'published_date': '2022-04-01'
    },
    {
        'cve_id': 'CVE-2017-5753',
        'description': 'Spectre Variant 1 (bounds check bypass). Systems with microprocessors utilizing speculative execution and branch prediction may allow unauthorized disclosure of information to an attacker with local user access via a side-channel analysis.',
        'severity': 'MEDIUM',
        'cwe_id': 'CWE-200',
        'published_date': '2018-01-03'
    },
    {
        'cve_id': 'CVE-2019-11510',
        'description': 'Pulse Connect Secure Arbitrary File Read. An unauthenticated remote attacker can send a specially crafted URI to perform an arbitrary file reading vulnerability.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-22',
        'published_date': '2019-04-26'
    },
    {
        'cve_id': 'CVE-2020-1472',
        'description': 'Zerologon - Windows Netlogon Elevation of Privilege. An elevation of privilege vulnerability exists when an attacker establishes a vulnerable Netlogon secure channel connection to a domain controller, using the Netlogon Remote Protocol (MS-NRPC).',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-330',
        'published_date': '2020-08-17'
    },
    {
        'cve_id': 'CVE-2021-3156',
        'description': 'Sudo Heap Buffer Overflow (Baron Samedit). A heap-based buffer overflow in sudo allows local users to gain root privileges without authentication.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-787',
        'published_date': '2021-01-26'
    },
    {
        'cve_id': 'CVE-2019-0708',
        'description': 'BlueKeep - Remote Desktop Protocol RCE. A remote code execution vulnerability exists in Remote Desktop Services when an unauthenticated attacker connects to the target system using RDP and sends specially crafted requests.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-416',
        'published_date': '2019-05-16'
    },
    {
        'cve_id': 'CVE-2021-26855',
        'description': 'Microsoft Exchange Server SSRF (ProxyLogon). A server-side request forgery vulnerability in Microsoft Exchange Server allows an attacker to send arbitrary HTTP requests and authenticate as the Exchange server.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-918',
        'published_date': '2021-03-02'
    },
    {
        'cve_id': 'CVE-2018-11776',
        'description': 'Apache Struts2 RCE. When namespace value is not set for a result defined in the same form or in a URLresult, Struts will try to convert the value to an OGNL expression, which can lead to remote code execution.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-20',
        'published_date': '2018-08-22'
    },
    {
        'cve_id': 'CVE-2017-0144',
        'description': 'EternalBlue - Windows SMBv1 RCE. The SMBv1 server in Microsoft Windows allows remote attackers to execute arbitrary code via crafted packets.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-119',
        'published_date': '2017-03-14'
    },
    {
        'cve_id': 'CVE-2019-19781',
        'description': 'Citrix ADC Directory Traversal. An unauthenticated attacker with network access to the vulnerable system can perform directory traversal and execute arbitrary code.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-22',
        'published_date': '2020-01-17'
    },
    {
        'cve_id': 'CVE-2020-5902',
        'description': 'F5 BIG-IP TMUI RCE. Undisclosed requests may bypass authentication and lead to remote code execution.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-22',
        'published_date': '2020-07-01'
    },
    {
        'cve_id': 'CVE-2022-0847',
        'description': 'Dirty Pipe - Linux Kernel Privilege Escalation. A flaw in the Linux kernel allows overwriting data in arbitrary read-only files, leading to privilege escalation.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-787',
        'published_date': '2022-03-07'
    },
    {
        'cve_id': 'CVE-2021-40438',
        'description': 'Apache HTTP Server SSRF. A crafted request uri-path can cause mod_proxy to forward the request to an origin server chosen by the remote user.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-918',
        'published_date': '2021-09-16'
    },
    {
        'cve_id': 'CVE-2020-3452',
        'description': 'Cisco ASA Path Traversal. An attacker could read sensitive files on the targeted system.',
        'severity': 'HIGH',
        'cwe_id': 'CWE-22',
        'published_date': '2020-07-22'
    },
    {
        'cve_id': 'CVE-2021-44832',
        'description': 'Apache Log4j2 RCE via JDBC Appender. When a JDBC Appender is configured, an attacker who can control log messages or log message parameters can execute arbitrary code.',
        'severity': 'MEDIUM',
        'cwe_id': 'CWE-502',
        'published_date': '2021-12-28'
    },
    {
        'cve_id': 'CVE-2022-26134',
        'description': 'Atlassian Confluence OGNL Injection RCE. An OGNL injection vulnerability allows an unauthenticated attacker to execute arbitrary code.',
        'severity': 'CRITICAL',
        'cwe_id': 'CWE-94',
        'published_date': '2022-06-02'
    }
]

def seed_cve_data():
    """Seed CVE data into database and FAISS index."""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting CVE data seeding...")
        
        # Check if data already exists
        existing_count = db.session.query(CVEDataset).count()
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} CVEs. Clearing...")
            db.session.query(CVEDataset).delete()
            db.session.commit()
        
        # Initialize services
        cohere_service = CohereEmbeddingService()
        cve_index = CVEIndexManager()
        
        # Prepare texts for embedding
        texts = [f"{cve['cve_id']}: {cve['description']}" for cve in SAMPLE_CVES]
        
        logger.info(f"Generating embeddings for {len(SAMPLE_CVES)} CVEs...")
        embeddings = cohere_service.generate_embeddings(texts)
        
        # Add CVEs to database
        logger.info("Storing CVEs in database...")
        cve_objects = []
        for cve_data in SAMPLE_CVES:
            cve = CVEDataset(**cve_data)
            db.session.add(cve)
            cve_objects.append(cve)
        
        db.session.flush()
        
        # Add embeddings to FAISS index
        logger.info("Adding embeddings to FAISS index...")
        embedding_array = np.array(embeddings, dtype='float32')
        metadata = [{'cve_id': cve.cve_id} for cve in cve_objects]
        vector_ids = cve_index.add_vectors(embedding_array, metadata)
        
        # Update CVEs with embedding_id
        for cve, vector_id in zip(cve_objects, vector_ids):
            cve.embedding_id = vector_id
        
        db.session.commit()
        
        # Save FAISS index
        cve_index.save_index()
        
        logger.info(f"✅ Successfully seeded {len(SAMPLE_CVES)} CVEs")
        logger.info(f"   - Database records: {db.session.query(CVEDataset).count()}")
        logger.info(f"   - FAISS vectors: {cve_index.index.ntotal}")

if __name__ == '__main__':
    seed_cve_data()
