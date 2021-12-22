# analysis-pipeline
  - Demonstrates multiprocessing data analysis pipelines
    - Simulated data streaming in a process
    - Processing simulated data in a different process.
    - Streaming processed data over ZMQ socket
    - Simple **DASH** based web client that receive processed data over network and display
    - **DASH** app components metadata is accessed between different process through REDIS as a broker  

Installing
==========

`analysis-pipeline` 

Create conda environment with Python 3.6 or later:

    conda create -n {env_name} python=3.6

Activate conda environment:

    conda activate {env_name}
    pip install -e .

Usage:

 - Open terminal and start the pipeline:

        start_pipeline {hostname} {port}
        hostname, port: tcp://{hostname}:{port} address for ZMQ streaming of processed data.

 - Open another terminal and start the **Matplotlib** client that displays processed data:
    
        start_test_client
 
 - Open another terminal and start the **DASH** based client that displays processed data:
    
        start_dash_client
