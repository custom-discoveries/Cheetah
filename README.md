<p align="center">
<img width="400" alt="image" src="https://github.com/user-attachments/assets/176b28d4-e720-48c9-aab9-d341976974eb">
</p>


<h2>
<p align="center">Custom Discoveries Cheetah</p>
</h2>

### Cheetah is a command-line Rapid Application Deployment (RAD) tool designed to simplify TigerGraph Database administrative functions. It eliminates the complexities of managing secrets, tokens, and security authentication, ensuring seamless access. 

### Cheetah program is compatible with both Linux (Ubuntu) and macOS, enabling effortless deployment of TigerGraph Database DDL scripts either locally or in the cloud with minimal effort

### One of Cheetah’s super powers is the ability to “Flip” between Local and Remote Servers, allowing a developer to develop loacally and deploy in their TigerGraph database schema in the cloud.

### Cheetah is built on the principle of 'Separation of Concerns,' utilizing a folder structure to organize different DDL scripts for building and loading a *Graph* instance. One folder is dedicated to schema definition, another to query definitions, and a final folder for defining the data loading process for vertices and edges.

### To get started: Simply clone this repository and run the *initCheetah.sh* from the bin directory to setup your environment path.
### Once your environment path is setup, quit out of the tool, then clone one of the other TigerGraph examples in cusotm-discoveries repository.
  - [BCBSA](https://github.com/custom-discoveries/BCBSA)
  - [Genealogy](https://github.com/custom-discoveries/Genealogy)
  - [Health-Analytics](https://github.com/custom-discoveries/Health-Analytics)
  - [HRA](https://github.com/custom-discoveries/HRA)
  - With the exception of [*Ethereum*](https://github.com/custom-discoveries/Ethereum), which is a pure python programmatic application that will create a simple schema with Vertex and Edges.

### Enter the project dirctory that you cloned and run the command Cheetah, you should be prompted for environment variables.
  - Example: cd ~/mydata/Genealogy/
  - Genealogy> Cheetah
### If you are starting from scratch, Cheetah has an option to allow you to create a project directory and populate it with template TigerGraph DDL scripts , so as to get you up and running in no time.
  - Run Cheetah, then select [-p] to define and install a new Project Folder Structure
