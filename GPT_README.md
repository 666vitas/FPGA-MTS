\# GPT Reading Guide for FPGA-MTS



This repository is my Red Pitaya FPGA laser frequency locking project.



Priority reading order:



1\. `version/`

&#x20;  - v1/v2/v2a development records

&#x20;  - roadmap, SOP, review checklist



2\. `v0.94/`

&#x20;  - real FPGA development directory

&#x20;  - RTL, testbench, Vivado source files



3\. `v-weifang/`

&#x20;  - copied active FPGA development project



4\. `version-weifang/`

&#x20;  - related development records



5\. `docs/`

&#x20;  - earlier project documents



Important status:



The v2a PI/PID code has already been written. Do not ignore it.



v2a is useful because it is the first digital replacement of the D2-125 servo core, but it does not yet replace the full D2-125 workflow. The full workflow still requires scan, offset, scan-lock switching, lock acquisition, relock, and lock quality judgment.

