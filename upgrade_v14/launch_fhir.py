"""Launch the official application locally, binding only loopback."""
import os
from pathlib import Path
from bootstrap_fhir import LOCAL

def main():
    java=(LOCAL/'java-path.txt').read_text().strip();runtime=LOCAL/'runtime'
    command=[java,'-Xms512m','-Xmx2g','-jar',str(runtime/'app/main.war'),
        '--spring.config.additional-location=file:'+str(runtime/'configs/application.yaml'),
        '--spring.datasource.url=jdbc:h2:'+str(runtime/'data/test_db')+';DB_CLOSE_DELAY=-1',
        '--server.address=127.0.0.1','--server.port=18080',
        '--hapi.fhir.server_address=http://127.0.0.1:18080/fhir']
    os.chdir(runtime/'app');os.execv(java,command)

if __name__=='__main__':main()
