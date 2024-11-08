<p align="center">
<img width="400" alt="image" src="https://github.com/user-attachments/assets/95effac5-14cd-4612-b4dd-01303c806231">
</p>


<h2>
<p align="center">Custom Discoveries Cheetah</p>
</h2>

### Cheetah is a command-line Rapid Application Deployment (RAD) tool designed to simplify TigerGraph *"Classic"* Database administrative functions. It eliminates the complexities of managing secrets, tokens, and security authentication, ensuring seamless access. 

### Cheetah program runs on both Linux (Ubuntu) and macOS (Intel,Mx), enabling effortless deployment of TigerGraph Database DDL scripts either locally or in the cloud with minimal effort.

### One of Cheetah’s super powers is the ability to “Flip” between Local and Remote Servers, allowing a developer to develop loacally and deploy in their TigerGraph database schema in the cloud.

### Cheetah is built on the principle of 'Separation of Concerns,' utilizing a folder structure to organize different DDL scripts for building and loading a *Graph* instance. 

### One folder is dedicated to schema definition, another to query definitions, and a final folder for defining the data loading process for vertices and edges. The *GraphData* folder holds all of your data files that will be used to load your Graph.
<img width="400" alt="image" src="https://github.com/user-attachments/assets/257572ef-bade-45f0-a510-235d3963a244">


## Install and Run
### Install
To install Cheetah, clone this repository at a terminal command prompt: 
- \>git clone https://github.com/custom-discoveries/Cheetah.git [^1]
[^1]: Cloning this repository will download Cheetah for all three supported platforms (Linux, macOS-(Intel,Mx)). Linux is only supported for zip based delivery at this time.

### Initialize Cheetah:
-  cd Cheetah/bin
-  Cheetah/bin\> . ./initCheetah.sh [^2]
-  Cheetah will open with a welcome banner in the terminal, this will confirm that you have properly installed and initialized it. Now close Cheetah.

[^2]: initCheetah will initialize your enviornment only for the session of the terminal window. You will need to add $CHEETAH_PATH to startup script (.bashrc) to make the changes permanent.
### Using Cheetah on one of the Custom Discoveries TigerGraph Schema examples below:
  - [Global_Types](https://github.com/custom-discoveries/Global_Types)
  - [BCBSA](https://github.com/custom-discoveries/BCBSA) (Note: BCBSA has a dependency on Global_Types)
  - [Genealogy](https://github.com/custom-discoveries/Genealogy)
  - [Health-Analytics](https://github.com/custom-discoveries/Health-Analytics)
  - [HRA](https://github.com/custom-discoveries/HRA)
  - [LDBC](https://github.com/custom-discoveries/LDBC)  - Linked Data Benchmark Council
      - Requires loading **User Defined Functions** (UDF's)
  - With the exception of [*Ethereum*](https://github.com/custom-discoveries/Ethereum), which is a pure python programmatic application that will create a simple schema with Vertex and Edges.
### Using Cheetah to Install one of the TigerGraph Example Applications:
-  To install one of the above TigerGraph examples perform the following:
  - Example: cd ~/mydata/Genealogy/
  - Genealogy> Cheetah
      - Select -b option to load both the schema & data
      - Select -q (sub option -b) to Define and Install the queries
### Using Cheetah when starting from scratch:
- Cheetah will create a project directory and populate it with template TigerGraph DDL scripts
- Example:
    - cd ~/mydata/[^3]
    - mydata> Cheetah
       - Cheetah will prompt you for a Project Directory. Enter *SomeProjectName*
       - Cheetah will create you a directory with the name you passed it: *SomeProjectName*
[^3]: The assumption is the 'Cheetah' directory exists under *~/mydata/* directory
